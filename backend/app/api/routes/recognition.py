from fastapi import APIRouter, HTTPException

from app.models.recognition import FaceRecognitionResult, RecognizedFace
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
        detector = MediaPipeFaceDetector()
        recognizer = get_facenet_recognizer()

        frame = camera.fetch_frame()
        faces = detector.detect(frame)
        known_embeddings = recognizer.build_known_index()

        recognized_faces: list[RecognizedFace] = []
        for face in faces:
            match = recognizer.identify_face(frame, face, known_embeddings)
            recognized_faces.append(
                RecognizedFace(
                    box=face,
                    recognized=match is not None,
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
