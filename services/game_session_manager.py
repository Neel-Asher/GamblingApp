from config.database import db
from decimal import Decimal


class GameSessionManager:

    def start_session(self, username):
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

            gambler_id = gambler["gambler_id"]

            cursor.execute("""
                SELECT * FROM sessions 
                WHERE gambler_id = %s AND status = 'ACTIVE'
                LIMIT 1
            """, (gambler_id,))
            active_session = cursor.fetchone()

            if active_session:
                return active_session["session_id"]

            starting_stake = Decimal(gambler["current_stake"])

            cursor.execute("""
                INSERT INTO sessions (
                    gambler_id,
                    status,
                    starting_stake,
                    peak_stake,
                    lowest_stake,
                    max_games,
                    games_played,
                    total_pause_seconds,
                    started_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW())
            """, (
                gambler_id,
                "ACTIVE",
                starting_stake,
                starting_stake,
                starting_stake,
                100,
                0,
                0
            ))

            session_id = cursor.lastrowid

            conn.commit()

            return session_id

        except Exception as e:
            conn.rollback()
            raise e

        finally:
            cursor.close()
            conn.close()

    def get_active_session(self, username):
        result = db.execute("""
            SELECT s.session_id
            FROM sessions s
            JOIN gamblers g ON s.gambler_id = g.gambler_id
            WHERE g.username = %s AND s.status = 'ACTIVE'
            LIMIT 1
        """, (username,), fetch=True)

        if not result:
            return None

        return result[0]["session_id"]

    def end_session(self, session_id, reason="MANUAL"):
        conn = db.get_connection()
        cursor = conn.cursor(dictionary=True)

        try:
            conn.start_transaction()

            cursor.execute("""
                SELECT current_stake FROM gamblers
                WHERE gambler_id = (
                    SELECT gambler_id FROM sessions WHERE session_id = %s
                )
            """, (session_id,))
            gambler = cursor.fetchone()

            ending_stake = gambler["current_stake"] if gambler else 0

            cursor.execute("""
                UPDATE sessions
                SET status = 'COMPLETED',
                    end_reason = %s,
                    ending_stake = %s,
                    ended_at = NOW()
                WHERE session_id = %s
            """, (reason, ending_stake, session_id))

            conn.commit()

        except Exception as e:
            conn.rollback()
            raise e

        finally:
            cursor.close()
            conn.close()

    def update_after_game(self, session_id, stake_after):
        conn = db.get_connection()
        cursor = conn.cursor(dictionary=True)

        try:
            conn.start_transaction()

            cursor.execute("""
                SELECT * FROM sessions WHERE session_id = %s
            """, (session_id,))
            session = cursor.fetchone()

            if not session:
                raise ValueError("Session not found")

            games_played = session["games_played"] + 1

            peak_stake = max(Decimal(session["peak_stake"]), Decimal(stake_after))
            lowest_stake = min(Decimal(session["lowest_stake"]), Decimal(stake_after))

            cursor.execute("""
                UPDATE sessions
                SET games_played = %s,
                    peak_stake = %s,
                    lowest_stake = %s
                WHERE session_id = %s
            """, (
                games_played,
                peak_stake,
                lowest_stake,
                session_id
            ))

            conn.commit()

        except Exception as e:
            conn.rollback()
            raise e

        finally:
            cursor.close()
            conn.close()
    
    def check_and_end_session(self, session_id, current_stake):
        conn = db.get_connection()
        cursor = conn.cursor(dictionary=True)

        try:
            conn.start_transaction()

            cursor.execute("""
                SELECT * FROM sessions WHERE session_id = %s
            """, (session_id,))
            session = cursor.fetchone()

            if not session:
                raise ValueError("Session not found")

            cursor.execute("""
                SELECT * FROM gamblers WHERE gambler_id = %s
            """, (session["gambler_id"],))
            gambler = cursor.fetchone()

            cursor.execute("""
                SELECT * FROM betting_preferences WHERE gambler_id = %s
            """, (gambler["gambler_id"],))
            prefs = cursor.fetchone()

            reason = None

            if session["games_played"] >= session["max_games"]:
                reason = "MAX_GAMES"

            if prefs and prefs["session_loss_limit"]:
                loss = Decimal(session["starting_stake"]) - Decimal(current_stake)
                if loss > Decimal(prefs["session_loss_limit"]):
                    reason = "LOSS_LIMIT"

            if prefs and prefs["session_win_target"]:
                profit = Decimal(current_stake) - Decimal(session["starting_stake"])
                if profit > Decimal(prefs["session_win_target"]):
                    reason = "WIN_TARGET"

            if reason:
                cursor.execute("""
                    UPDATE sessions
                    SET status = 'COMPLETED',
                        end_reason = %s,
                        ending_stake = %s,
                        ended_at = NOW()
                    WHERE session_id = %s
                """, (reason, current_stake, session_id))

            conn.commit()

            return reason

        except Exception as e:
            conn.rollback()
            raise e

        finally:
            cursor.close()
            conn.close()
    
    def pause_session(self, session_id, reason="USER"):
        conn = db.get_connection()
        cursor = conn.cursor(dictionary=True)

        try:
            conn.start_transaction()

            cursor.execute("""
                INSERT INTO pause_records (
                    session_id,
                    pause_reason,
                    paused_at
                )
                VALUES (%s, %s, NOW())
            """, (session_id, reason))

            cursor.execute("""
                UPDATE sessions
                SET status = 'PAUSED'
                WHERE session_id = %s
            """, (session_id,))

            conn.commit()

        except Exception as e:
            conn.rollback()
            raise e

        finally:
            cursor.close()
            conn.close()
    
    def resume_session(self, session_id):
        conn = db.get_connection()
        cursor = conn.cursor(dictionary=True)

        try:
            conn.start_transaction()

            cursor.execute("""
                SELECT * FROM pause_records
                WHERE session_id = %s AND resumed_at IS NULL
                ORDER BY pause_id DESC
                LIMIT 1
            """, (session_id,))
            pause = cursor.fetchone()

            if not pause:
                raise ValueError("No active pause found")

            cursor.execute("""
                UPDATE pause_records
                SET resumed_at = NOW(),
                    pause_seconds = TIMESTAMPDIFF(SECOND, paused_at, NOW())
                WHERE pause_id = %s
            """, (pause["pause_id"],))

            cursor.execute("""
                UPDATE sessions
                SET status = 'ACTIVE',
                    total_pause_seconds = total_pause_seconds + %s
                WHERE session_id = %s
            """, (pause["pause_seconds"], session_id))

            conn.commit()

        except Exception as e:
            conn.rollback()
            raise e

        finally:
            cursor.close()
            conn.close()

    def get_session_details(self, session_id):
        result = db.execute("""
            SELECT *
            FROM sessions
            WHERE session_id = %s
        """, (session_id,), fetch=True)

        if not result:
            raise ValueError("Session not found")

        return result[0]
    
    def get_session_summary(self, session_id):
        result = db.execute("""
            SELECT * FROM sessions WHERE session_id = %s
        """, (session_id,), fetch=True)

        if not result:
            raise ValueError("Session not found")

        return result[0]


session_manager = GameSessionManager()