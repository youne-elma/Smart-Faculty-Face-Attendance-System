from fastapi import APIRouter

from app.models.student import KnownStudentsResult
from app.services.students.student_service import StudentService

router = APIRouter()


@router.get("/known", response_model=KnownStudentsResult)
def list_known_students() -> KnownStudentsResult:
    service = StudentService()
    return service.list_known_students()
