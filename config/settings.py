import os
from dotenv import load_dotenv
from decimal import Decimal

load_dotenv()

class Settings:

    def __init__(self):
        self.app_name = self._get("APP_NAME")
        self.app_env = self._get("APP_ENV")
        self.app_debug = self._get_bool("APP_DEBUG")

        self.db_host = self._get("DB_HOST")
        self.db_port = self._get_int("DB_PORT")
        self.db_name = self._get("DB_NAME")
        self.db_user = self._get("DB_USER")
        self.db_password = self._get("DB_PASSWORD")
        self.db_charset = self._get("DB_CHARSET")
        self.db_autocommit = self._get_bool("DB_AUTOCOMMIT")

        self.session_default_win_probability = self._get_decimal("SESSION_DEFAULT_WIN_PROBABILITY")
        self.session_default_max_games = self._get_int("SESSION_DEFAULT_MAX_GAMES")
        self.session_default_max_minutes = self._get_int("SESSION_DEFAULT_MAX_MINUTES")

        self.validation_strict_mode = self._get_bool("VALIDATION_STRICT_MODE")

        self.min_initial_stake = self._get_decimal("MIN_INITIAL_STAKE")
        self.max_initial_stake = self._get_decimal("MAX_INITIAL_STAKE")

    def _get(self, key):
        value = os.getenv(key)
        if value is None:
            raise ValueError(f"Missing required env variable: {key}")
        return value

    def _get_int(self, key):
        try:
            return int(self._get(key))
        except ValueError:
            raise ValueError(f"Invalid integer for {key}")

    def _get_bool(self, key):
        value = self._get(key).lower()
        if value in ["true", "1", "yes"]:
            return True
        if value in ["false", "0", "no"]:
            return False
        raise ValueError(f"Invalid boolean for {key}")

    def _get_decimal(self, key):
        try:
            return Decimal(self._get(key))
        except:
            raise ValueError(f"Invalid decimal for {key}")


settings = Settings()