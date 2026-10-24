from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class ClothingItem(Base):
    __tablename__ = "clothing_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    category: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    style: Mapped[str] = mapped_column(String(20), default="casual", nullable=False, index=True)
    gender: Mapped[str] = mapped_column(String(20), default="unisex", nullable=False, index=True)
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), nullable=True, index=True
    )
    color: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    season: Mapped[str] = mapped_column(String(20), default="all", nullable=False)
    occasions: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    image_path: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
