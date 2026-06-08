import sqlite3

from app.database.connection import get_connection
from app.models.student import StudentCreate, StudentPhotoCreate


class StudentRepository:
    def list_students(self) -> list[sqlite3.Row]:
        with get_connection() as connection:
            return connection.execute(
                """
                SELECT id, student_code, first_name, last_name, group_name, email, is_active
                FROM students
                ORDER BY last_name, first_name, student_code;
                """
            ).fetchall()

    def get_by_code(self, student_code: str) -> sqlite3.Row | None:
        with get_connection() as connection:
            return connection.execute(
                """
                SELECT id, student_code, first_name, last_name, group_name, email, is_active
                FROM students
                WHERE student_code = ?;
                """,
                (student_code,),
            ).fetchone()

    def create_student(self, payload: StudentCreate) -> sqlite3.Row:
        try:
            with get_connection() as connection:
                connection.execute(
                    """
                    INSERT INTO students (student_code, first_name, last_name, group_name, email)
                    VALUES (?, ?, ?, ?, ?);
                    """,
                    (
                        payload.student_code,
                        payload.first_name,
                        payload.last_name,
                        payload.group_name,
                        payload.email,
                    ),
                )
        except sqlite3.IntegrityError as exc:
            raise ValueError(f"Student already exists: {payload.student_code}") from exc

        student = self.get_by_code(payload.student_code)
        if student is None:
            raise RuntimeError("Unable to create student")

        return student

    def add_photo(self, student_id: int, payload: StudentPhotoCreate) -> sqlite3.Row:
        try:
            with get_connection() as connection:
                connection.execute(
                    """
                    INSERT INTO student_photos (student_id, source_uri, storage_type, is_primary)
                    VALUES (?, ?, ?, ?);
                    """,
                    (
                        student_id,
                        payload.source_uri,
                        payload.storage_type,
                        int(payload.is_primary),
                    ),
                )
        except sqlite3.IntegrityError as exc:
            raise ValueError(f"Photo already exists for this student: {payload.source_uri}") from exc

        with get_connection() as connection:
            photo = connection.execute(
                """
                SELECT id, student_id, source_uri, storage_type, is_primary
                FROM student_photos
                WHERE student_id = ? AND source_uri = ?;
                """,
                (student_id, payload.source_uri),
            ).fetchone()

        if photo is None:
            raise RuntimeError("Unable to add student photo")

        return photo

    def list_known_students_with_photos(self) -> list[sqlite3.Row]:
        with get_connection() as connection:
            return connection.execute(
                """
                SELECT
                    s.id,
                    s.student_code,
                    s.first_name,
                    s.last_name,
                    p.source_uri,
                    p.storage_type
                FROM students s
                JOIN student_photos p ON p.student_id = s.id
                WHERE s.is_active = 1
                ORDER BY s.last_name, s.first_name, s.student_code, p.is_primary DESC, p.id;
                """
            ).fetchall()
