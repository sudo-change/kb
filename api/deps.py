from __future__ import annotations
from core.database import DB

_db: DB | None = None


def get_db() -> DB:
    assert _db is not None, "DB not initialised — did lifespan run?"
    return _db


def init_db(path: str) -> DB:
    global _db
    _db = DB(path)
    return _db


def close_db() -> None:
    global _db
    if _db:
        _db.close()
        _db = None
