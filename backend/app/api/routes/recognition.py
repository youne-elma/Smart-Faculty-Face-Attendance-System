from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import get_current_admin
from app.models.auth import AdminUserPublic
from app.models.recognition import FaceRecognitionResult, RecognizedFace
from app.services.camera.esp32_camera import (
    CameraConnectionError,
    CameraFrameDecodeError,
    CameraStreamFrameError,
    Esp32CameraClient,
)
from app.services.detection.mediapipe_detector import (
    MediaPipeDependencyError,
    get_mediapipe_face_detector,
)
from app.services.recognition.facenet_recognizer import (
    FaceNetDependencyError,
    FaceNetRecognizer,
    KnownFaceIndexError,
    get_facenet_recognizer,
)

router = APIRouter()


@router.get("/identify", response_model=FaceRecognitionResult)
def identify_faces() -> FaceRecognitionResult:
    try:
        camera = Esp32CameraClient()
        detector = get_mediapipe_face_detector()
        recognizer = get_facenet_recognizer()

        frame = camera.fetch_frame()
        faces = detector.detect(frame)
        known_embeddings = recognizer.build_known_index()

        recognized_faces: list[RecognizedFace] = []
        for face in faces:
            match = recognizer.find_best_match(frame, face, known_embeddings)
            recognized_faces.append(
                RecognizedFace(
                    box=face,
                    recognized=match is not None and match.score >= recognizer.threshold,
                    best_match=match,
                )
            )
    except FaceNetDependencyError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except MediaPipeDependencyError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except (CameraConnectionError, CameraStreamFrameError) as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except (CameraFrameDecodeError, KnownFaceIndexError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return FaceRecognitionResult(
        detector=detector.name,
        recognizer=recognizer.name,
        threshold=recognizer.threshold,
        known_embeddings_count=len(known_embeddings),
        faces_count=len(recognized_faces),
        faces=recognized_faces,
    )


@router.post("/known-index/refresh")
def refresh_known_index(
    current_admin: AdminUserPublic = Depends(get_current_admin),
) -> dict[str, object]:
    try:
        recognizer = get_facenet_recognizer()
        known_embeddings = recognizer.refresh_known_index()
    except FaceNetDependencyError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except MediaPipeDependencyError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    return {
        "status": "ok",
        "known_embeddings_count": len(known_embeddings),
    }
