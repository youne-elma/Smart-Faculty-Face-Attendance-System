import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from app.config.settings import BASE_DIR, settings


def resolve_database_path() -> Path:
    database_path = settings.database_path

    if database_path.is_absolute():
        return database_path

    return BASE_DIR / database_path


@contextmanager
def get_connection() -> Iterator[sqlite3.Connection]:
    database_path = resolve_database_path()
    database_path.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON;")

    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()
