from pydantic import BaseModel


class EmbeddingBuildResult(BaseModel):
    model_name: str
    photos_processed: int
    embeddings_created: int
    skipped_photos: int


class EmbeddingStats(BaseModel):
    model_name: str
    embeddings_count: int
    students_count: int
