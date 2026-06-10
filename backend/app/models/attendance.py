from datetime import datetime

from pydantic import BaseModel, Field


class AttendanceSessionCreate(BaseModel):
    title: str = Field(min_length=1)
    session_type: str = Field(min_length=1)
    course_name: str | None = None
    group_name: str | None = None
    starts_at: datetime | None = None
    ends_at: datetime | None = None


class AttendanceSessionRead(BaseModel):
    id: int
    admin_user_id: int | None = None
    title: str
    session_type: str
    course_name: str | None = None
    group_name: str | None = None
    starts_at: str | None = None
    ends_at: str | None = None
    created_at: str


class AttendanceRecordRead(BaseModel):
    id: int
    session_id: int
    student_id: int
    student_code: str
    first_name: str
    last_name: str
    group_name: str | None = None
    status: str
    recognized_at: str | None = None
    recognition_score: float | None = None


class AttendanceSessionDetail(AttendanceSessionRead):
    records: list[AttendanceRecordRead] = Field(default_factory=list)


class AttendanceImportResult(BaseModel):
    session_id: int
    imported_students: int
    created_students: int
    attendance_records: int
    skipped_rows: int


class AttendanceExportResult(BaseModel):
    session_id: int
    file_name: str


class AttendanceRecognitionResult(BaseModel):
    session_id: int
    faces_count: int
    recognized: bool
    student_code: str | None = None
    display_name: str | None = None
    score: float | None = None
    status: str | None = None
    message: str
