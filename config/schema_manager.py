from config.database import db


class SchemaManager:

    def create_tables(self):
        print("Creating gamblers...")
        self._create_gamblers_table()

        print("Creating betting_preferences...")
        self._create_betting_preferences_table()

        print("Creating sessions...")
        self._create_sessions_table()

        print("Creating session_parameters...")
        self._create_session_parameters_table()

        print("Creating betting_strategies...")
        self._create_betting_strategies_table()

        print("Creating bets...")
        self._create_bets_table()

        print("Creating game_records...")
        self._create_game_records_table()

        print("Creating stake_transactions...")
        self._create_stake_transactions_table()

        print("Creating pause_records...")
        self._create_pause_records_table()

        print("Creating running_totals_snapshots...")
        self._create_running_totals_snapshots_table()

        print("Creating validation_events...")
        self._create_validation_events_table()

        print("Seeding betting_strategies...")
        self._seed_betting_strategies()

    def _create_gamblers_table(self):
        query = """
        CREATE TABLE IF NOT EXISTS gamblers (
            gambler_id BIGINT PRIMARY KEY AUTO_INCREMENT,
            username VARCHAR(50) NOT NULL UNIQUE,
            full_name VARCHAR(100),
            email VARCHAR(100) UNIQUE,
            is_active BOOLEAN DEFAULT TRUE,
            initial_stake DECIMAL(15,2) NOT NULL,
            current_stake DECIMAL(15,2) NOT NULL,
            win_threshold DECIMAL(15,2),
            loss_threshold DECIMAL(15,2),
            min_required_stake DECIMAL(15,2),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        )
        """
        db.execute(query)
    
    def _create_betting_preferences_table(self):
        query = """
        CREATE TABLE IF NOT EXISTS betting_preferences (
            preference_id BIGINT PRIMARY KEY AUTO_INCREMENT,
            gambler_id BIGINT NOT NULL UNIQUE,
            min_bet DECIMAL(15,2) NOT NULL,
            max_bet DECIMAL(15,2) NOT NULL,
            preferred_game_type VARCHAR(50),
            auto_play_enabled BOOLEAN DEFAULT FALSE,
            auto_play_max_games INT,
            session_loss_limit DECIMAL(15,2),
            session_win_target DECIMAL(15,2),
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            CONSTRAINT fk_pref_gambler FOREIGN KEY (gambler_id)
                REFERENCES gamblers(gambler_id)
                ON DELETE CASCADE
        )
        """
        db.execute(query)

    def _create_sessions_table(self):
        query = """
        CREATE TABLE IF NOT EXISTS sessions (
            session_id BIGINT PRIMARY KEY AUTO_INCREMENT,
            gambler_id BIGINT NOT NULL,
            status VARCHAR(20),
            end_reason VARCHAR(50),
            starting_stake DECIMAL(15,2),
            ending_stake DECIMAL(15,2),
            peak_stake DECIMAL(15,2),
            lowest_stake DECIMAL(15,2),
            max_games INT,
            games_played INT DEFAULT 0,
            total_pause_seconds INT DEFAULT 0,
            started_at DATETIME,
            ended_at DATETIME,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT fk_session_gambler FOREIGN KEY (gambler_id)
                REFERENCES gamblers(gambler_id)
                ON DELETE CASCADE
        )
        """
        db.execute(query)
    
    def _create_session_parameters_table(self):
        query = """
        CREATE TABLE IF NOT EXISTS session_parameters (
            parameter_id BIGINT PRIMARY KEY AUTO_INCREMENT,
            session_id BIGINT NOT NULL UNIQUE,
            lower_limit DECIMAL(15,2),
            upper_limit DECIMAL(15,2),
            min_bet DECIMAL(15,2),
            max_bet DECIMAL(15,2),
            default_win_probability DECIMAL(5,4),
            max_session_minutes INT,
            strict_mode BOOLEAN,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT fk_params_session FOREIGN KEY (session_id)
                REFERENCES sessions(session_id)
                ON DELETE CASCADE
        )
        """
        db.execute(query)
    
    def _create_betting_strategies_table(self):
        query = """
        CREATE TABLE IF NOT EXISTS betting_strategies (
            strategy_id TINYINT PRIMARY KEY,
            strategy_code VARCHAR(50) UNIQUE,
            strategy_name VARCHAR(100),
            strategy_type VARCHAR(50),
            is_progressive BOOLEAN,
            is_active BOOLEAN DEFAULT TRUE,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """
        db.execute(query)
    
    def _seed_betting_strategies(self):
        query = """
        INSERT INTO betting_strategies 
        (strategy_id, strategy_code, strategy_name, strategy_type, is_progressive)
        VALUES (%s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE strategy_name = VALUES(strategy_name)
        """

        strategies = [
            (1, "FLAT", "Flat Betting", "FIXED", False),
            (2, "MARTINGALE", "Martingale", "PROGRESSIVE", True),
            (3, "FIBONACCI", "Fibonacci", "PROGRESSIVE", True),
            (4, "PAROLI", "Paroli", "POSITIVE_PROGRESSIVE", True)
        ]

        db.execute(query, strategies, many=True)

    def _create_bets_table(self):
        query = """
        CREATE TABLE IF NOT EXISTS bets (
            bet_id BIGINT PRIMARY KEY AUTO_INCREMENT,
            session_id BIGINT NOT NULL,
            gambler_id BIGINT NOT NULL,
            strategy_id TINYINT,
            game_index INT,
            bet_amount DECIMAL(15,2) NOT NULL,
            win_probability DECIMAL(5,4),
            odds_type VARCHAR(20),
            odds_value DECIMAL(10,4),
            potential_win DECIMAL(15,2),
            stake_before DECIMAL(15,2),
            stake_after DECIMAL(15,2),
            is_settled BOOLEAN DEFAULT FALSE,
            placed_at DATETIME DEFAULT CURRENT_TIMESTAMP,

            CONSTRAINT fk_bet_session FOREIGN KEY (session_id)
                REFERENCES sessions(session_id)
                ON DELETE CASCADE,

            CONSTRAINT fk_bet_gambler FOREIGN KEY (gambler_id)
                REFERENCES gamblers(gambler_id)
                ON DELETE CASCADE,

            CONSTRAINT fk_bet_strategy FOREIGN KEY (strategy_id)
                REFERENCES betting_strategies(strategy_id)
        )
        """
        db.execute(query)
    
    def _create_game_records_table(self):
        query = """
        CREATE TABLE IF NOT EXISTS game_records (
            game_id BIGINT PRIMARY KEY AUTO_INCREMENT,
            session_id BIGINT NOT NULL,
            bet_id BIGINT NOT NULL UNIQUE,
            outcome VARCHAR(10),
            payout_amount DECIMAL(15,2),
            loss_amount DECIMAL(15,2),
            net_change DECIMAL(15,2),
            stake_before DECIMAL(15,2),
            stake_after DECIMAL(15,2),
            consecutive_win_streak INT,
            consecutive_loss_streak INT,
            game_duration_ms INT,
            resolved_at DATETIME DEFAULT CURRENT_TIMESTAMP,

            CONSTRAINT fk_game_session FOREIGN KEY (session_id)
                REFERENCES sessions(session_id)
                ON DELETE CASCADE,

            CONSTRAINT fk_game_bet FOREIGN KEY (bet_id)
                REFERENCES bets(bet_id)
                ON DELETE CASCADE
        )
        """
        db.execute(query)
    
    def _create_stake_transactions_table(self):
        query = """
        CREATE TABLE IF NOT EXISTS stake_transactions (
            transaction_id BIGINT PRIMARY KEY AUTO_INCREMENT,
            session_id BIGINT,
            gambler_id BIGINT NOT NULL,
            bet_id BIGINT,
            game_id BIGINT,
            transaction_type VARCHAR(30),
            amount DECIMAL(15,2),
            balance_before DECIMAL(15,2),
            balance_after DECIMAL(15,2),
            transaction_ref VARCHAR(100),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

            CONSTRAINT fk_txn_session FOREIGN KEY (session_id)
                REFERENCES sessions(session_id)
                ON DELETE SET NULL,

            CONSTRAINT fk_txn_gambler FOREIGN KEY (gambler_id)
                REFERENCES gamblers(gambler_id)
                ON DELETE CASCADE,

            CONSTRAINT fk_txn_bet FOREIGN KEY (bet_id)
                REFERENCES bets(bet_id)
                ON DELETE SET NULL,

            CONSTRAINT fk_txn_game FOREIGN KEY (game_id)
                REFERENCES game_records(game_id)
                ON DELETE SET NULL
        )
        """
        db.execute(query)

    def _create_pause_records_table(self):
        query = """
        CREATE TABLE IF NOT EXISTS pause_records (
            pause_id BIGINT PRIMARY KEY AUTO_INCREMENT,
            session_id BIGINT NOT NULL,
            pause_reason VARCHAR(100),
            paused_at DATETIME,
            resumed_at DATETIME,
            pause_seconds INT,

            CONSTRAINT fk_pause_session FOREIGN KEY (session_id)
                REFERENCES sessions(session_id)
                ON DELETE CASCADE
        )
        """
        db.execute(query)
    
    def _create_running_totals_snapshots_table(self):
        query = """
        CREATE TABLE IF NOT EXISTS running_totals_snapshots (
            snapshot_id BIGINT PRIMARY KEY AUTO_INCREMENT,
            session_id BIGINT NOT NULL,
            game_id BIGINT,
            total_games INT,
            total_wins INT,
            total_losses INT,
            total_pushes INT,
            total_winnings DECIMAL(15,2),
            total_losses_amount DECIMAL(15,2),
            net_profit DECIMAL(15,2),
            win_rate DECIMAL(6,4),
            profit_factor DECIMAL(10,4),
            roi DECIMAL(10,4),
            longest_win_streak INT,
            longest_loss_streak INT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

            CONSTRAINT fk_snapshot_session FOREIGN KEY (session_id)
                REFERENCES sessions(session_id)
                ON DELETE CASCADE,

            CONSTRAINT fk_snapshot_game FOREIGN KEY (game_id)
                REFERENCES game_records(game_id)
                ON DELETE SET NULL
        )
        """
        db.execute(query)
    
    def _create_validation_events_table(self):
        query = """
        CREATE TABLE IF NOT EXISTS validation_events (
            validation_id BIGINT PRIMARY KEY AUTO_INCREMENT,
            session_id BIGINT,
            gambler_id BIGINT,
            error_type VARCHAR(50),
            severity VARCHAR(20),
            field_name VARCHAR(50),
            attempted_value VARCHAR(100),
            message VARCHAR(255),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

            CONSTRAINT fk_validation_session FOREIGN KEY (session_id)
                REFERENCES sessions(session_id)
                ON DELETE SET NULL,

            CONSTRAINT fk_validation_gambler FOREIGN KEY (gambler_id)
                REFERENCES gamblers(gambler_id)
                ON DELETE SET NULL
        )
        """
        db.execute(query)


schema_manager = SchemaManager()