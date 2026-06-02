from fastapi import APIRouter

from app.api.routes import camera, detection, health

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(camera.router, prefix="/camera", tags=["camera"])
api_router.include_router(detection.router, prefix="/detection", tags=["detection"])
