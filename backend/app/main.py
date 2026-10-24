from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.routes import auth, outfits, wardrobe
from app.core.config import settings
from app.db.session import Base, engine, upgrade_clothing_item_columns
from app.models import ClothingItem, User  # noqa: F401


@asynccontextmanager
async def lifespan(_: FastAPI):
    if settings.app_environment.lower() == "production" and not settings.auth_secret:
        raise RuntimeError("AUTH_SECRET must be configured in production.")
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
app.include_router(auth.router, prefix="/api")
app.include_router(wardrobe.router, prefix="/api")
app.include_router(outfits.router, prefix="/api")


@app.get("/api/health", tags=["health"])
def health() -> dict[str, str]:
    return {"status": "ok"}


if settings.frontend_dist_path.is_dir():
    app.mount(
        "/",
        StaticFiles(directory=settings.frontend_dist_path, html=True),
        name="frontend",
    )
