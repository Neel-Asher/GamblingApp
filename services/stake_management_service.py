from config.database import db


class StakeManagementService:

    def get_current_stake(self, username):
        query = """
        SELECT current_stake FROM gamblers WHERE username = %s
        """

        result = db.execute(query, (username,), fetch=True)

        if not result:
            raise ValueError("Gambler not found")

        return result[0]["current_stake"]

    def get_transaction_history(self, username):
        query = """
        SELECT st.*
        FROM stake_transactions st
        JOIN gamblers g ON st.gambler_id = g.gambler_id
        WHERE g.username = %s
        ORDER BY st.created_at DESC
        """

        return db.execute(query, (username,), fetch=True)
    
    def deposit(self, username, amount, session_id=None):
        if amount <= 0:
            raise ValueError("Deposit amount must be positive")

        gambler = db.execute(
            "SELECT * FROM gamblers WHERE username = %s",
            (username,),
            fetch=True
        )

        if not gambler:
            raise ValueError("Gambler not found")

        gambler = gambler[0]

        balance_before = gambler["current_stake"]
        balance_after = balance_before + amount

        # Update balance
        db.execute(
            "UPDATE gamblers SET current_stake = %s WHERE gambler_id = %s",
            (balance_after, gambler["gambler_id"])
        )

        # Log transaction
        db.execute("""
            INSERT INTO stake_transactions
            (gambler_id, transaction_type, amount, balance_before, balance_after, transaction_ref)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            gambler["gambler_id"],
            "DEPOSIT",
            amount,
            balance_before,
            balance_after,
            "USER_DEPOSIT"
        ))

        if session_id:
            self.update_session_stake_stats(session_id, balance_after)

        return balance_after
    
    def withdraw(self, username, amount, session_id=None):
        if amount <= 0:
            raise ValueError("Withdraw amount must be positive")

        gambler = db.execute(
            "SELECT * FROM gamblers WHERE username = %s",
            (username,),
            fetch=True
        )

        if not gambler:
            raise ValueError("Gambler not found")

        gambler = gambler[0]

        balance_before = gambler["current_stake"]

        if amount > balance_before:
            raise ValueError("Insufficient balance")

        balance_after = balance_before - amount

        # Update balance
        db.execute(
            "UPDATE gamblers SET current_stake = %s WHERE gambler_id = %s",
            (balance_after, gambler["gambler_id"])
        )

        # Log transaction
        db.execute("""
            INSERT INTO stake_transactions
            (gambler_id, transaction_type, amount, balance_before, balance_after, transaction_ref)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            gambler["gambler_id"],
            "WITHDRAW",
            amount,
            balance_before,
            balance_after,
            "USER_WITHDRAW"
        ))

        if session_id:
            self.update_session_stake_stats(session_id, balance_after)

        return balance_after
    
    def adjust_stake(self, username, amount, session_id=None):
        gambler = db.execute(
            "SELECT * FROM gamblers WHERE username = %s",
            (username,),
            fetch=True
        )

        if not gambler:
            raise ValueError("Gambler not found")

        gambler = gambler[0]

        balance_before = gambler["current_stake"]
        balance_after = balance_before + amount

        if balance_after < 0:
            raise ValueError("Adjustment leads to negative balance")

        # Update balance
        db.execute(
            "UPDATE gamblers SET current_stake = %s WHERE gambler_id = %s",
            (balance_after, gambler["gambler_id"])
        )

        # Log transaction
        db.execute("""
            INSERT INTO stake_transactions
            (gambler_id, transaction_type, amount, balance_before, balance_after, transaction_ref)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            gambler["gambler_id"],
            "ADJUSTMENT",
            amount,
            balance_before,
            balance_after,
            "MANUAL_ADJUSTMENT"
        ))

        if session_id:
            self.update_session_stake_stats(session_id, balance_after)

        return balance_after
    
    def update_session_stake_stats(self, session_id, new_balance):
        session = db.execute(
            "SELECT peak_stake, lowest_stake FROM sessions WHERE session_id = %s",
            (session_id,),
            fetch=True
        )

        if not session:
            raise ValueError("Session not found")

        session = session[0]

        peak = session["peak_stake"]
        lowest = session["lowest_stake"]

        # Initialize if null
        if peak is None or new_balance > peak:
            peak = new_balance

        if lowest is None or new_balance < lowest:
            lowest = new_balance

        db.execute("""
            UPDATE sessions
            SET peak_stake = %s,
                lowest_stake = %s
            WHERE session_id = %s
        """, (peak, lowest, session_id))
    
    def get_stake_summary(self, username):
        query = """
        SELECT 
            SUM(CASE WHEN transaction_type = 'DEPOSIT' THEN amount ELSE 0 END) AS total_deposit,
            SUM(CASE WHEN transaction_type = 'WITHDRAW' THEN amount ELSE 0 END) AS total_withdraw,
            SUM(CASE WHEN transaction_type = 'ADJUSTMENT' THEN amount ELSE 0 END) AS total_adjustment,
            SUM(balance_after - balance_before) AS net_movement
        FROM stake_transactions st
        JOIN gamblers g ON st.gambler_id = g.gambler_id
        WHERE g.username = %s
        """

        result = db.execute(query, (username,), fetch=True)

        return result[0] if result else None
    
    def get_session_stake_summary(self, session_id):
        query = """
        SELECT 
            SUM(CASE WHEN transaction_type = 'DEPOSIT' THEN amount ELSE 0 END) AS total_deposit,
            SUM(CASE WHEN transaction_type = 'WITHDRAW' THEN amount ELSE 0 END) AS total_withdraw,
            SUM(balance_after - balance_before) AS net_movement
        FROM stake_transactions
        WHERE session_id = %s
        """

        result = db.execute(query, (session_id,), fetch=True)

        return result[0] if result else None

stake_service = StakeManagementService()