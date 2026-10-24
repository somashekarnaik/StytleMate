from io import BytesIO

from PIL import Image, ImageOps, UnidentifiedImageError
from pillow_heif import register_heif_opener

register_heif_opener()

ALLOWED_FORMATS = {"JPEG", "PNG", "WEBP", "BMP", "GIF", "TIFF", "HEIF", "HEIC"}
MAX_IMAGE_DIMENSION = 1600
MAX_IMAGE_PIXELS = 30_000_000


class InvalidImageError(ValueError):
    pass


def process_image(data: bytes) -> tuple[bytes, str]:
    try:
        with Image.open(BytesIO(data)) as image:
            if image.format not in ALLOWED_FORMATS:
                raise InvalidImageError(
                    "Upload a JPEG, PNG, WebP, BMP, GIF, TIFF, or HEIC image."
                )
            if image.width * image.height > MAX_IMAGE_PIXELS:
                raise InvalidImageError("Image dimensions are too large to process.")
            image = ImageOps.exif_transpose(image).convert("RGB")
            image.thumbnail((MAX_IMAGE_DIMENSION, MAX_IMAGE_DIMENSION))
            color = _dominant_color(image)
            output = BytesIO()
            image.save(output, format="WEBP", quality=85, method=6)
            return output.getvalue(), color
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError) as exc:
        raise InvalidImageError("The uploaded file is not a valid image.") from exc


def _dominant_color(image: Image.Image) -> str:
    sample = image.copy()
    sample.thumbnail((100, 100))
    color = sample.quantize(colors=1).convert("RGB").getpixel((0, 0))
    return "#{:02x}{:02x}{:02x}".format(*color)
