from app.models.student import (
    KnownStudentsResult,
    StudentCreate,
    StudentPhotoCreate,
    StudentPhotoRead,
    StudentRead,
)
from app.services.students.photo_provider import (
    DatabaseStudentPhotoProvider,
    LocalKnownFacesProvider,
    StudentPhotoProvider,
)
from app.services.students.student_repository import StudentRepository


class StudentNotFoundError(RuntimeError):
    pass


class StudentService:
    def __init__(
        self,
        photo_provider: StudentPhotoProvider | None = None,
        repository: StudentRepository | None = None,
    ) -> None:
        self.repository = repository or StudentRepository()
        self.photo_provider = photo_provider or DatabaseStudentPhotoProvider(self.repository)

    def list_known_students(self) -> KnownStudentsResult:
        students = self.photo_provider.list_known_students()
        source = self.photo_provider.source

        if not students:
            fallback_provider = LocalKnownFacesProvider()
            students = fallback_provider.list_known_students()
            source = fallback_provider.source

        total_photos = sum(student.photos_count for student in students)

        return KnownStudentsResult(
            source=source,
            students_count=len(students),
            total_photos=total_photos,
            students=students,
        )

    def list_students(self) -> list[StudentRead]:
        return [self._to_student_read(row) for row in self.repository.list_students()]

    def get_student(self, student_code: str) -> StudentRead:
        row = self.repository.get_by_code(student_code)
        if row is None:
            raise StudentNotFoundError(f"Student not found: {student_code}")

        return self._to_student_read(row)

    def create_student(self, payload: StudentCreate) -> StudentRead:
        return self._to_student_read(self.repository.create_student(payload))

    def add_photo(self, student_code: str, payload: StudentPhotoCreate) -> StudentPhotoRead:
        student = self.repository.get_by_code(student_code)
        if student is None:
            raise StudentNotFoundError(f"Student not found: {student_code}")

        return self._to_photo_read(self.repository.add_photo(int(student["id"]), payload))

    def _to_student_read(self, row) -> StudentRead:
        return StudentRead(
            id=int(row["id"]),
            student_code=str(row["student_code"]),
            first_name=str(row["first_name"]),
            last_name=str(row["last_name"]),
            group_name=row["group_name"],
            email=row["email"],
            is_active=bool(row["is_active"]),
        )

    def _to_photo_read(self, row) -> StudentPhotoRead:
        return StudentPhotoRead(
            id=int(row["id"]),
            student_id=int(row["student_id"]),
            source_uri=str(row["source_uri"]),
            storage_type=str(row["storage_type"]),
            is_primary=bool(row["is_primary"]),
        )
