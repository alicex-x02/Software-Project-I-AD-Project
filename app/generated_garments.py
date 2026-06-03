import base64
import hashlib
import json
import os
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
from threading import Lock
from typing import Dict, Optional
from urllib.request import urlopen

from openai import OpenAI
from PIL import Image
from PIL import ImageDraw, ImageFont
from app.config import GENERATED_GARMENT_DIR
from app.utils import project_relative


INDEX_PATH = GENERATED_GARMENT_DIR / "index.json"
OPENAI_IMAGE_MODEL = os.getenv("OPENAI_IMAGE_MODEL", "gpt-image-1.5")
FALLBACK_IMAGE_MODELS = [
    OPENAI_IMAGE_MODEL,
    "gpt-image-1.5",
    "gpt-image-1",
]

_LOCK = Lock()


def _normalize_description(description: str) -> str:
    text = (description or "").lower().strip()
    text = text.replace("/", " ").replace("-", " ").replace(",", " ")
    return " ".join(text.split())


def _cache_key(category: str, description: str) -> str:
    raw = f"{category.strip().lower()}::{_normalize_description(description)}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]


def _garment_path(category: str, cache_key: str) -> Path:
    return GENERATED_GARMENT_DIR / category.strip().lower() / f"{cache_key}.png"


def _load_index() -> list[Dict]:
    if not INDEX_PATH.exists():
        return []

    try:
        data = json.loads(INDEX_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []

    if not isinstance(data, list):
        return []
    return [item for item in data if isinstance(item, dict)]


def _write_index(entries: list[Dict]) -> None:
    INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    INDEX_PATH.write_text(json.dumps(entries, indent=2), encoding="utf-8")


def _prompt_for_garment(description: str, category: str) -> str:
    category_name = {
        "top": "shirt, hoodie, jacket, sweater, or other upper-body garment",
        "bottom": "pants, jeans, skirt, or other lower-body garment",
        "accessory": "bag, cap, backpack, or other accessory",
    }.get(category, "garment")

    cleaned = (description or "").strip()
    return (
        "Create a clean studio product image of a single "
        f"{category_name} described as '{cleaned}'. "
        "The image must show only the clothing item or accessory, centered, "
        "front-facing, photorealistic, on a transparent background, with no person, "
        "no model, no text, no watermark, and no extra objects. "
        "Make it suitable as a virtual try-on garment reference."
    )


def _load_font(size: int, bold: bool = False) -> ImageFont.ImageFont:
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/dejavu/DejaVuSans.ttf",
    ]
    for candidate in candidates:
        path = Path(candidate)
        if path.exists():
            return ImageFont.truetype(str(path), size)
    return ImageFont.load_default()


def _draw_centered_text(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], text: str, font: ImageFont.ImageFont, fill: tuple[int, int, int]) -> None:
    bbox = draw.textbbox((0, 0), text, font=font)
    width = bbox[2] - bbox[0]
    height = bbox[3] - bbox[1]
    x = box[0] + (box[2] - box[0] - width) // 2
    y = box[1] + (box[3] - box[1] - height) // 2
    draw.text((x, y), text, font=font, fill=fill)


def _make_local_placeholder_image(description: str, category: str) -> bytes:
    category = (category or "garment").strip().lower()
    canvas = Image.new("RGBA", (1024, 1024), (255, 255, 255, 0))
    draw = ImageDraw.Draw(canvas)
    outline = (60, 72, 88, 255)
    fill = (226, 232, 240, 255)
    accent = {
        "top": (220, 38, 38, 255),
        "bottom": (37, 99, 235, 255),
        "accessory": (109, 40, 217, 255),
    }.get(category, (71, 85, 105, 255))

    draw.rounded_rectangle((70, 70, 954, 954), radius=46, fill=(255, 255, 255, 238), outline=(203, 213, 225, 255), width=4)
    draw.rounded_rectangle((170, 170, 854, 780), radius=54, fill=fill, outline=outline, width=4)

    if category == "top":
        draw.polygon([(340, 260), (470, 210), (554, 210), (684, 260), (740, 380), (684, 430), (648, 355), (648, 690), (376, 690), (376, 355), (340, 430), (284, 380)], fill=accent, outline=outline)
    elif category == "bottom":
        draw.polygon([(350, 250), (674, 250), (720, 690), (560, 690), (530, 430), (498, 690), (332, 690)], fill=accent, outline=outline)
        draw.line((512, 255, 512, 684), fill=(255, 255, 255, 120), width=4)
    else:
        draw.rounded_rectangle((340, 270, 684, 660), radius=60, fill=accent, outline=outline, width=4)
        draw.arc((270, 320, 390, 600), 90, 270, fill=outline, width=14)
        draw.arc((634, 320, 754, 600), 270, 90, fill=outline, width=14)

    title_font = _load_font(44, bold=True)
    body_font = _load_font(28)
    _draw_centered_text(draw, (150, 820, 874, 880), description or f"generated {category}", title_font, (31, 41, 55, 255))
    _draw_centered_text(draw, (150, 890, 874, 940), f"OpenAI cache placeholder - {category}", body_font, (71, 85, 105, 255))

    buffer = BytesIO()
    canvas.save(buffer, format="PNG")
    return buffer.getvalue()


def _decode_openai_image_response(response) -> bytes:
    data = getattr(response, "data", None) or []
    if not data:
        raise RuntimeError("OpenAI image response did not include image data.")

    first = data[0]
    if getattr(first, "b64_json", None):
        return base64.b64decode(first.b64_json)
    if getattr(first, "url", None):
        with urlopen(first.url) as response_handle:
            return response_handle.read()
    raise RuntimeError("OpenAI image response did not contain b64_json or url.")


def _try_openai_generate(prompt: str) -> Optional[bytes]:
    if not os.getenv("OPENAI_API_KEY"):
        return None

    client = OpenAI()
    seen_models = []
    for model in FALLBACK_IMAGE_MODELS:
        if model and model not in seen_models:
            seen_models.append(model)

    last_error: Optional[Exception] = None
    for model in seen_models:
        try:
            response = client.images.generate(
                model=model,
                prompt=prompt,
                size="1024x1024",
                quality="high",
                background="transparent",
                n=1,
            )
            return _decode_openai_image_response(response)
        except Exception as exc:  # pragma: no cover - depends on remote API state
            last_error = exc

    if last_error is not None:
        raise last_error
    return None


def _update_index(entry: Dict) -> None:
    entries = _load_index()
    entries = [item for item in entries if item.get("cache_key") != entry.get("cache_key")]
    entries.append(entry)
    _write_index(entries)


def find_cached_garment(description: str, category: str) -> Optional[Path]:
    cache_key = _cache_key(category, description)
    path = _garment_path(category, cache_key)
    if path.exists():
        return path

    for item in _load_index():
        if item.get("cache_key") != cache_key:
            continue
        candidate = project_relative_path_to_abs(item.get("image_path"))
        if candidate and candidate.exists():
            return candidate
    return None


def project_relative_path_to_abs(path_value: Optional[str]) -> Optional[Path]:
    if not path_value:
        return None
    path = Path(path_value)
    if path.is_absolute():
        return path

    from app.config import BASE_DIR

    return (BASE_DIR / path).resolve()


def generate_or_load_garment_image(description: str, category: str) -> Optional[Path]:
    description = (description or "").strip()
    category = (category or "").strip().lower()
    if not description:
        return None

    cache_key = _cache_key(category, description)
    output_path = _garment_path(category, cache_key)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if output_path.exists():
        return output_path

    with _LOCK:
        if output_path.exists():
            return output_path

        cached = find_cached_garment(description, category)
        if cached and cached.exists():
            return cached

        prompt = _prompt_for_garment(description, category)
        image_bytes = None
        try:
            image_bytes = _try_openai_generate(prompt)
        except Exception:
            image_bytes = None

        if image_bytes is None:
            image_bytes = _make_local_placeholder_image(description, category)

        try:
            Image.open(BytesIO(image_bytes)).verify()
        except Exception:
            image_bytes = _make_local_placeholder_image(description, category)

        output_path.write_bytes(image_bytes)

        entry = {
            "cache_key": cache_key,
            "category": category,
            "description": description,
            "prompt": prompt,
            "image_path": str(output_path),
            "image_path_project": project_relative(output_path),
            "source": "openai",
            "model": OPENAI_IMAGE_MODEL,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        _update_index(entry)
        return output_path
