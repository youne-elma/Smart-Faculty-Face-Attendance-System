from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np

from app.config.settings import settings
from app.models.face import FaceBox
from app.models.recognition import RecognitionMatch
from app.models.student import KnownStudent
from app.services.detection.haar_detector import HaarCascadeDetector
from app.services.students.student_service import StudentService


class FaceNetDependencyError(RuntimeError):
    pass


class KnownFaceIndexError(RuntimeError):
    pass


@dataclass(frozen=True)
class KnownFaceEmbedding:
    student: KnownStudent
    embedding: np.ndarray


class FaceNetRecognizer:
    name = "facenet"

    def __init__(self, threshold: float | None = None) -> None:
        self.threshold = threshold or settings.face_recognition_threshold
        self.device, self.model, self.torch = self._load_model()

    def build_known_index(self) -> list[KnownFaceEmbedding]:
        students = StudentService().list_known_students().students
        detector = HaarCascadeDetector()
        known_embeddings: list[KnownFaceEmbedding] = []

        for student in students:
            for photo in student.photos:
                photo_path = settings.known_faces_dir / Path(photo.source_uri)
                frame = cv2.imread(str(photo_path))

                if frame is None:
                    continue

                faces = detector.detect(frame)
                if not faces:
                    continue

                face = self._largest_face(faces)
                embedding = self.embed_face(frame, face)
                known_embeddings.append(KnownFaceEmbedding(student=student, embedding=embedding))

        return known_embeddings

    def identify_face(
        self,
        frame: np.ndarray,
        face: FaceBox,
        known_embeddings: list[KnownFaceEmbedding],
    ) -> RecognitionMatch | None:
        if not known_embeddings:
            raise KnownFaceIndexError("No known face embeddings are available")

        query_embedding = self.embed_face(frame, face)
        best_match: RecognitionMatch | None = None

        for known in known_embeddings:
            score = self._cosine_similarity(query_embedding, known.embedding)
            if best_match is None or score > best_match.score:
                best_match = RecognitionMatch(
                    student_id=known.student.student_id,
                    display_name=known.student.display_name,
                    score=score,
                )

        if best_match and best_match.score >= self.threshold:
            return best_match

        return None

    def embed_face(self, frame: np.ndarray, face: FaceBox) -> np.ndarray:
        face_image = self._crop_face(frame, face)
        face_tensor = self._preprocess(face_image)

        with self.torch.no_grad():
            embedding = self.model(face_tensor.to(self.device)).detach().cpu().numpy()[0]

        norm = np.linalg.norm(embedding)
        if norm == 0:
            return embedding

        return embedding / norm

    def _load_model(self):
        try:
            import torch
            from facenet_pytorch import InceptionResnetV1
        except ImportError as exc:
            raise FaceNetDependencyError(
                "FaceNet dependencies are missing. Install facenet-pytorch and torch first."
            ) from exc

        device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
        model = InceptionResnetV1(pretrained=settings.facenet_pretrained_model).eval().to(device)
        return device, model, torch

    def _preprocess(self, face_image: np.ndarray):
        resized = cv2.resize(face_image, (160, 160), interpolation=cv2.INTER_AREA)
        rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
        normalized = (rgb.astype(np.float32) - 127.5) / 128.0
        tensor = self.torch.from_numpy(normalized).permute(2, 0, 1).unsqueeze(0)
        return tensor.float()

    def _crop_face(self, frame: np.ndarray, face: FaceBox) -> np.ndarray:
        height, width = frame.shape[:2]
        x1 = max(face.x, 0)
        y1 = max(face.y, 0)
        x2 = min(face.x + face.width, width)
        y2 = min(face.y + face.height, height)

        if x2 <= x1 or y2 <= y1:
            raise ValueError("Invalid face box for embedding")

        return frame[y1:y2, x1:x2]

    def _largest_face(self, faces: list[FaceBox]) -> FaceBox:
        return max(faces, key=lambda face: face.width * face.height)

    def _cosine_similarity(self, left: np.ndarray, right: np.ndarray) -> float:
        denominator = np.linalg.norm(left) * np.linalg.norm(right)
        if denominator == 0:
            return 0.0

        return float(np.dot(left, right) / denominator)
