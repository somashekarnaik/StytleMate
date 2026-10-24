from hashlib import sha256
from pathlib import Path

from PIL import Image, ImageDraw, ImageOps

CELL_WIDTH = 320
CELL_HEIGHT = 420
PADDING = 16


def create_outfit_preview(items: list[dict], upload_dir: Path) -> str:
    preview_dir = upload_dir / "outfit-previews"
    preview_dir.mkdir(parents=True, exist_ok=True)
    cache_key = "|".join(f"{item['id']}:{item['image_path']}" for item in items)
    filename = f"{sha256(cache_key.encode()).hexdigest()[:24]}.webp"
    output_path = preview_dir / filename
    if output_path.exists():
        return f"/media/outfit-previews/{filename}"

    canvas = Image.new(
        "RGB",
        (CELL_WIDTH * len(items), CELL_HEIGHT),
        color="#f4f4ef",
    )
    draw = ImageDraw.Draw(canvas)
    for index, item in enumerate(items):
        left = index * CELL_WIDTH
        with Image.open(upload_dir / Path(item["image_path"]).name) as source:
            photo = ImageOps.exif_transpose(source).convert("RGB")
            photo.thumbnail((CELL_WIDTH - PADDING * 2, CELL_HEIGHT - PADDING * 2))
            x = left + (CELL_WIDTH - photo.width) // 2
            y = (CELL_HEIGHT - photo.height) // 2
            canvas.paste(photo, (x, y))
        if index:
            draw.line((left, 0, left, CELL_HEIGHT), fill="#ffffff", width=5)

    canvas.save(output_path, format="WEBP", quality=88, method=6)
    return f"/media/outfit-previews/{filename}"
