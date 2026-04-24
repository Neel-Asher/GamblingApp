import mysql.connector
from config.settings import settings


class Database:

    def __init__(self):
        self._ensure_database()

    def _get_server_connection(self):
        return mysql.connector.connect(
            host=settings.db_host,
            port=settings.db_port,
            user=settings.db_user,
            password=settings.db_password
        )

    def _get_database_connection(self):
        return mysql.connector.connect(
            host=settings.db_host,
            port=settings.db_port,
            user=settings.db_user,
            password=settings.db_password,
            database=settings.db_name,
            charset=settings.db_charset,
            autocommit=settings.db_autocommit
        )

    def _ensure_database(self):
        conn = self._get_server_connection()
        cursor = conn.cursor()

        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {settings.db_name}")
        cursor.close()
        conn.close()

    def get_connection(self):
        return self._get_database_connection()

    def execute(self, query, params=None, fetch=False, many=False):
        conn = self.get_connection()
        cursor = conn.cursor(dictionary=True)

        try:
            if many:
                cursor.executemany(query, params)
            else:
                cursor.execute(query, params)

            if fetch:
                result = cursor.fetchall()
            else:
                result = None

            if not settings.db_autocommit:
                conn.commit()

            return result

        except Exception as e:
            conn.rollback()
            raise e

        finally:
            cursor.close()
            conn.close()

db = Database()