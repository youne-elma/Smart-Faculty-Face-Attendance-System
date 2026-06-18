import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.database.service import DatabaseService
from app.services.recognition.embedding_service import FaceEmbeddingService


def main() -> None:
    DatabaseService().initialize()
    result = FaceEmbeddingService().rebuild_embeddings()
    print(result.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
