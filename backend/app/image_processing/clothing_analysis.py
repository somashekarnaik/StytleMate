import base64
import json
from urllib.error import URLError
from urllib.request import Request, urlopen

from app.core.config import settings

CATEGORIES = {"top", "bottom", "shoes", "outerwear", "accessory"}
STYLES = {
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
GENDERS = {"men", "women", "unisex"}
SEASONS = {"all", "spring", "summer", "autumn", "winter"}


class ClothingAnalysisError(RuntimeError):
    pass


def analyze_clothing(image_data: bytes) -> dict[str, str]:
    request_body = json.dumps(
        {
            "model": settings.ollama_vision_model,
            "prompt": (
                "Analyze this photo of one clothing item. Return only a JSON object "
                "with string fields: name (short specific garment name), category "
                "(top, bottom, shoes, outerwear, or accessory), style (western, "
                "casual, traditional, formal, sports, winter, summer, party, "
                "wedding, loungewear, streetwear, or college), gender (men, women, "
                "or unisex; use unisex when the design does not clearly indicate "
                "otherwise), season (all, spring, summer, autumn, or winter), and "
                "color (the main garment color as one CSS color keyword, without spaces). "
                "Describe the garment, not the person or background. If uncertain, "
                "choose the broadest accurate category and use casual, unisex, and "
                "all as defaults."
            ),
            "images": [base64.b64encode(image_data).decode("ascii")],
            "stream": False,
            "format": "json",
            "options": {"temperature": 0, "num_predict": 256},
        }
    ).encode("utf-8")
    request = Request(
        f"{settings.ollama_host.rstrip('/')}/api/generate",
        data=request_body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urlopen(request, timeout=settings.ollama_timeout_seconds) as response:
            payload = json.loads(response.read())
    except (TimeoutError, URLError) as exc:
        raise ClothingAnalysisError(
            "Vision analysis is unavailable. Ensure Ollama is running and reachable "
            "from the API server, then pull "
            f"`{settings.ollama_vision_model}` on the Ollama server and try again."
        ) from exc
    except (json.JSONDecodeError, OSError) as exc:
        raise ClothingAnalysisError("The local vision model returned an invalid response.") from exc

    if not isinstance(payload, dict):
        raise ClothingAnalysisError("The local vision model returned an invalid response.")
    response_text = payload.get("response")
    if not isinstance(response_text, str):
        raise ClothingAnalysisError("The local vision model returned an invalid response.")
    try:
        result = json.loads(response_text)
    except json.JSONDecodeError as exc:
        raise ClothingAnalysisError("The local vision model could not analyze this photo.") from exc

    if not isinstance(result, dict):
        raise ClothingAnalysisError("The local vision model returned invalid clothing details.")
    category = _choice(result, "category", CATEGORIES)
    style = _choice(result, "style", STYLES)
    gender = _choice(result, "gender", GENDERS)
    season = _choice(result, "season", SEASONS)
    name = result.get("name")
    color = result.get("color")
    if not isinstance(name, str) or not name.strip():
        raise ClothingAnalysisError("The local vision model did not identify the garment.")
    if not isinstance(color, str) or not color.strip():
        raise ClothingAnalysisError("The local vision model did not identify the garment color.")
    return {
        "name": name.strip()[:100],
        "category": category,
        "style": style,
        "gender": gender,
        "season": season,
        "color": color.strip().lower()[:40],
    }


def analyze_outfit(image_data: bytes) -> dict[str, str | list[str]]:
    request_body = json.dumps(
        {
            "model": settings.ollama_vision_model,
            "prompt": (
                "Analyze the clothing and styling in this photo of a complete outfit. "
                "Return only a JSON object with these fields: summary (a concise, "
                "balanced overall assessment), items (an array of the visible clothing "
                "pieces), color_palette (a short description of the colors and how they "
                "work together), strengths (an array of 1-3 specific things that work "
                "well), and suggestions (an array of 1-3 practical ways to improve or "
                "adapt the outfit). Focus on clothing coordination and visible styling; "
                "do not identify or judge the person's body, identity, or attractiveness. "
                "Do not claim to assess fit when it is not clearly visible."
            ),
            "images": [base64.b64encode(image_data).decode("ascii")],
            "stream": False,
            "format": "json",
            "options": {"temperature": 0, "num_predict": 384},
        }
    ).encode("utf-8")
    request = Request(
        f"{settings.ollama_host.rstrip('/')}/api/generate",
        data=request_body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urlopen(request, timeout=settings.ollama_timeout_seconds) as response:
            payload = json.loads(response.read())
    except (TimeoutError, URLError) as exc:
        raise ClothingAnalysisError(
            "Vision analysis is unavailable. Ensure Ollama is running and reachable "
            "from the API server, then pull "
            f"`{settings.ollama_vision_model}` on the Ollama server and try again."
        ) from exc
    except (json.JSONDecodeError, OSError) as exc:
        raise ClothingAnalysisError("The local vision model returned an invalid response.") from exc

    if not isinstance(payload, dict):
        raise ClothingAnalysisError("The local vision model returned an invalid response.")
    response_text = payload.get("response")
    if not isinstance(response_text, str):
        raise ClothingAnalysisError("The local vision model returned an invalid response.")
    try:
        result = json.loads(response_text)
    except json.JSONDecodeError as exc:
        raise ClothingAnalysisError("The local vision model could not analyze this outfit.") from exc

    if not isinstance(result, dict):
        raise ClothingAnalysisError("The local vision model returned invalid outfit details.")
    summary = _required_text(result, "summary", 400)
    color_palette = _required_text(result, "color_palette", 160)
    items = _required_list(result, "items", 8, 100)
    strengths = _required_list(result, "strengths", 3, 200)
    suggestions = _required_list(result, "suggestions", 3, 200)
    return {
        "summary": summary,
        "items": items,
        "color_palette": color_palette,
        "strengths": strengths,
        "suggestions": suggestions,
    }


def _required_text(payload: dict, field: str, max_length: int) -> str:
    value = payload.get(field)
    if not isinstance(value, str) or not value.strip():
        raise ClothingAnalysisError(
            f"The local vision model did not return a valid {field.replace('_', ' ')}."
        )
    return value.strip()[:max_length]


def _required_list(
    payload: dict, field: str, max_items: int, max_length: int
) -> list[str]:
    value = payload.get(field)
    if (
        not isinstance(value, list)
        or not value
        or any(not isinstance(entry, str) or not entry.strip() for entry in value)
    ):
        raise ClothingAnalysisError(
            f"The local vision model did not return valid {field.replace('_', ' ')}."
        )
    return [entry.strip()[:max_length] for entry in value[:max_items]]


def _choice(payload: dict, field: str, choices: set[str]) -> str:
    value = payload.get(field)
    if not isinstance(value, str) or value.strip().lower() not in choices:
        raise ClothingAnalysisError(
            f"The local vision model returned an unsupported {field}."
        )
    return value.strip().lower()
