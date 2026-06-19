from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import get_current_admin
from app.models.auth import AdminUserPublic
from app.models.embedding import EmbeddingBuildResult, EmbeddingStats
from app.services.detection.mediapipe_detector import MediaPipeDependencyError
from app.services.recognition.embedding_service import FaceEmbeddingService
from app.services.recognition.facenet_recognizer import FaceNetDependencyError

router = APIRouter()


@router.post("/rebuild", response_model=EmbeddingBuildResult)
def rebuild_embeddings(
    current_admin: AdminUserPublic = Depends(get_current_admin),
) -> EmbeddingBuildResult:
    try:
        return FaceEmbeddingService().rebuild_embeddings()
    except FaceNetDependencyError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except MediaPipeDependencyError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.get("/stats", response_model=EmbeddingStats)
def embedding_stats(
    current_admin: AdminUserPublic = Depends(get_current_admin),
) -> EmbeddingStats:
    try:
        return FaceEmbeddingService().stats()
    except FaceNetDependencyError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
