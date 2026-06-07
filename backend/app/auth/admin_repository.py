import sqlite3

from app.database.connection import get_connection


class AdminRepository:
    def get_by_username(self, username: str) -> sqlite3.Row | None:
        with get_connection() as connection:
            return connection.execute(
                """
                SELECT id, username, password_hash, is_active
                FROM admin_users
                WHERE username = ?;
                """,
                (username,),
            ).fetchone()

    def get_by_id(self, admin_id: int) -> sqlite3.Row | None:
        with get_connection() as connection:
            return connection.execute(
                """
                SELECT id, username, password_hash, is_active
                FROM admin_users
                WHERE id = ?;
                """,
                (admin_id,),
            ).fetchone()

    def create_or_update(self, username: str, password_hash: str) -> sqlite3.Row:
        with get_connection() as connection:
            existing = connection.execute(
                "SELECT id FROM admin_users WHERE username = ?;",
                (username,),
            ).fetchone()

            if existing:
                connection.execute(
                    """
                    UPDATE admin_users
                    SET password_hash = ?, is_active = 1, updated_at = CURRENT_TIMESTAMP
                    WHERE username = ?;
                    """,
                    (password_hash, username),
                )
            else:
                connection.execute(
                    """
                    INSERT INTO admin_users (username, password_hash)
                    VALUES (?, ?);
                    """,
                    (username, password_hash),
                )

        admin = self.get_by_username(username)
        if admin is None:
            raise RuntimeError("Unable to create admin user")

        return admin
