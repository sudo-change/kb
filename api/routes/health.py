from __future__ import annotations

from fastapi import APIRouter, Depends

from api.deps import get_db

router = APIRouter()


@router.get("/health")
def health(db=Depends(get_db)):
    info = db.get_health()
    return {
        "status": "ok",
        "last_run": info.last_run.isoformat() if info.last_run else None,
        "items_today": info.items_today,
        "errors": info.errors,
    }
