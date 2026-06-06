from pathlib import Path

from app.config.settings import BASE_DIR
from app.database.connection import get_connection, resolve_database_path


SCHEMA_PATH = BASE_DIR / "backend/app/database/schema.sql"
EXPECTED_TABLES = {
    "students",
    "student_photos",
    "attendance_sessions",
    "attendance_records",
    "admin_users",
}


class DatabaseService:
    def initialize(self) -> dict[str, object]:
        schema_sql = SCHEMA_PATH.read_text(encoding="utf-8")

        with get_connection() as connection:
            connection.executescript(schema_sql)
            self._apply_lightweight_migrations(connection)

        return self.status()

    def status(self) -> dict[str, object]:
        database_path = resolve_database_path()
        tables = self._list_tables() if database_path.exists() else []
        missing_tables = sorted(EXPECTED_TABLES.difference(tables))

        return {
            "database_path": str(database_path),
            "exists": database_path.exists(),
            "initialized": not missing_tables,
            "tables": sorted(tables),
            "missing_tables": missing_tables,
        }

    def _list_tables(self) -> set[str]:
        with get_connection() as connection:
            rows = connection.execute(
                """
                SELECT name
                FROM sqlite_master
                WHERE type = 'table'
                  AND name NOT LIKE 'sqlite_%'
                ORDER BY name;
                """
            ).fetchall()

        return {row["name"] for row in rows}

    def _apply_lightweight_migrations(self, connection) -> None:
        columns = {
            row["name"]
            for row in connection.execute("PRAGMA table_info(attendance_sessions);").fetchall()
        }

        if "admin_user_id" not in columns:
            connection.execute("ALTER TABLE attendance_sessions ADD COLUMN admin_user_id INTEGER;")

        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_attendance_sessions_admin_user_id
            ON attendance_sessions(admin_user_id);
            """
        )
