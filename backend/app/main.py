from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import anki as anki_api
from app.api import songs as songs_api
from app.config import get_settings
from app.db import init_db
from app.services.ingestion import sweep_orphans


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    sweep_orphans()
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="LLMP", version="0.1.0", lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(songs_api.router, prefix="/api")
    app.include_router(anki_api.router, prefix="/api")

    @app.get("/api/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
