import json
from pathlib import Path
from typing import Dict, Optional

from PIL import Image, ImageDraw

from app.config import MANNEQUIN_DIR, PERSON_REF_DIR, PERSON_REF_METADATA_PATH
from app.utils import resolve_project_path


VALID_GENDERS = {"male", "female"}
VALID_AGE_GROUPS = {"adult", "kids"}


def _safe_choice(value: str, allowed: set[str], default: str) -> str:
    value = (value or default).lower().strip()
    return value if value in allowed else default


def _create_dummy_mannequin(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    image = Image.new("RGBA", (420, 640), (255, 255, 255, 0))
    draw = ImageDraw.Draw(image)

    skin = (207, 211, 218, 255)
    outline = (92, 102, 116, 255)
    draw.ellipse((155, 45, 265, 155), fill=skin, outline=outline, width=4)
    draw.rounded_rectangle((125, 165, 295, 375), radius=55, fill=skin, outline=outline, width=4)
    draw.line((125, 190, 65, 340), fill=outline, width=22)
    draw.line((295, 190, 355, 340), fill=outline, width=22)
    draw.line((170, 370, 145, 590), fill=outline, width=28)
    draw.line((250, 370, 275, 590), fill=outline, width=28)
    image.save(path)
    return path


def _load_person_metadata() -> list[Dict]:
    if not PERSON_REF_METADATA_PATH.exists():
        return []

    try:
        data = json.loads(PERSON_REF_METADATA_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []

    if not isinstance(data, list):
        return []
    return [item for item in data if isinstance(item, dict)]


def _person_tokens(item: Dict) -> set[str]:
    values = [
        item.get("id"),
        item.get("description"),
        item.get("gender"),
        item.get("age_group"),
    ]
    tags = (item.get("tags") or []) + (item.get("manual_tags") or [])
    tokens = set()
    for value in values + tags:
        if not value:
            continue
        tokens.update(str(value).lower().replace("-", " ").replace("_", " ").split())
    return tokens


def _resolve_person_path(item: Dict) -> Optional[Path]:
    image_path = resolve_project_path(item.get("image_path"))
    if image_path and image_path.exists():
        return image_path
    source_path = resolve_project_path(item.get("source_path"))
    if source_path and source_path.exists():
        return source_path
    return None


def _select_person_reference(gender: str, age_group: str) -> Optional[Path]:
    metadata_items = _load_person_metadata()
    existing_items = [(item, _resolve_person_path(item)) for item in metadata_items]
    existing_items = [(item, path) for item, path in existing_items if path is not None]

    if existing_items:
        targets = {gender, age_group} - {"unknown"}
        best_item, best_path = existing_items[0]
        best_score = -1
        for item, path in existing_items:
            score = len(targets & _person_tokens(item))
            if score > best_score:
                best_item, best_path = item, path
                best_score = score
        return best_path

    direct_images = sorted(
        path
        for path in PERSON_REF_DIR.iterdir()
        if path.is_file() and path.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
    ) if PERSON_REF_DIR.exists() else []
    return direct_images[0] if direct_images else None


def select_mannequin(gender: str, age_group: str) -> Path:
    gender = _safe_choice(gender, VALID_GENDERS, "male")
    age_group = _safe_choice(age_group, VALID_AGE_GROUPS, "adult")

    if age_group == "kids":
        kids_path = MANNEQUIN_DIR / "kids.png"
        if kids_path.exists():
            return kids_path
        fallback_candidates = [
            MANNEQUIN_DIR / "unknown_unknown.png",
            MANNEQUIN_DIR / f"{gender}_unknown.png",
        ]
        for candidate in fallback_candidates:
            if candidate.exists():
                return candidate
        return _create_dummy_mannequin(MANNEQUIN_DIR / "kids.png")

    candidates = [
        MANNEQUIN_DIR / f"{gender}_adult.png",
        MANNEQUIN_DIR / f"{gender}_unknown.png",
        MANNEQUIN_DIR / "unknown_unknown.png",
    ]

    for candidate in candidates:
        if candidate.exists():
            return candidate

    person_reference = _select_person_reference(gender, age_group)
    if person_reference:
        return person_reference

    return _create_dummy_mannequin(MANNEQUIN_DIR / "unknown_unknown.png")
