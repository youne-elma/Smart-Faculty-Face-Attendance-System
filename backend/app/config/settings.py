from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parents[3]
BACKEND_DIR = BASE_DIR / "backend"


class Settings(BaseSettings):
    app_name: str = "Smart Faculty Face Attendance System"
    app_env: str = "development"
    api_prefix: str = "/api/v1"

    esp32_cam_url: str = "http://192.168.1.30/"
    esp32_cam_snapshot_path: str = "/capture"
    esp32_cam_stream_url: str = "http://192.168.1.30:81/stream"
    camera_timeout_seconds: int = 5
    camera_stream_read_bytes: int = 65_536

    facenet_pretrained_model: str = "vggface2"
    face_recognition_threshold: float = 0.7
    mediapipe_face_min_confidence: float = 0.6
    mediapipe_face_model_path: Path = Field(
        default=BASE_DIR / "backend/data/models/blaze_face_short_range.tflite"
    )

    admin_username: str = "admin"
    admin_password: str = "admin1234"
    secret_key: str = "ait-melloul"
    access_token_expire_minutes: int = 480

    database_path: Path = Field(default=BASE_DIR / "backend/data/db/attendance.sqlite3")
    imports_dir: Path = Field(default=BASE_DIR / "backend/data/imports")
    exports_dir: Path = Field(default=BASE_DIR / "backend/data/exports")
    known_faces_dir: Path = Field(default=BASE_DIR / "backend/data/known_faces")
    models_dir: Path = Field(default=BASE_DIR / "backend/data/models")
    benchmarks_dir: Path = Field(default=BASE_DIR / "backend/data/benchmarks")

    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]

    @model_validator(mode="after")
    def resolve_relative_paths(self) -> "Settings":
        self.database_path = self._resolve_backend_path(self.database_path)
        self.imports_dir = self._resolve_backend_path(self.imports_dir)
        self.exports_dir = self._resolve_backend_path(self.exports_dir)
        self.known_faces_dir = self._resolve_backend_path(self.known_faces_dir)
        self.models_dir = self._resolve_backend_path(self.models_dir)
        self.benchmarks_dir = self._resolve_backend_path(self.benchmarks_dir)
        self.mediapipe_face_model_path = self._resolve_backend_path(
            self.mediapipe_face_model_path
        )
        return self

    def _resolve_backend_path(self, path: Path) -> Path:
        if path.is_absolute():
            return path

        if path.parts and path.parts[0] == "backend":
            return BASE_DIR / path

        return BACKEND_DIR / path

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / "backend/.env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
