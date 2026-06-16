from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse

from app.api.dependencies import get_current_admin
from app.models.auth import AdminUserPublic
from app.models.metrics import BenchmarkFile, RecognitionBenchmarkResult
from app.services.camera.esp32_camera import (
    CameraConnectionError,
    CameraFrameDecodeError,
    CameraStreamFrameError,
)
from app.services.detection.mediapipe_detector import MediaPipeDependencyError
from app.services.metrics.benchmark_service import (
    BenchmarkFileNotFoundError,
    RecognitionBenchmarkService,
)
from app.services.recognition.facenet_recognizer import (
    FaceNetDependencyError,
    KnownFaceIndexError,
)

router = APIRouter()


@router.post("/recognition/run", response_model=RecognitionBenchmarkResult)
def run_recognition_benchmark(
    current_admin: AdminUserPublic = Depends(get_current_admin),
) -> RecognitionBenchmarkResult:
    try:
        return RecognitionBenchmarkService().run_recognition_benchmark()
    except FaceNetDependencyError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except MediaPipeDependencyError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except (CameraConnectionError, CameraStreamFrameError) as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except (CameraFrameDecodeError, KnownFaceIndexError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/benchmarks", response_model=list[BenchmarkFile])
def list_benchmarks(
    current_admin: AdminUserPublic = Depends(get_current_admin),
) -> list[BenchmarkFile]:
    return RecognitionBenchmarkService().list_benchmark_files()


@router.get("/benchmarks/{file_name}")
def download_benchmark(
    file_name: str,
    current_admin: AdminUserPublic = Depends(get_current_admin),
) -> FileResponse:
    try:
        path = RecognitionBenchmarkService().resolve_benchmark_file(file_name)
    except BenchmarkFileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return FileResponse(
        path,
        media_type="text/csv",
        filename=path.name,
    )
