from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import get_current_admin
from app.models.auth import AdminUserPublic
from app.models.student import (
    KnownStudentsResult,
    StudentCreate,
    StudentPhotoCreate,
    StudentPhotoRead,
    StudentRead,
)
from app.services.students.student_service import StudentNotFoundError, StudentService

router = APIRouter()


@router.get("/known", response_model=KnownStudentsResult)
def list_known_students() -> KnownStudentsResult:
    service = StudentService()
    return service.list_known_students()


@router.get("", response_model=list[StudentRead])
def list_students(
    current_admin: AdminUserPublic = Depends(get_current_admin),
) -> list[StudentRead]:
    return StudentService().list_students()


@router.post("", response_model=StudentRead, status_code=201)
def create_student(
    payload: StudentCreate,
    current_admin: AdminUserPublic = Depends(get_current_admin),
) -> StudentRead:
    try:
        return StudentService().create_student(payload)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get("/{student_code}", response_model=StudentRead)
def get_student(
    student_code: str,
    current_admin: AdminUserPublic = Depends(get_current_admin),
) -> StudentRead:
    try:
        return StudentService().get_student(student_code)
    except StudentNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/{student_code}/photos", response_model=StudentPhotoRead, status_code=201)
def add_student_photo(
    student_code: str,
    payload: StudentPhotoCreate,
    current_admin: AdminUserPublic = Depends(get_current_admin),
) -> StudentPhotoRead:
    try:
        return StudentService().add_photo(student_code, payload)
    except StudentNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
