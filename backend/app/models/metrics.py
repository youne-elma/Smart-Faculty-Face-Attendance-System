from pydantic import BaseModel


class RecognitionBenchmarkResult(BaseModel):
    file_name: str
    timestamp: str
    detector: str
    recognizer: str
    capture_ms: float
    detection_ms: float
    recognition_ms: float
    total_ms: float
    faces_count: int
    known_embeddings_count: int
    best_student: str | None = None
    best_score: float | None = None
    recognized: bool
    threshold: float


class BenchmarkFile(BaseModel):
    file_name: str
    size_bytes: int
    modified_at: str
