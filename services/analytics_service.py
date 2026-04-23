from config.database import db


class AnalyticsService:

    def get_session_summary(self, session_id):
        result = db.execute("""
            SELECT *
            FROM running_totals_snapshots
            WHERE session_id = %s
            ORDER BY snapshot_id DESC
            LIMIT 1
        """, (session_id,), fetch=True)

        if not result:
            return None

        return result[0]

    def get_full_timeline(self, session_id):
        return db.execute("""
            SELECT *
            FROM running_totals_snapshots
            WHERE session_id = %s
            ORDER BY snapshot_id ASC
        """, (session_id,), fetch=True)

    def get_basic_stats(self, session_id):
        result = db.execute("""
            SELECT 
                COUNT(*) as total_games,
                SUM(CASE WHEN outcome = 'WIN' THEN 1 ELSE 0 END) as wins,
                SUM(CASE WHEN outcome = 'LOSS' THEN 1 ELSE 0 END) as losses
            FROM game_records
            WHERE session_id = %s
        """, (session_id,), fetch=True)

        return result[0] if result else None


analytics_service = AnalyticsService()