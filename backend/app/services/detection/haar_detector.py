from pathlib import Path

import cv2
import numpy as np

from app.models.face import FaceBox


class HaarCascadeLoadError(RuntimeError):
    pass


class HaarCascadeDetector:
    name = "haar_cascade"

    def __init__(self, cascade_path: str | Path | None = None) -> None:
        self.cascade_path = Path(cascade_path) if cascade_path else self._default_cascade_path()
        self.classifier = cv2.CascadeClassifier(str(self.cascade_path))

        if self.classifier.empty():
            raise HaarCascadeLoadError(f"Unable to load Haar Cascade from {self.cascade_path}")

    def detect(self, frame: np.ndarray) -> list[FaceBox]:
        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray_frame = cv2.equalizeHist(gray_frame)

        detections = self.classifier.detectMultiScale(
            gray_frame,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(40, 40),
            flags=cv2.CASCADE_SCALE_IMAGE,
        )

        return [
            FaceBox(x=int(x), y=int(y), width=int(width), height=int(height))
            for x, y, width, height in detections
        ]

    def draw_detections(self, frame: np.ndarray, faces: list[FaceBox]) -> np.ndarray:
        annotated_frame = frame.copy()

        for face in faces:
            top_left = (face.x, face.y)
            bottom_right = (face.x + face.width, face.y + face.height)
            cv2.rectangle(annotated_frame, top_left, bottom_right, (0, 255, 0), 2)

        return annotated_frame

    def encode_jpeg(self, frame: np.ndarray) -> bytes:
        success, buffer = cv2.imencode(".jpg", frame)

        if not success:
            raise ValueError("Unable to encode frame as JPEG")

        return buffer.tobytes()

    def _default_cascade_path(self) -> Path:
        return Path(cv2.data.haarcascades) / "haarcascade_frontalface_default.xml"
