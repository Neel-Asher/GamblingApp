from config.database import db
from decimal import Decimal
from strategies.strategy_factory import StrategyFactory 
from validators.input_validator import InputValidator
from services.game_session_manager import session_manager
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

        conn = db.get_connection()
        cursor = conn.cursor(dictionary=True)

        try:

            cursor.execute(
                "SELECT * FROM gamblers WHERE username = %s",
                (username,)
            )
            gambler = cursor.fetchone()

            if not gambler:
                raise ValueError("Gambler not found")

            cursor.execute(
                "SELECT * FROM sessions WHERE session_id = %s",
                (session_id,)
            )
            session = cursor.fetchone()

            if not session:
                raise ValueError("Session not found")

            if session["status"] != "ACTIVE":
                raise ValueError("Session is not active")

            stake_before = Decimal(
                session["ending_stake"]
                if session["ending_stake"] is not None
                else session["starting_stake"]
            )

            base_bet = InputValidator.validate_initial_stake(base_bet)
            win_probability = InputValidator.validate_probability(win_probability)

            InputValidator.validate_bet_amount(base_bet, stake_before)

            strategy = StrategyFactory.get_strategy(strategy_code)

            context = {
                "base_bet": Decimal(base_bet),
                "last_bet": Decimal(base_bet),
                "last_outcome": None
            }

            bet_amount = Decimal(strategy.get_next_bet(context))
            bet_amount = InputValidator.validate_bet_amount(bet_amount, stake_before)

            stake_after = stake_before - bet_amount
            potential_win = bet_amount * Decimal(odds_value)

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

            conn.commit()

            return {
                "bet_id": bet_id,
                "bet_amount": float(bet_amount),
                "stake_before": float(stake_before),
                "stake_after": float(stake_after)
            }

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

            cursor.execute("""
                UPDATE sessions
                SET 
                    games_played = games_played + 1,
                    peak_stake = GREATEST(peak_stake, %s),
                    lowest_stake = LEAST(lowest_stake, %s),
                    ending_stake = %s
                WHERE session_id = %s
            """, (
                stake_after,
                stake_after,
                stake_after,
                bet["session_id"]
            ))

            cursor.execute("""
                UPDATE bets SET is_settled = TRUE WHERE bet_id = %s
            """, (bet_id,))

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
    
    def get_last_game_result(self, session_id):
        conn = db.get_connection()
        cursor = conn.cursor(dictionary=True)

        try:
            cursor.execute("""
                SELECT 
                    b.bet_id,
                    b.bet_amount,
                    g.outcome,
                    g.stake_after
                FROM bets b
                JOIN game_records g ON b.bet_id = g.bet_id
                WHERE b.session_id = %s
                ORDER BY b.bet_id DESC
                LIMIT 1
            """, (session_id,))

            result = cursor.fetchone()

            return result

        finally:
            cursor.close()
            conn.close()


betting_service = BettingService()