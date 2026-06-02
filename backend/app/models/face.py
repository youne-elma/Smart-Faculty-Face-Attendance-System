from pydantic import BaseModel, Field


class FaceBox(BaseModel):
    x: int = Field(ge=0)
    y: int = Field(ge=0)
    width: int = Field(gt=0)
    height: int = Field(gt=0)


class FaceDetectionResult(BaseModel):
    detector: str
    faces_count: int
    faces: list[FaceBox]
