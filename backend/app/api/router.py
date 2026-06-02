from fastapi import APIRouter

from app.api.routes import camera, health

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(camera.router, prefix="/camera", tags=["camera"])
