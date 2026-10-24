from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.routes import outfits, wardrobe
from app.core.config import settings
from app.db.session import Base, engine, upgrade_clothing_item_columns
from app.models import ClothingItem  # noqa: F401


@asynccontextmanager
async def lifespan(_: FastAPI):
    settings.upload_path.mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(bind=engine)
    upgrade_clothing_item_columns()
    yield


app = FastAPI(title="StyleMate API", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/media", StaticFiles(directory=settings.upload_path, check_dir=False), name="media")
app.include_router(wardrobe.router, prefix="/api")
app.include_router(outfits.router, prefix="/api")


@app.get("/api/health", tags=["health"])
def health() -> dict[str, str]:
    return {"status": "ok"}
