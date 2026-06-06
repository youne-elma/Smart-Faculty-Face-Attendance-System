import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.database.service import DatabaseService


def main() -> None:
    status = DatabaseService().initialize()
    print(f"Database initialized: {status['database_path']}")
    print(f"Tables: {', '.join(status['tables'])}")


if __name__ == "__main__":
    main()
