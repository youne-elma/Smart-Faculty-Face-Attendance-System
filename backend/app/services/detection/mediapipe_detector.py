from functools import lru_cache

import cv2
import numpy as np

from app.config.settings import settings
from app.models.face import FaceBox


class MediaPipeDependencyError(RuntimeError):
    pass


class MediaPipeFaceDetector:
    name = "mediapipe_face_detection"

    def __init__(self, min_confidence: float | None = None) -> None:
        self.min_confidence = min_confidence or settings.mediapipe_face_min_confidence
        self.mp, self.vision, self.detector = self._load_detector()

    def detect(self, frame: np.ndarray) -> list[FaceBox]:
        height, width = frame.shape[:2]
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = self.mp.Image(image_format=self.mp.ImageFormat.SRGB, data=rgb_frame)
        results = self.detector.detect(mp_image)

        if not results.detections:
            return []

        faces: list[FaceBox] = []
        for detection in results.detections:
            box = detection.bounding_box
            x = max(int(box.origin_x), 0)
            y = max(int(box.origin_y), 0)
            box_width = min(int(box.width), width - x)
            box_height = min(int(box.height), height - y)

            if box_width <= 0 or box_height <= 0:
                continue

            faces.append(
                FaceBox(
                    x=x,
                    y=y,
                    width=box_width,
                    height=box_height,
                )
            )

        return faces

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

    def _load_detector(self):
        try:
            import mediapipe as mp
            from mediapipe.tasks import python
            from mediapipe.tasks.python import vision
        except ImportError as exc:
            raise MediaPipeDependencyError(
                "MediaPipe is missing. Install backend requirements before using face detection."
            ) from exc

        model_path = settings.mediapipe_face_model_path
        if not model_path.exists():
            raise MediaPipeDependencyError(
                f"MediaPipe face model is missing at {model_path}. "
                "Download blaze_face_short_range.tflite into backend/data/models."
            )

        base_options = python.BaseOptions(model_asset_path=str(model_path))
        options = vision.FaceDetectorOptions(
            base_options=base_options,
            running_mode=vision.RunningMode.IMAGE,
            min_detection_confidence=self.min_confidence,
        )
        return mp, vision, vision.FaceDetector.create_from_options(options)


@lru_cache(maxsize=1)
def get_mediapipe_face_detector() -> MediaPipeFaceDetector:
    return MediaPipeFaceDetector()
