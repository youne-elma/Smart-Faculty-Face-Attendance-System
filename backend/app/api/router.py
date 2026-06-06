from fastapi import APIRouter

from app.api.routes import camera, detection, health, recognition, students

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(camera.router, prefix="/camera", tags=["camera"])
api_router.include_router(detection.router, prefix="/detection", tags=["detection"])
api_router.include_router(recognition.router, prefix="/recognition", tags=["recognition"])
api_router.include_router(students.router, prefix="/students", tags=["students"])
