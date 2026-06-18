import sqlite3

from app.database.connection import get_connection


class FaceEmbeddingRepository:
    def clear_model(self, model_name: str) -> None:
        with get_connection() as connection:
            connection.execute(
                "DELETE FROM face_embeddings WHERE model_name = ?;",
                (model_name,),
            )

    def list_student_photos(self) -> list[sqlite3.Row]:
        with get_connection() as connection:
            return connection.execute(
                """
                SELECT
                    s.id AS student_id,
                    s.student_code,
                    s.first_name,
                    s.last_name,
                    p.id AS photo_id,
                    p.source_uri,
                    p.storage_type
                FROM students s
                JOIN student_photos p ON p.student_id = s.id
                WHERE s.is_active = 1
                ORDER BY s.student_code, p.is_primary DESC, p.id;
                """
            ).fetchall()

    def upsert_embedding(
        self,
        student_id: int,
        student_photo_id: int | None,
        model_name: str,
        embedding_bytes: bytes,
        dimension: int,
    ) -> None:
        with get_connection() as connection:
            connection.execute(
                """
                INSERT INTO face_embeddings (
                    student_id, student_photo_id, model_name, embedding, dimension
                )
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(student_id, student_photo_id, model_name)
                DO UPDATE SET
                    embedding = excluded.embedding,
                    dimension = excluded.dimension,
                    created_at = CURRENT_TIMESTAMP;
                """,
                (student_id, student_photo_id, model_name, embedding_bytes, dimension),
            )

    def list_embeddings(self, model_name: str) -> list[sqlite3.Row]:
        with get_connection() as connection:
            return connection.execute(
                """
                SELECT
                    fe.id,
                    fe.student_id,
                    fe.student_photo_id,
                    fe.model_name,
                    fe.embedding,
                    fe.dimension,
                    s.student_code,
                    s.first_name,
                    s.last_name
                FROM face_embeddings fe
                JOIN students s ON s.id = fe.student_id
                WHERE fe.model_name = ?
                  AND s.is_active = 1
                ORDER BY s.student_code, fe.id;
                """,
                (model_name,),
            ).fetchall()

    def stats(self, model_name: str) -> sqlite3.Row:
        with get_connection() as connection:
            return connection.execute(
                """
                SELECT
                    COUNT(*) AS embeddings_count,
                    COUNT(DISTINCT student_id) AS students_count
                FROM face_embeddings
                WHERE model_name = ?;
                """,
                (model_name,),
            ).fetchone()
