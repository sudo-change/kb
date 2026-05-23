from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from api.deps import get_db

router = APIRouter()

VALID_CATEGORIES = [
    "BugBounty", "AI-Money", "SaaS-Niches",
    "Crypto-DeFi-Alpha", "Attacking-AI", "Tools-Drops", "General",
]


class ItemUpdate(BaseModel):
    category: str | None = None
    score: float | None = None
    tags: list[str] | None = None
    summary: str | None = None


@router.get("/items")
def list_items(
    category: str | None = None,
    source: str | None = None,
    since: str | None = None,
    until: str | None = None,
    q: str | None = None,
    limit: int = 50,
    offset: int = 0,
    db=Depends(get_db),
):
    if category and category not in VALID_CATEGORIES:
        raise HTTPException(
            status_code=400,
            detail={"error": "invalid category", "valid": VALID_CATEGORIES},
        )
    return db.get_items({
        "category": category,
        "source_id": source,
        "since": since,
        "until": until,
        "q": q,
        "limit": min(limit, 500),
        "offset": offset,
    })


@router.get("/items/{item_id}")
def get_item(item_id: int, db=Depends(get_db)):
    item = db.get_item(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="not found")
    return item


@router.patch("/items/{item_id}")
def update_item(item_id: int, body: ItemUpdate, db=Depends(get_db)):
    opts = body.model_dump(exclude_none=True)
    opts["id"] = item_id
    result = db.update_item(opts)
    if not result:
        raise HTTPException(status_code=404, detail="not found")
    return result
