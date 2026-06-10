from fastapi import APIRouter, Depends, File, HTTPException, Response, UploadFile

from app.api.dependencies import get_current_admin
from app.models.attendance import (
    AttendanceImportResult,
    AttendanceRecognitionResult,
    AttendanceSessionCreate,
    AttendanceSessionDetail,
    AttendanceSessionRead,
)
from app.services.camera.esp32_camera import (
    CameraConnectionError,
    CameraFrameDecodeError,
    CameraStreamFrameError,
)
from app.services.detection.mediapipe_detector import MediaPipeDependencyError
from app.services.recognition.facenet_recognizer import (
    FaceNetDependencyError,
    KnownFaceIndexError,
)
from app.models.auth import AdminUserPublic
from app.services.attendance.attendance_service import (
    AttendanceService,
    AttendanceSessionNotFoundError,
)

router = APIRouter()


@router.post("/sessions", response_model=AttendanceSessionRead, status_code=201)
def create_session(
    payload: AttendanceSessionCreate,
    current_admin: AdminUserPublic = Depends(get_current_admin),
) -> AttendanceSessionRead:
    return AttendanceService().create_session(payload, current_admin.id)


@router.get("/sessions", response_model=list[AttendanceSessionRead])
def list_sessions(
    current_admin: AdminUserPublic = Depends(get_current_admin),
) -> list[AttendanceSessionRead]:
    return AttendanceService().list_sessions()


@router.get("/sessions/{session_id}", response_model=AttendanceSessionDetail)
def get_session(
    session_id: int,
    current_admin: AdminUserPublic = Depends(get_current_admin),
) -> AttendanceSessionDetail:
    try:
        return AttendanceService().get_session_detail(session_id)
    except AttendanceSessionNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/sessions/{session_id}/import", response_model=AttendanceImportResult)
async def import_attendance_sheet(
    session_id: int,
    file: UploadFile = File(...),
    current_admin: AdminUserPublic = Depends(get_current_admin),
) -> AttendanceImportResult:
    if not file.filename.lower().endswith((".xlsx", ".xlsm")):
        raise HTTPException(status_code=400, detail="Only .xlsx or .xlsm files are supported")

    try:
        return AttendanceService().import_attendance_sheet(session_id, await file.read())
    except AttendanceSessionNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/sessions/{session_id}/export")
def export_attendance_sheet(
    session_id: int,
    current_admin: AdminUserPublic = Depends(get_current_admin),
) -> Response:
    try:
        file_name, file_bytes = AttendanceService().export_session(session_id)
    except AttendanceSessionNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return Response(
        content=file_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{file_name}"'},
    )


@router.post("/sessions/{session_id}/recognize", response_model=AttendanceRecognitionResult)
def recognize_attendance(
    session_id: int,
    current_admin: AdminUserPublic = Depends(get_current_admin),
) -> AttendanceRecognitionResult:
    try:
        return AttendanceService().recognize_attendance(session_id)
    except AttendanceSessionNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except FaceNetDependencyError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except MediaPipeDependencyError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except (CameraConnectionError, CameraStreamFrameError) as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except (CameraFrameDecodeError, KnownFaceIndexError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
