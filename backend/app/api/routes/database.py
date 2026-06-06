from fastapi import APIRouter

from app.database.service import DatabaseService

router = APIRouter()


@router.get("/status")
def database_status() -> dict[str, object]:
    service = DatabaseService()
    return service.status()


@router.post("/initialize")
def initialize_database() -> dict[str, object]:
    service = DatabaseService()
    return service.initialize()
