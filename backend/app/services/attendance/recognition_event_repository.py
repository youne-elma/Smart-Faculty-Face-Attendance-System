import sqlite3

from app.database.connection import get_connection
from app.models.attendance import RecognitionEventCreate


class RecognitionEventRepository:
    def create(self, event: RecognitionEventCreate) -> sqlite3.Row:
        with get_connection() as connection:
            cursor = connection.execute(
                """
                INSERT INTO recognition_events (
                    session_id,
                    student_id,
                    student_code,
                    recognized,
                    message,
                    score,
                    threshold,
                    faces_count
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    event.session_id,
                    event.student_id,
                    event.student_code,
                    1 if event.recognized else 0,
                    event.message,
                    event.score,
                    event.threshold,
                    event.faces_count,
                ),
            )
            event_id = int(cursor.lastrowid)

            row = connection.execute(
                """
                SELECT id, session_id, student_id, student_code, recognized, message,
                       score, threshold, faces_count, created_at
                FROM recognition_events
                WHERE id = ?;
                """,
                (event_id,),
            ).fetchone()

        if row is None:
            raise RuntimeError("Unable to create recognition event")

        return row

    def list_by_session(self, session_id: int, limit: int = 200) -> list[sqlite3.Row]:
        with get_connection() as connection:
            return connection.execute(
                """
                SELECT id, session_id, student_id, student_code, recognized, message,
                       score, threshold, faces_count, created_at
                FROM recognition_events
                WHERE session_id = ?
                ORDER BY created_at DESC, id DESC
                LIMIT ?;
                """,
                (session_id, limit),
            ).fetchall()

    def list_by_session_for_export(self, session_id: int) -> list[sqlite3.Row]:
        with get_connection() as connection:
            return connection.execute(
                """
                SELECT id, session_id, student_id, student_code, recognized, message,
                       score, threshold, faces_count, created_at
                FROM recognition_events
                WHERE session_id = ?
                ORDER BY created_at ASC, id ASC;
                """,
                (session_id,),
            ).fetchall()
