from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api import deps
from api.routes import items, sources, health


@asynccontextmanager
async def lifespan(app: FastAPI):
    deps.init_db("data/kf.db")
    yield
    deps.close_db()


app = FastAPI(title="KnowledgeForge API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(items.router)
app.include_router(sources.router)
app.include_router(health.router)
