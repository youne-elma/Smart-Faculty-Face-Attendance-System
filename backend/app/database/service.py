from pathlib import Path

from app.config.settings import BASE_DIR
from app.database.connection import get_connection, resolve_database_path


SCHEMA_PATH = BASE_DIR / "backend/app/database/schema.sql"
EXPECTED_TABLES = {
    "students",
    "student_photos",
    "face_embeddings",
    "attendance_sessions",
    "attendance_records",
    "recognition_events",
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

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS face_embeddings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                student_photo_id INTEGER,
                model_name TEXT NOT NULL,
                embedding BLOB NOT NULL,
                dimension INTEGER NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
                FOREIGN KEY (student_photo_id) REFERENCES student_photos(id) ON DELETE SET NULL,
                UNIQUE (student_id, student_photo_id, model_name)
            );
            """
        )
        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_face_embeddings_student_id
            ON face_embeddings(student_id);
            """
        )
        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_face_embeddings_model_name
            ON face_embeddings(model_name);
            """
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS recognition_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                student_id INTEGER,
                student_code TEXT,
                recognized INTEGER NOT NULL DEFAULT 0,
                message TEXT NOT NULL,
                score REAL,
                threshold REAL,
                faces_count INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES attendance_sessions(id) ON DELETE CASCADE,
                FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE SET NULL
            );
            """
        )
        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_recognition_events_session_id
            ON recognition_events(session_id);
            """
        )
        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_recognition_events_created_at
            ON recognition_events(created_at);
            """
        )
