from pydantic import BaseModel, Field


class StudentPhotoReference(BaseModel):
    file_name: str
    source_uri: str


class KnownStudent(BaseModel):
    student_id: str = Field(min_length=1)
    first_name: str | None = None
    last_name: str | None = None
    display_name: str
    photos_count: int = Field(ge=0)
    photos: list[StudentPhotoReference] = Field(default_factory=list)
    source: str


class KnownStudentsResult(BaseModel):
    source: str
    students_count: int
    total_photos: int
    students: list[KnownStudent]
