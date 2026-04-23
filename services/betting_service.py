from config.database import db
from decimal import Decimal
from strategies.strategy_factory import StrategyFactory 
import random


class BettingService:

    def place_bet(
        self,
        username,
        session_id,
        base_bet,
        win_probability,
        strategy_code="FLAT",
        odds_type="FIXED",
        odds_value=2.0,
        strategy_id=1
    ):
        if base_bet <= 0:
            raise ValueError("Base bet must be greater than 0")

        if not (0 <= win_probability <= 1):
            raise ValueError("Invalid probability")

        conn = db.get_connection()
        cursor = conn.cursor(dictionary=True)

        try:
            conn.start_transaction()

            cursor.execute(
                "SELECT * FROM gamblers WHERE username = %s",
                (username,)
            )
            gambler = cursor.fetchone()

            if not gambler:
                raise ValueError("Gambler not found")

            stake_before = Decimal(gambler["current_stake"])
            odds_value = Decimal(odds_value)

            cursor.execute("""
                SELECT * FROM betting_preferences 
                WHERE gambler_id = %s
            """, (gambler["gambler_id"],))
            prefs = cursor.fetchone()

            cursor.execute("""
                SELECT * FROM sessions WHERE session_id = %s
            """, (session_id,))
            session = cursor.fetchone()

            if not session:
                raise ValueError("Session not found")
            
            if session["status"] != "ACTIVE":
                raise ValueError("Session is not active")

            strategy = StrategyFactory.get_strategy(strategy_code)

            cursor.execute("""
                SELECT bet_id, bet_amount 
                FROM bets 
                WHERE session_id = %s 
                ORDER BY bet_id DESC 
                LIMIT 1
            """, (session_id,))
            last_bet_row = cursor.fetchone()

            last_bet = Decimal(base_bet)
            last_outcome = None

            if last_bet_row:
                last_bet = Decimal(last_bet_row["bet_amount"])

                cursor.execute("""
                    SELECT outcome 
                    FROM game_records 
                    WHERE bet_id = %s
                """, (last_bet_row["bet_id"],))
                outcome_row = cursor.fetchone()

                if outcome_row:
                    last_outcome = outcome_row["outcome"]

            context = {
                "base_bet": Decimal(base_bet),
                "last_outcome": last_outcome,
                "last_bet": last_bet
            }

            bet_amount = Decimal(strategy.get_next_bet(context))

            max_bet_cap = Decimal("10000")

            if bet_amount > max_bet_cap:
                bet_amount = max_bet_cap

            if prefs and prefs["session_loss_limit"]:
                loss_limit = Decimal(prefs["session_loss_limit"])
                loss_so_far = Decimal(session["starting_stake"]) - stake_before

                if loss_so_far >= loss_limit:
                        self._end_session(cursor, session_id, "LOSS_LIMIT", stake_before)
                        conn.commit()
                        raise ValueError("Session ended: loss limit reached")
                
            if prefs and prefs["session_win_target"]:
                win_target = Decimal(prefs["session_win_target"])
                profit = stake_before - Decimal(session["starting_stake"])

                if profit >= win_target:
                    self._end_session(cursor, session_id, "WIN_TARGET", stake_before)
                    conn.commit()
                    raise ValueError("Session ended: win target reached")

            if bet_amount > stake_before:
                bet_amount = stake_before

            if bet_amount <= 0:
                raise ValueError("Invalid bet amount after strategy")

            if prefs:
                if bet_amount < prefs["min_bet"]:
                    raise ValueError("Below min bet")
                if bet_amount > prefs["max_bet"]:
                    raise ValueError("Above max bet")

            stake_after = stake_before - bet_amount
            potential_win = bet_amount * odds_value

            cursor.execute(
                "UPDATE gamblers SET current_stake = %s WHERE gambler_id = %s",
                (stake_after, gambler["gambler_id"])
            )

            cursor.execute("""
                INSERT INTO bets
                (session_id, gambler_id, strategy_id, bet_amount,
                 win_probability, odds_type, odds_value,
                 potential_win, stake_before, stake_after)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                session_id,
                gambler["gambler_id"],
                strategy_id,
                bet_amount,
                win_probability,
                odds_type,
                odds_value,
                potential_win,
                stake_before,
                stake_after
            ))

            bet_id = cursor.lastrowid

            cursor.execute("""
                INSERT INTO stake_transactions
                (session_id, gambler_id, bet_id, transaction_type,
                 amount, balance_before, balance_after, transaction_ref)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                session_id,
                gambler["gambler_id"],
                bet_id,
                "BET_PLACED",
                bet_amount,
                stake_before,
                stake_after,
                "BET_PLACEMENT"
            ))

            conn.commit()

            return {
                "bet_id": bet_id,
                "bet_amount": float(bet_amount),
                "stake_before": float(stake_before),
                "stake_after": float(stake_after),
                "potential_win": float(potential_win),
                "strategy": strategy_code
            }

        except Exception as e:
            conn.rollback()
            raise e

        finally:
            cursor.close()
            conn.close()    

    def resolve_bet(self, bet_id):
        conn = db.get_connection()
        cursor = conn.cursor(dictionary=True)

        try:
            conn.start_transaction()

            cursor.execute(
                "SELECT * FROM bets WHERE bet_id = %s",
                (bet_id,)
            )
            bet = cursor.fetchone()

            if not bet:
                raise ValueError("Bet not found")

            if bet["is_settled"]:
                raise ValueError("Already settled")

            rand_val = Decimal(str(random.random()))
            win_prob = Decimal(str(bet["win_probability"]))

            outcome = "WIN" if rand_val <= win_prob else "LOSS"

            stake_before = Decimal(bet["stake_after"])

            if outcome == "WIN":
                payout = Decimal(bet["potential_win"])
                net_change = payout
                stake_after = stake_before + payout
            else:
                payout = Decimal(0)
                net_change = -Decimal(bet["bet_amount"])
                stake_after = stake_before

            cursor.execute(
                "UPDATE gamblers SET current_stake = %s WHERE gambler_id = %s",
                (stake_after, bet["gambler_id"])
            )

            cursor.execute("""
                INSERT INTO game_records
                (session_id, bet_id, outcome, payout_amount,
                 loss_amount, net_change, stake_before, stake_after, resolved_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW())
            """, (
                bet["session_id"],
                bet_id,
                outcome,
                payout,
                bet["bet_amount"] if outcome == "LOSS" else 0,
                net_change,
                stake_before,
                stake_after
            ))

            game_id = cursor.lastrowid

            self._insert_snapshot(cursor, bet["session_id"], game_id, outcome, net_change, bet["bet_amount"])

            cursor.execute("""
                INSERT INTO stake_transactions
                (session_id, gambler_id, bet_id, transaction_type,
                 amount, balance_before, balance_after, transaction_ref)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                bet["session_id"],
                bet["gambler_id"],
                bet_id,
                "BET_WIN" if outcome == "WIN" else "BET_LOSS",
                payout if outcome == "WIN" else bet["bet_amount"],
                stake_before,
                stake_after,
                "BET_RESULT"
            ))

            cursor.execute(
                "UPDATE bets SET is_settled = TRUE WHERE bet_id = %s",
                (bet_id,)
            )

            conn.commit()

            return {
                "bet_id": bet_id,
                "outcome": outcome,
                "stake_after": float(stake_after)
            }

        except Exception as e:
            conn.rollback()
            raise e

        finally:
            cursor.close()
            conn.close()

    def _get_last_snapshot(self, cursor, session_id):
        cursor.execute("""
            SELECT * FROM running_totals_snapshots
            WHERE session_id = %s
            ORDER BY snapshot_id DESC
            LIMIT 1
        """, (session_id,))
        return cursor.fetchone()

    def _insert_snapshot(self, cursor, session_id, game_id, outcome, net_change, bet_amount):
        last = self._get_last_snapshot(cursor, session_id)

        if not last:
            total_games = 1
            total_wins = 1 if outcome == "WIN" else 0
            total_losses = 1 if outcome == "LOSS" else 0
            net_profit = net_change

            current_win = 1 if outcome == "WIN" else 0
            current_loss = 1 if outcome == "LOSS" else 0

            longest_win = current_win
            longest_loss = current_loss

            total_bet_amount = Decimal(bet_amount)

        else:
            total_games = last["total_games"] + 1
            total_wins = last["total_wins"] + (1 if outcome == "WIN" else 0)
            total_losses = last["total_losses"] + (1 if outcome == "LOSS" else 0)
            net_profit = last["net_profit"] + net_change

            total_bet_amount = Decimal(last.get("total_bet_amount", 0)) + Decimal(bet_amount)

            if outcome == "WIN":
                current_win = last.get("current_win_streak", 0) + 1
                current_loss = 0
            else:
                current_loss = last.get("current_loss_streak", 0) + 1
                current_win = 0

            longest_win = max(last["longest_win_streak"], current_win)
            longest_loss = max(last["longest_loss_streak"], current_loss)

        win_rate = total_wins / total_games if total_games else 0
        roi = net_profit / total_bet_amount if total_bet_amount else 0

        cursor.execute("""
            INSERT INTO running_totals_snapshots
            (session_id, game_id, total_games, total_wins, total_losses,
             net_profit, win_rate, roi,
             longest_win_streak, longest_loss_streak)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            session_id, game_id, total_games, total_wins,
            total_losses, net_profit, win_rate, roi,
            longest_win, longest_loss
        ))
    
    def _end_session(self, cursor, session_id, reason, ending_stake):
        cursor.execute("""
            UPDATE sessions
            SET status = %s,
                end_reason = %s,
                ending_stake = %s,
                ended_at = NOW()
            WHERE session_id = %s
        """, ("COMPLETED", reason, ending_stake, session_id))


betting_service = BettingService()