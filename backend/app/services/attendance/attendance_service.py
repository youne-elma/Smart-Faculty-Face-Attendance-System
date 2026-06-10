from app.models.attendance import (
    AttendanceImportResult,
    AttendanceRecordRead,
    AttendanceRecognitionResult,
    AttendanceSessionCreate,
    AttendanceSessionDetail,
    AttendanceSessionRead,
)
from app.services.camera.esp32_camera import Esp32CameraClient
from app.services.attendance.attendance_repository import AttendanceRepository
from app.services.attendance.excel_io import AttendanceExcelReader, AttendanceExcelWriter
from app.services.detection.mediapipe_detector import get_mediapipe_face_detector
from app.services.recognition.facenet_recognizer import get_facenet_recognizer


class AttendanceSessionNotFoundError(RuntimeError):
    pass


class AttendanceService:
    def __init__(self, repository: AttendanceRepository | None = None) -> None:
        self.repository = repository or AttendanceRepository()

    def create_session(
        self,
        payload: AttendanceSessionCreate,
        admin_user_id: int,
    ) -> AttendanceSessionRead:
        return self._to_session_read(self.repository.create_session(payload, admin_user_id))

    def list_sessions(self) -> list[AttendanceSessionRead]:
        return [self._to_session_read(row) for row in self.repository.list_sessions()]

    def get_session_detail(self, session_id: int) -> AttendanceSessionDetail:
        session = self.repository.get_session(session_id)
        if session is None:
            raise AttendanceSessionNotFoundError(f"Attendance session not found: {session_id}")

        records = [self._to_record_read(row) for row in self.repository.list_records(session_id)]
        return AttendanceSessionDetail(
            **self._to_session_read(session).model_dump(),
            records=records,
        )

    def import_attendance_sheet(
        self,
        session_id: int,
        file_bytes: bytes,
    ) -> AttendanceImportResult:
        if self.repository.get_session(session_id) is None:
            raise AttendanceSessionNotFoundError(f"Attendance session not found: {session_id}")

        rows, skipped_rows = AttendanceExcelReader().read_students(file_bytes)
        created_students = 0
        attendance_records = 0

        for row in rows:
            student, created = self.repository.get_or_create_student(
                student_code=row.student_code,
                first_name=row.first_name,
                last_name=row.last_name,
                group_name=row.group_name,
                email=row.email,
            )
            if created:
                created_students += 1

            self.repository.ensure_absent_record(session_id, int(student["id"]))
            attendance_records += 1

        return AttendanceImportResult(
            session_id=session_id,
            imported_students=len(rows),
            created_students=created_students,
            attendance_records=attendance_records,
            skipped_rows=skipped_rows,
        )

    def export_session(self, session_id: int) -> tuple[str, bytes]:
        detail = self.get_session_detail(session_id)
        file_name = f"attendance_session_{session_id}.xlsx"
        file_bytes = AttendanceExcelWriter().write_session_export(detail, detail.records)
        return file_name, file_bytes

    def recognize_attendance(self, session_id: int) -> AttendanceRecognitionResult:
        if self.repository.get_session(session_id) is None:
            raise AttendanceSessionNotFoundError(f"Attendance session not found: {session_id}")

        frame = Esp32CameraClient().fetch_frame()
        detector = get_mediapipe_face_detector()
        recognizer = get_facenet_recognizer()

        faces = detector.detect(frame)
        if not faces:
            return AttendanceRecognitionResult(
                session_id=session_id,
                faces_count=0,
                recognized=False,
                message="No face detected",
            )

        known_embeddings = recognizer.build_known_index()
        face = max(faces, key=lambda item: item.width * item.height)
        match = recognizer.find_best_match(frame, face, known_embeddings)

        if match is None:
            return AttendanceRecognitionResult(
                session_id=session_id,
                faces_count=len(faces),
                recognized=False,
                message="No known face match found",
            )

        if match.score < recognizer.threshold:
            return AttendanceRecognitionResult(
                session_id=session_id,
                faces_count=len(faces),
                recognized=False,
                student_code=match.student_id,
                display_name=match.display_name,
                score=match.score,
                message="Best match score is below threshold",
            )

        record = self.repository.mark_present(session_id, match.student_id, match.score)
        if record is None:
            return AttendanceRecognitionResult(
                session_id=session_id,
                faces_count=len(faces),
                recognized=True,
                student_code=match.student_id,
                display_name=match.display_name,
                score=match.score,
                message="Student recognized but not found in this attendance session",
            )

        return AttendanceRecognitionResult(
            session_id=session_id,
            faces_count=len(faces),
            recognized=True,
            student_code=match.student_id,
            display_name=match.display_name,
            score=match.score,
            status=str(record["status"]),
            message="Attendance marked as present",
        )

    def _to_session_read(self, row) -> AttendanceSessionRead:
        return AttendanceSessionRead(
            id=int(row["id"]),
            admin_user_id=row["admin_user_id"],
            title=str(row["title"]),
            session_type=str(row["session_type"]),
            course_name=row["course_name"],
            group_name=row["group_name"],
            starts_at=row["starts_at"],
            ends_at=row["ends_at"],
            created_at=str(row["created_at"]),
        )

    def _to_record_read(self, row) -> AttendanceRecordRead:
        return AttendanceRecordRead(
            id=int(row["id"]),
            session_id=int(row["session_id"]),
            student_id=int(row["student_id"]),
            student_code=str(row["student_code"]),
            first_name=str(row["first_name"]),
            last_name=str(row["last_name"]),
            group_name=row["group_name"],
            status=str(row["status"]),
            recognized_at=row["recognized_at"],
            recognition_score=row["recognition_score"],
        )
