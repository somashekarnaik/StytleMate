from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.config import settings
from app.db.session import get_db
from app.image_processing.clothing_analysis import (
    ClothingAnalysisError,
    analyze_clothing,
)
from app.image_processing.processor import InvalidImageError, process_image
from app.models.clothing_item import ClothingItem
from app.models.user import User

router = APIRouter(prefix="/clothing", tags=["wardrobe"])
ALLOWED_CATEGORIES = {"top", "bottom", "shoes", "outerwear", "accessory"}
ALLOWED_STYLES = {
    "western",
    "casual",
    "traditional",
    "formal",
    "sports",
    "winter",
    "summer",
    "party",
    "wedding",
    "loungewear",
    "streetwear",
    "college",
}
ALLOWED_GENDERS = {"men", "women", "unisex"}
ALLOWED_SEASONS = {"all", "spring", "summer", "autumn", "winter"}


def _to_response(item: ClothingItem) -> dict:
    return {
        "id": item.id,
        "name": item.name,
        "category": item.category,
        "style": item.style,
        "gender": item.gender,
        "color": item.color,
        "season": item.season,
        "occasions": item.occasions,
        "image_url": f"/api/clothing/media/{Path(item.image_path).name}",
        "created_at": item.created_at,
    }


@router.get("")
def list_clothing(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[dict]:
    items = db.scalars(
        select(ClothingItem)
        .where(ClothingItem.user_id == user.id)
        .order_by(ClothingItem.created_at.desc())
    ).all()
    return [_to_response(item) for item in items]


@router.get("/media/{filename}")
def get_clothing_image(
    filename: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> FileResponse:
    safe_filename = Path(filename).name
    item = db.scalar(
        select(ClothingItem).where(
            ClothingItem.user_id == user.id,
            ClothingItem.image_path == safe_filename,
        )
    )
    if item is None:
        raise HTTPException(status_code=404, detail="Clothing image not found.")
    return FileResponse(settings.upload_path / safe_filename)


@router.post("", status_code=status.HTTP_201_CREATED)
async def add_clothing(
    name: str = Form("", max_length=100),
    category: str = Form("auto"),
    style: str = Form("auto"),
    gender: str = Form("auto"),
    color: str = Form("", max_length=40),
    season: str = Form("auto"),
    occasions: str = Form(""),
    photo: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    category = category.strip().lower()
    style = style.strip().lower()
    gender = gender.strip().lower()
    season = season.strip().lower()
    if category != "auto" and category not in ALLOWED_CATEGORIES:
        raise HTTPException(status_code=422, detail="Choose a valid clothing category.")
    if style != "auto" and style not in ALLOWED_STYLES:
        raise HTTPException(status_code=422, detail="Choose a supported clothing style.")
    if gender != "auto" and gender not in ALLOWED_GENDERS:
        raise HTTPException(status_code=422, detail="Choose men, women, or unisex.")
    if season != "auto" and season not in ALLOWED_SEASONS:
        raise HTTPException(status_code=422, detail="Choose a valid season.")

    data = await photo.read(settings.max_upload_bytes + 1)
    if len(data) > settings.max_upload_bytes:
        raise HTTPException(status_code=413, detail="Image must be 8 MB or smaller.")
    try:
        processed, detected_color = process_image(data)
    except InvalidImageError as exc:
        raise HTTPException(status_code=415, detail=str(exc)) from exc
    finally:
        await photo.close()

    try:
        analysis = analyze_clothing(processed)
    except ClothingAnalysisError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    filename = f"{uuid4().hex}.webp"
    settings.upload_path.mkdir(parents=True, exist_ok=True)
    (settings.upload_path / filename).write_bytes(processed)
    item = ClothingItem(
        name=name.strip() or analysis["name"],
        category=analysis["category"] if category == "auto" else category,
        style=analysis["style"] if style == "auto" else style,
        gender=analysis["gender"] if gender == "auto" else gender,
        color=color.strip() or analysis["color"] or detected_color,
        season=analysis["season"] if season == "auto" else season,
        occasions=[value.strip() for value in occasions.split(",") if value.strip()],
        image_path=filename,
        user_id=user.id,
    )
    try:
        db.add(item)
        db.commit()
        db.refresh(item)
    except Exception:
        db.rollback()
        (settings.upload_path / filename).unlink(missing_ok=True)
        raise
    return _to_response(item)


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_clothing(
    item_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> None:
    item = db.scalar(
        select(ClothingItem).where(
            ClothingItem.id == item_id,
            ClothingItem.user_id == user.id,
        )
    )
    if item is None:
        raise HTTPException(status_code=404, detail="Clothing item not found.")
    image_path = settings.upload_path / Path(item.image_path).name
    db.delete(item)
    db.commit()
    image_path.unlink(missing_ok=True)
