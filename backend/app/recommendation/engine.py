from itertools import product
import colorsys
import re

from PIL import ImageColor

from app.models.clothing_item import ClothingItem

CATEGORIES = ("top", "bottom", "shoes")
WEATHER_SEASONS = {
    "hot": {"summer", "spring", "all"},
    "mild": {"spring", "autumn", "all"},
    "cold": {"winter", "autumn", "all"},
    "rainy": {"spring", "autumn", "winter", "all"},
}
NEUTRAL_COLORS = {
    "black", "white", "gray", "grey", "navy", "beige", "brown", "cream"
}


def recommend_outfits(
    items: list[ClothingItem],
    weather: str | None = None,
    occasion: str | None = None,
    preferred_color: str | None = None,
    style: str | None = None,
    gender: str | None = None,
    limit: int = 6,
) -> list[dict]:
    grouped = {category: [] for category in CATEGORIES}
    for item in items:
        if item.category in grouped and _fits_filters(item, weather, occasion, style, gender):
            grouped[item.category].append(item)

    available_categories = [category for category in CATEGORIES if grouped[category]]
    if not available_categories or not any(
        grouped[category] for category in ("top", "bottom")
    ):
        return []

    ranked = []
    for combo in product(*(grouped[category] for category in available_categories)):
        score = _color_score(combo, preferred_color)
        ranked.append(
            {
                "items": [
                    {
                        "id": item.id,
                        "name": item.name,
                        "category": item.category,
                        "style": item.style,
                        "gender": item.gender,
                        "color": item.color,
                        "image_url": f"/media/{item.image_path}",
                    }
                    for item in combo
                ],
                "missing_categories": [
                    category for category in CATEGORIES if not grouped[category]
                ],
                "score": score,
                "reason": _explanation(
                    combo,
                    weather,
                    occasion,
                    preferred_color,
                    style,
                    gender,
                    [category for category in CATEGORIES if not grouped[category]],
                ),
            }
        )
    ranked.sort(key=lambda outfit: (-outfit["score"], tuple(i["id"] for i in outfit["items"])))
    return ranked[:limit]


def _fits_filters(
    item: ClothingItem,
    weather: str | None,
    occasion: str | None,
    style: str | None,
    gender: str | None,
) -> bool:
    if weather:
        seasons = WEATHER_SEASONS.get(weather)
        if seasons and item.season not in seasons:
            return False
    if occasion and item.occasions and occasion.lower() not in {o.lower() for o in item.occasions}:
        return False
    if style and item.style != style:
        return False
    if gender and item.gender not in {gender, "unisex"}:
        return False
    return True


def _color_score(items: tuple[ClothingItem, ...], preferred_color: str | None) -> int:
    colors = [item.color.strip().lower() for item in items]
    score = 65
    if preferred_color and any(preferred_color.lower() in color for color in colors):
        score += 25
    score += _color_harmony(colors)
    if len({item.style for item in items}) == 1:
        score += 12
    else:
        score -= 10
    if len({item.gender for item in items}) == 1 or all(
        item.gender == "unisex" for item in items
    ):
        score += 5
    return min(score, 100)


def _color_harmony(colors: list[str]) -> int:
    hues = [hue for color in colors if (hue := _color_hue(color)) is not None]
    if len(hues) < 2:
        if all(
            color in NEUTRAL_COLORS
            or (color.startswith("#") and _color_hue(color) is None)
            for color in colors
        ):
            return 5
        return 0
    distances = [
        min(abs(hues[left] - hues[right]), 360 - abs(hues[left] - hues[right]))
        for left in range(len(hues))
        for right in range(left + 1, len(hues))
    ]
    if all(distance <= 35 for distance in distances):
        return 12
    if any(145 <= distance <= 180 for distance in distances):
        return 14
    if all(80 <= distance <= 140 for distance in distances):
        return 8
    if all(distance <= 55 for distance in distances):
        return 6
    return -8


def _color_hue(color: str) -> float | None:
    if color in NEUTRAL_COLORS:
        return None
    aliases = {"cream": "#fffdd0", "beige": "#f5f5dc", "grey": "#808080"}
    value = aliases.get(color, color)
    if not re.fullmatch(r"#[0-9a-f]{6}", value):
        try:
            red, green, blue = ImageColor.getrgb(value)[:3]
        except ValueError:
            return None
    else:
        red, green, blue = (
            int(value[index:index + 2], 16)
            for index in (1, 3, 5)
        )
    if not all(0 <= component <= 255 for component in (red, green, blue)):
        return None
    hue, saturation, _ = colorsys.rgb_to_hsv(
        red / 255, green / 255, blue / 255
    )
    return None if saturation < 0.12 else hue * 360


def _explanation(
    items: tuple[ClothingItem, ...],
    weather: str | None,
    occasion: str | None,
    preferred_color: str | None,
    style: str | None,
    gender: str | None,
    missing_categories: list[str],
) -> str:
    reasons = ["Built from items in your wardrobe"]
    if weather:
        reasons.append(f"filtered for {weather} weather")
    if occasion:
        reasons.append(f"matched to {occasion}")
    if style:
        reasons.append(f"matched to {style} style")
    elif len({item.style for item in items}) == 1:
        reasons.append(f"{items[0].style} style")
    if gender:
        reasons.append(f"matched for {gender}")
    if preferred_color and any(preferred_color.lower() in item.color.lower() for item in items):
        reasons.append(f"includes your preferred {preferred_color} color")
    if _color_harmony([item.color.strip().lower() for item in items]) > 0:
        reasons.append("the colors work well together")
    if missing_categories:
        labels = {"top": "a top", "bottom": "a bottom", "shoes": "shoes"}
        reasons.append(
            "complete this look with "
            + " and ".join(labels[category] for category in missing_categories)
        )
    return "; ".join(reasons) + "."
