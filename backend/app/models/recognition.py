from pydantic import BaseModel, Field

from app.models.face import FaceBox


class RecognitionMatch(BaseModel):
    student_id: str
    display_name: str
    score: float = Field(ge=-1.0, le=1.0)


class RecognizedFace(BaseModel):
    box: FaceBox
    recognized: bool
    best_match: RecognitionMatch | None = None


class FaceRecognitionResult(BaseModel):
    detector: str
    recognizer: str
    threshold: float
    known_embeddings_count: int
    faces_count: int
    faces: list[RecognizedFace]
