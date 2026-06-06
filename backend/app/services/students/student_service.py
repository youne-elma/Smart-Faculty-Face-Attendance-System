from app.models.student import KnownStudentsResult
from app.services.students.photo_provider import LocalKnownFacesProvider, StudentPhotoProvider


class StudentService:
    def __init__(self, photo_provider: StudentPhotoProvider | None = None) -> None:
        self.photo_provider = photo_provider or LocalKnownFacesProvider()

    def list_known_students(self) -> KnownStudentsResult:
        students = self.photo_provider.list_known_students()
        total_photos = sum(student.photos_count for student in students)

        return KnownStudentsResult(
            source=self.photo_provider.source,
            students_count=len(students),
            total_photos=total_photos,
            students=students,
        )
