from pathlib import Path
from typing import Protocol

from app.config.settings import settings
from app.models.student import KnownStudent, StudentPhotoReference
from app.services.students.student_repository import StudentRepository


SUPPORTED_PHOTO_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


class StudentPhotoProvider(Protocol):
    source: str

    def list_known_students(self) -> list[KnownStudent]:
        pass


class LocalKnownFacesProvider:
    source = "local_known_faces"

    def __init__(self, root_dir: Path | None = None) -> None:
        self.root_dir = root_dir or settings.known_faces_dir

    def list_known_students(self) -> list[KnownStudent]:
        if not self.root_dir.exists():
            return []

        students: list[KnownStudent] = []

        for student_dir in sorted(path for path in self.root_dir.iterdir() if path.is_dir()):
            photos = self._list_student_photos(student_dir)
            if not photos:
                continue

            student_id, last_name, first_name = self._parse_student_folder(student_dir.name)
            display_name = self._build_display_name(student_id, first_name, last_name)

            students.append(
                KnownStudent(
                    student_id=student_id,
                    first_name=first_name,
                    last_name=last_name,
                    display_name=display_name,
                    photos_count=len(photos),
                    photos=photos,
                    source=self.source,
                )
            )

        return students

    def _list_student_photos(self, student_dir: Path) -> list[StudentPhotoReference]:
        photos: list[StudentPhotoReference] = []

        for photo_path in sorted(path for path in student_dir.iterdir() if path.is_file()):
            if photo_path.suffix.lower() not in SUPPORTED_PHOTO_EXTENSIONS:
                continue

            photos.append(
                StudentPhotoReference(
                    file_name=photo_path.name,
                    source_uri=self._relative_source_uri(photo_path),
                    storage_type="local_file",
                )
            )

        return photos

    def _relative_source_uri(self, photo_path: Path) -> str:
        return photo_path.relative_to(self.root_dir).as_posix()

    def _parse_student_folder(self, folder_name: str) -> tuple[str, str | None, str | None]:
        parts = [part for part in folder_name.split("_") if part]

        if not parts:
            return folder_name, None, None

        student_id = parts[0]
        last_name = parts[1] if len(parts) >= 2 else None
        first_name = " ".join(parts[2:]) if len(parts) >= 3 else None

        return student_id, last_name, first_name

    def _build_display_name(
        self,
        student_id: str,
        first_name: str | None,
        last_name: str | None,
    ) -> str:
        full_name = " ".join(part for part in [first_name, last_name] if part)
        return f"{student_id} - {full_name}" if full_name else student_id


class DatabaseStudentPhotoProvider:
    source = "database_students"

    def __init__(self, repository: StudentRepository | None = None) -> None:
        self.repository = repository or StudentRepository()

    def list_known_students(self) -> list[KnownStudent]:
        rows = self.repository.list_known_students_with_photos()
        students_by_code: dict[str, KnownStudent] = {}

        for row in rows:
            student_code = str(row["student_code"])
            photo = StudentPhotoReference(
                file_name=Path(str(row["source_uri"])).name,
                source_uri=str(row["source_uri"]),
                storage_type=str(row["storage_type"]),
            )

            if student_code not in students_by_code:
                display_name = self._build_display_name(
                    student_code=student_code,
                    first_name=str(row["first_name"]),
                    last_name=str(row["last_name"]),
                )
                students_by_code[student_code] = KnownStudent(
                    student_id=student_code,
                    first_name=str(row["first_name"]),
                    last_name=str(row["last_name"]),
                    display_name=display_name,
                    photos_count=0,
                    photos=[],
                    source=self.source,
                )

            students_by_code[student_code].photos.append(photo)

        students = list(students_by_code.values())
        for student in students:
            student.photos_count = len(student.photos)

        return students

    def _build_display_name(self, student_code: str, first_name: str, last_name: str) -> str:
        return f"{student_code} - {first_name} {last_name}"
