from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel

from api.deps import get_db
from core.models import Source

router = APIRouter()


class SourceCreate(BaseModel):
    id: str
    name: str
    type: str
    config: dict = {}
    glyph: str = ""
    category: str | None = None
    enabled: bool = True


@router.get("/sources")
def list_sources(db=Depends(get_db)):
    return db.get_sources()


@router.post("/sources", status_code=201)
def add_source(body: SourceCreate, db=Depends(get_db)):
    source = Source(
        id=body.id,
        name=body.name,
        type=body.type,
        config=body.config,
        glyph=body.glyph,
        category=body.category,
        enabled=body.enabled,
    )
    return db.add_source(source)


@router.delete("/sources/{source_id}", status_code=204)
def delete_source(source_id: str, db=Depends(get_db)):
    db.remove_source(source_id)
    return Response(status_code=204)
