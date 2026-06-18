from pathlib import Path

import cv2
import numpy as np

from app.config.settings import settings
from app.models.embedding import EmbeddingBuildResult, EmbeddingStats
from app.services.detection.mediapipe_detector import get_mediapipe_face_detector
from app.services.recognition.embedding_repository import FaceEmbeddingRepository
from app.services.recognition.facenet_recognizer import get_facenet_recognizer


class FaceEmbeddingService:
    def __init__(self, repository: FaceEmbeddingRepository | None = None) -> None:
        self.repository = repository or FaceEmbeddingRepository()

    def rebuild_embeddings(self) -> EmbeddingBuildResult:
        recognizer = get_facenet_recognizer()
        detector = get_mediapipe_face_detector()
        photos = self.repository.list_student_photos()
        processed = 0
        created = 0
        skipped = 0

        self.repository.clear_model(recognizer.name)

        for photo in photos:
            processed += 1
            photo_path = self._resolve_photo_path(str(photo["source_uri"]))
            frame = cv2.imread(str(photo_path))

            if frame is None:
                skipped += 1
                continue

            faces = detector.detect(frame)
            if not faces:
                skipped += 1
                continue

            face = max(faces, key=lambda item: item.width * item.height)
            embedding = recognizer.embed_face(frame, face).astype(np.float32)
            self.repository.upsert_embedding(
                student_id=int(photo["student_id"]),
                student_photo_id=int(photo["photo_id"]),
                model_name=recognizer.name,
                embedding_bytes=embedding.tobytes(),
                dimension=int(embedding.shape[0]),
            )
            created += 1

        recognizer.refresh_known_index()
        return EmbeddingBuildResult(
            model_name=recognizer.name,
            photos_processed=processed,
            embeddings_created=created,
            skipped_photos=skipped,
        )

    def stats(self) -> EmbeddingStats:
        model_name = get_facenet_recognizer().name
        row = self.repository.stats(model_name)
        return EmbeddingStats(
            model_name=model_name,
            embeddings_count=int(row["embeddings_count"]),
            students_count=int(row["students_count"]),
        )

    def _resolve_photo_path(self, source_uri: str) -> Path:
        photo_path = Path(source_uri)
        if photo_path.is_absolute():
            return photo_path
        return settings.known_faces_dir / photo_path
