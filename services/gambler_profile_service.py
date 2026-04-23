from config.database import db
from decimal import Decimal


class GamblerProfileService:

    def create_gambler(self, username, full_name, email, initial_stake):
        # Basic validation
        if initial_stake <= 0:
            raise ValueError("Initial stake must be greater than 0")

        query = """
        INSERT INTO gamblers 
        (username, full_name, email, initial_stake, current_stake)
        VALUES (%s, %s, %s, %s, %s)
        """

        db.execute(query, (
            username,
            full_name,
            email,
            Decimal(initial_stake),
            Decimal(initial_stake)
        ))

        return self.get_gambler_by_username(username)

    def get_gambler_by_username(self, username):
        query = """
        SELECT * FROM gamblers WHERE username = %s
        """

        result = db.execute(query, (username,), fetch=True)

        if not result:
            return None

        return result[0]
    
    def update_gambler(self, username, full_name=None, email=None):
        existing = self.get_gambler_by_username(username)

        if not existing:
            raise ValueError("Gambler not found")

        query = """
        UPDATE gamblers
        SET full_name = COALESCE(%s, full_name),
            email = COALESCE(%s, email)
        WHERE username = %s
        """

        db.execute(query, (full_name, email, username))

        return self.get_gambler_by_username(username)
    
    def reset_stake(self, username, new_amount):
        gambler = self.get_gambler_by_username(username)

        if not gambler:
            raise ValueError("Gambler not found")

        if new_amount < 0:
            raise ValueError("Stake cannot be negative")

        balance_before = gambler["current_stake"]

        # Update gambler balance
        update_query = """
        UPDATE gamblers
        SET current_stake = %s
        WHERE gambler_id = %s
        """

        db.execute(update_query, (new_amount, gambler["gambler_id"]))

        # Insert transaction record
        txn_query = """
        INSERT INTO stake_transactions
        (gambler_id, transaction_type, amount, balance_before, balance_after, transaction_ref)
        VALUES (%s, %s, %s, %s, %s, %s)
        """

        db.execute(txn_query, (
            gambler["gambler_id"],
            "RESET",
            new_amount,
            balance_before,
            new_amount,
            "MANUAL_RESET"
        ))

        return self.get_gambler_by_username(username)
    
    def set_betting_preferences(
        self,
        username,
        min_bet,
        max_bet,
        preferred_game_type=None,
        auto_play_enabled=False,
        auto_play_max_games=None,
        session_loss_limit=None,
        session_win_target=None
    ):
        gambler = self.get_gambler_by_username(username)

        if not gambler:
            raise ValueError("Gambler not found")

        if min_bet <= 0:
            raise ValueError("min_bet must be > 0")

        if max_bet < min_bet:
            raise ValueError("max_bet must be >= min_bet")

        query = """
        INSERT INTO betting_preferences
        (gambler_id, min_bet, max_bet, preferred_game_type,
        auto_play_enabled, auto_play_max_games,
        session_loss_limit, session_win_target)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            min_bet = VALUES(min_bet),
            max_bet = VALUES(max_bet),
            preferred_game_type = VALUES(preferred_game_type),
            auto_play_enabled = VALUES(auto_play_enabled),
            auto_play_max_games = VALUES(auto_play_max_games),
            session_loss_limit = VALUES(session_loss_limit),
            session_win_target = VALUES(session_win_target)
        """

        db.execute(query, (
            gambler["gambler_id"],
            min_bet,
            max_bet,
            preferred_game_type,
            auto_play_enabled,
            auto_play_max_games,
            session_loss_limit,
            session_win_target
        ))

        return self.get_betting_preferences(username)
    
    def get_betting_preferences(self, username):
        gambler = self.get_gambler_by_username(username)

        if not gambler:
            raise ValueError("Gambler not found")

        query = """
        SELECT * FROM betting_preferences WHERE gambler_id = %s
        """

        result = db.execute(query, (gambler["gambler_id"],), fetch=True)

        return result[0] if result else None

gambler_service = GamblerProfileService()