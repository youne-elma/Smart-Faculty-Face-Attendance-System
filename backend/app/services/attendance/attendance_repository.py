import sqlite3
from datetime import datetime

from app.database.connection import get_connection
from app.models.attendance import AttendanceSessionCreate


class AttendanceRepository:
    def create_session(self, payload: AttendanceSessionCreate, admin_user_id: int) -> sqlite3.Row:
        with get_connection() as connection:
            cursor = connection.execute(
                """
                INSERT INTO attendance_sessions (
                    admin_user_id, title, session_type, course_name, group_name, starts_at, ends_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    admin_user_id,
                    payload.title,
                    payload.session_type,
                    payload.course_name,
                    payload.group_name,
                    self._format_datetime(payload.starts_at),
                    self._format_datetime(payload.ends_at),
                ),
            )
            session_id = int(cursor.lastrowid)

        session = self.get_session(session_id)
        if session is None:
            raise RuntimeError("Unable to create attendance session")

        return session

    def list_sessions(self) -> list[sqlite3.Row]:
        with get_connection() as connection:
            return connection.execute(
                """
                SELECT id, admin_user_id, title, session_type, course_name, group_name,
                       starts_at, ends_at, created_at
                FROM attendance_sessions
                ORDER BY created_at DESC, id DESC;
                """
            ).fetchall()

    def get_session(self, session_id: int) -> sqlite3.Row | None:
        with get_connection() as connection:
            return connection.execute(
                """
                SELECT id, admin_user_id, title, session_type, course_name, group_name,
                       starts_at, ends_at, created_at
                FROM attendance_sessions
                WHERE id = ?;
                """,
                (session_id,),
            ).fetchone()

    def list_records(self, session_id: int) -> list[sqlite3.Row]:
        with get_connection() as connection:
            return connection.execute(
                """
                SELECT
                    ar.id,
                    ar.session_id,
                    ar.student_id,
                    s.student_code,
                    s.first_name,
                    s.last_name,
                    s.group_name,
                    ar.status,
                    ar.recognized_at,
                    ar.recognition_score
                FROM attendance_records ar
                JOIN students s ON s.id = ar.student_id
                WHERE ar.session_id = ?
                ORDER BY s.last_name, s.first_name, s.student_code;
                """,
                (session_id,),
            ).fetchall()

    def get_or_create_student(
        self,
        student_code: str,
        first_name: str,
        last_name: str,
        group_name: str | None = None,
        email: str | None = None,
    ) -> tuple[sqlite3.Row, bool]:
        with get_connection() as connection:
            existing = connection.execute(
                """
                SELECT id, student_code, first_name, last_name, group_name, email, is_active
                FROM students
                WHERE student_code = ?;
                """,
                (student_code,),
            ).fetchone()

            if existing:
                return existing, False

            cursor = connection.execute(
                """
                INSERT INTO students (student_code, first_name, last_name, group_name, email)
                VALUES (?, ?, ?, ?, ?);
                """,
                (student_code, first_name, last_name, group_name, email),
            )
            student_id = int(cursor.lastrowid)

            student = connection.execute(
                """
                SELECT id, student_code, first_name, last_name, group_name, email, is_active
                FROM students
                WHERE id = ?;
                """,
                (student_id,),
            ).fetchone()

        if student is None:
            raise RuntimeError("Unable to create student from attendance import")

        return student, True

    def ensure_absent_record(self, session_id: int, student_id: int) -> sqlite3.Row:
        with get_connection() as connection:
            connection.execute(
                """
                INSERT OR IGNORE INTO attendance_records (session_id, student_id, status)
                VALUES (?, ?, 'absent');
                """,
                (session_id, student_id),
            )
            record = connection.execute(
                """
                SELECT id, session_id, student_id, status, recognized_at, recognition_score
                FROM attendance_records
                WHERE session_id = ? AND student_id = ?;
                """,
                (session_id, student_id),
            ).fetchone()

        if record is None:
            raise RuntimeError("Unable to create attendance record")

        return record

    def _format_datetime(self, value: datetime | None) -> str | None:
        return value.isoformat() if value else None
