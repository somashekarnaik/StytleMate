from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.db.session import get_db
from app.core.config import settings
from app.image_processing.outfit_preview import create_outfit_preview
from app.models.clothing_item import ClothingItem
from app.models.user import User
from app.recommendation.engine import recommend_outfits

router = APIRouter(prefix="/outfits", tags=["outfits"])
STYLE_FILTER = (
    "western|casual|traditional|formal|sports|winter|summer|party|wedding|"
    "loungewear|streetwear|college"
)


@router.get("/recommendations")
def get_recommendations(
    weather: str | None = Query(default=None, pattern="^(hot|mild|cold|rainy)$"),
    occasion: str | None = Query(default=None, max_length=40),
    color: str | None = Query(default=None, max_length=40),
    style: str | None = Query(default=None, pattern=f"^({STYLE_FILTER})$"),
    gender: str | None = Query(default=None, pattern="^(men|women)$"),
    limit: int = Query(default=6, ge=1, le=20),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    items = db.scalars(
        select(ClothingItem).where(ClothingItem.user_id == user.id)
    ).all()
    recommendations = recommend_outfits(
        list(items),
        weather=weather,
        occasion=occasion,
        preferred_color=color,
        style=style,
        gender=gender,
        limit=limit,
    )
    for recommendation in recommendations:
        preview_items = [
            next(item for item in items if item.id == entry["id"])
            for entry in recommendation["items"]
        ]
        item_ids = "&".join(f"item_ids={item.id}" for item in preview_items)
        recommendation["preview_url"] = f"/api/outfits/preview?{item_ids}"
    missing_categories = [
        category
        for category in ("top", "bottom", "shoes")
        if not any(item.category == category for item in items)
    ]
    if missing_categories:
        category_labels = {
            "top": "a top",
            "bottom": "a bottom",
            "shoes": "a pair of shoes",
        }
        missing = [category_labels[category] for category in missing_categories]
        if len(missing) == 1:
            missing_text = missing[0]
        elif len(missing) == 2:
            missing_text = " and ".join(missing)
        else:
            missing_text = f"{', '.join(missing[:-1])}, and {missing[-1]}"
        if recommendations:
            message = f"Your outfit idea is ready. Add {missing_text} to complete the look."
        else:
            message = f"Add {missing_text} to your wardrobe to get a complete outfit."
    elif not recommendations:
        message = (
            "No complete outfits match these filters. Try another weather, "
            "occasion, style, or audience filter."
        )
    else:
        message = None

    return {"recommendations": recommendations, "message": message}


@router.get("/preview")
def get_outfit_preview(
    item_ids: list[int] = Query(..., min_length=1, max_length=3),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> FileResponse:
    if len(set(item_ids)) != len(item_ids):
        raise HTTPException(status_code=422, detail="Outfit items must be unique.")
    items = db.scalars(
        select(ClothingItem).where(
            ClothingItem.user_id == user.id,
            ClothingItem.id.in_(item_ids),
        )
    ).all()
    if len(items) != len(item_ids):
        raise HTTPException(status_code=404, detail="Outfit items not found.")
    ordered_items = {item.id: item for item in items}
    preview_url = create_outfit_preview(
        [
            {"id": item_id, "image_path": ordered_items[item_id].image_path}
            for item_id in item_ids
        ],
        settings.upload_path,
    )
    preview_path = settings.upload_path / preview_url.removeprefix("/media/")
    return FileResponse(preview_path)
