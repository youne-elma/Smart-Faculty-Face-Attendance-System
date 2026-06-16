import csv
from datetime import datetime
from pathlib import Path
from time import perf_counter

from app.config.settings import settings
from app.models.metrics import BenchmarkFile, RecognitionBenchmarkResult
from app.services.camera.esp32_camera import Esp32CameraClient
from app.services.detection.mediapipe_detector import get_mediapipe_face_detector
from app.services.recognition.facenet_recognizer import get_facenet_recognizer


class BenchmarkFileNotFoundError(RuntimeError):
    pass


class RecognitionBenchmarkService:
    fieldnames = [
        "timestamp",
        "detector",
        "recognizer",
        "capture_ms",
        "detection_ms",
        "recognition_ms",
        "total_ms",
        "faces_count",
        "known_embeddings_count",
        "best_student",
        "best_score",
        "recognized",
        "threshold",
    ]

    def run_recognition_benchmark(self) -> RecognitionBenchmarkResult:
        detector = get_mediapipe_face_detector()
        recognizer = get_facenet_recognizer()

        total_start = perf_counter()

        capture_start = perf_counter()
        frame = Esp32CameraClient().fetch_frame()
        capture_ms = self._elapsed_ms(capture_start)

        detection_start = perf_counter()
        faces = detector.detect(frame)
        detection_ms = self._elapsed_ms(detection_start)

        recognition_start = perf_counter()
        known_embeddings = recognizer.build_known_index()
        best_match = None
        if faces and known_embeddings:
            face = max(faces, key=lambda item: item.width * item.height)
            best_match = recognizer.find_best_match(frame, face, known_embeddings)
        recognition_ms = self._elapsed_ms(recognition_start)

        total_ms = self._elapsed_ms(total_start)
        timestamp = datetime.now().isoformat(timespec="seconds")
        recognized = bool(best_match and best_match.score >= recognizer.threshold)

        row = {
            "timestamp": timestamp,
            "detector": detector.name,
            "recognizer": recognizer.name,
            "capture_ms": round(capture_ms, 3),
            "detection_ms": round(detection_ms, 3),
            "recognition_ms": round(recognition_ms, 3),
            "total_ms": round(total_ms, 3),
            "faces_count": len(faces),
            "known_embeddings_count": len(known_embeddings),
            "best_student": best_match.display_name if best_match else "",
            "best_score": round(best_match.score, 6) if best_match else "",
            "recognized": recognized,
            "threshold": recognizer.threshold,
        }

        file_name = self._append_row(row)

        return RecognitionBenchmarkResult(
            file_name=file_name,
            timestamp=timestamp,
            detector=detector.name,
            recognizer=recognizer.name,
            capture_ms=row["capture_ms"],
            detection_ms=row["detection_ms"],
            recognition_ms=row["recognition_ms"],
            total_ms=row["total_ms"],
            faces_count=len(faces),
            known_embeddings_count=len(known_embeddings),
            best_student=best_match.display_name if best_match else None,
            best_score=best_match.score if best_match else None,
            recognized=recognized,
            threshold=recognizer.threshold,
        )

    def list_benchmark_files(self) -> list[BenchmarkFile]:
        self._ensure_dir()
        files = []

        for path in sorted(settings.benchmarks_dir.glob("*.csv"), reverse=True):
            stat = path.stat()
            files.append(
                BenchmarkFile(
                    file_name=path.name,
                    size_bytes=stat.st_size,
                    modified_at=datetime.fromtimestamp(stat.st_mtime).isoformat(timespec="seconds"),
                )
            )

        return files

    def resolve_benchmark_file(self, file_name: str) -> Path:
        self._ensure_dir()
        path = settings.benchmarks_dir / Path(file_name).name

        if not path.exists() or path.suffix.lower() != ".csv":
            raise BenchmarkFileNotFoundError(f"Benchmark file not found: {file_name}")

        return path

    def _append_row(self, row: dict[str, object]) -> str:
        self._ensure_dir()
        file_name = f"recognition_benchmark_{datetime.now().strftime('%Y%m%d')}.csv"
        path = settings.benchmarks_dir / file_name
        write_header = not path.exists()

        with path.open("a", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=self.fieldnames)
            if write_header:
                writer.writeheader()
            writer.writerow(row)

        return file_name

    def _ensure_dir(self) -> None:
        settings.benchmarks_dir.mkdir(parents=True, exist_ok=True)

    def _elapsed_ms(self, started_at: float) -> float:
        return (perf_counter() - started_at) * 1000
