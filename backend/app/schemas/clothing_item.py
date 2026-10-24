from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ClothingItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    category: str
    color: str
    season: str
    occasions: list[str]
    image_url: str
    created_at: datetime


class ClothingItemCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    category: str = Field(pattern="^(top|bottom|shoes|outerwear|accessory)$")
    color: str = Field(min_length=1, max_length=40)
    season: str = Field(default="all", pattern="^(all|spring|summer|autumn|winter)$")
    occasions: list[str] = Field(default_factory=list, max_length=10)
