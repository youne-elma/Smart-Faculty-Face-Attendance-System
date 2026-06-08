from pydantic import BaseModel, Field


class StudentPhotoReference(BaseModel):
    file_name: str
    source_uri: str
    storage_type: str = "database_reference"


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


class StudentCreate(BaseModel):
    student_code: str = Field(min_length=1)
    first_name: str = Field(min_length=1)
    last_name: str = Field(min_length=1)
    group_name: str | None = None
    email: str | None = None


class StudentRead(BaseModel):
    id: int
    student_code: str
    first_name: str
    last_name: str
    group_name: str | None = None
    email: str | None = None
    is_active: bool


class StudentPhotoCreate(BaseModel):
    source_uri: str = Field(min_length=1)
    storage_type: str = "database_reference"
    is_primary: bool = False


class StudentPhotoRead(BaseModel):
    id: int
    student_id: int
    source_uri: str
    storage_type: str
    is_primary: bool
