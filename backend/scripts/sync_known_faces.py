import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.database.service import DatabaseService
from app.models.student import StudentCreate, StudentPhotoCreate
from app.services.students.photo_provider import LocalKnownFacesProvider
from app.services.students.student_service import StudentService


def main() -> None:
    DatabaseService().initialize()

    local_students = LocalKnownFacesProvider().list_known_students()
    service = StudentService()
    created_students = 0
    added_photos = 0

    for student in local_students:
        try:
            service.create_student(
                StudentCreate(
                    student_code=student.student_id,
                    first_name=student.first_name or "Unknown",
                    last_name=student.last_name or "Unknown",
                )
            )
            created_students += 1
        except ValueError:
            pass

        for photo in student.photos:
            try:
                service.add_photo(
                    student.student_id,
                    StudentPhotoCreate(
                        source_uri=photo.source_uri,
                        storage_type="local_file",
                        is_primary=photo.file_name.lower() in {"image_1.jpg", "image_1.jpeg", "image_1.png"},
                    ),
                )
                added_photos += 1
            except ValueError:
                pass

    print(f"Known faces synced: students_created={created_students}, photos_added={added_photos}")


if __name__ == "__main__":
    main()
