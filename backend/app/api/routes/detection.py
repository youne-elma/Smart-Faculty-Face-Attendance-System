from fastapi import APIRouter, HTTPException, Response

from app.models.face import FaceDetectionResult
from app.services.camera.esp32_camera import (
    CameraConnectionError,
    CameraFrameDecodeError,
    CameraStreamFrameError,
    Esp32CameraClient,
)
from app.services.detection.mediapipe_detector import (
    MediaPipeDependencyError,
    MediaPipeFaceDetector,
)

router = APIRouter()


@router.get("/faces", response_model=FaceDetectionResult)
def detect_faces() -> FaceDetectionResult:
    camera = Esp32CameraClient()
    detector = _build_detector()

    try:
        frame = camera.fetch_frame()
        faces = detector.detect(frame)
    except (CameraConnectionError, CameraStreamFrameError) as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except CameraFrameDecodeError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return FaceDetectionResult(
        detector=detector.name,
        faces_count=len(faces),
        faces=faces,
    )


@router.get("/preview")
def detection_preview() -> Response:
    camera = Esp32CameraClient()
    detector = _build_detector()

    try:
        frame = camera.fetch_frame()
        faces = detector.detect(frame)
        annotated_frame = detector.draw_detections(frame, faces)
        image_bytes = detector.encode_jpeg(annotated_frame)
    except (CameraConnectionError, CameraStreamFrameError) as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except CameraFrameDecodeError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return Response(content=image_bytes, media_type="image/jpeg")


def _build_detector() -> MediaPipeFaceDetector:
    try:
        return MediaPipeFaceDetector()
    except MediaPipeDependencyError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
