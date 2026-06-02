import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Set

from PIL import Image

from app.config import DRESSCODE_DIR, METADATA_PATH, VITON_HD_DIR
from app.utils import resolve_project_path
from app.viton_utils import (
    find_viton_cloth_dir,
    list_images,
    list_dresscode_garments,
    project_relative,
    safe_id_part,
    tokens_from_filename,
)


TOKEN_SPLIT_PATTERN = re.compile(r"[\s,\-]+")


def load_metadata() -> List[Dict]:
    """Load clothes metadata from data/clothes/metadata.json."""
    if not METADATA_PATH.exists():
        return []

    try:
        data = json.loads(METADATA_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []

    if not isinstance(data, list):
        return []
    return [item for item in data if isinstance(item, dict)]


def tokenize_text(text: str) -> Set[str]:
    text = (text or "").lower().strip()
    if not text:
        return set()
    return {token for token in TOKEN_SPLIT_PATTERN.split(text) if token}


def _item_tokens(item: Dict) -> Set[str]:
    tags = (item.get("tags") or []) + (item.get("manual_tags") or [])
    description = item.get("description") or ""
    tokens = tokenize_text(description)
    for tag in tags:
        tokens.update(tokenize_text(str(tag)))
    tokens.update(tokenize_text(str(item.get("id") or "")))
    tokens.update(tokenize_text(str(item.get("image_path") or "")))
    tokens.update(_infer_color_tags_from_image(item.get("image_path")))
    return tokens


def _classify_color(rgb: tuple[int, int, int]) -> Optional[str]:
    r, g, b = rgb
    brightness = (r + g + b) / 3
    max_c = max(rgb)
    min_c = min(rgb)
    chroma = max_c - min_c

    if brightness < 55:
        return "black"
    if brightness > 220 and chroma < 30:
        return "white"
    if chroma < 24:
        return "gray"
    if r > g + 25 and r > b + 25:
        return "red"
    if b > r + 20 and b > g + 10:
        return "blue"
    if g > r + 20 and g > b + 10:
        return "green"
    return None


@lru_cache(maxsize=256)
def _infer_color_tags_from_image(image_path_value: Optional[str]) -> Set[str]:
    if not image_path_value:
        return set()

    path = resolve_project_path(image_path_value) or Path(image_path_value)
    if not path.exists():
        return set()

    try:
        image = Image.open(path).convert("RGB").resize((48, 48))
    except OSError:
        return set()

    samples = []
    for r, g, b in image.getdata():
        if r + g + b > 720:
            continue
        if abs(r - g) < 12 and abs(g - b) < 12 and r > 235:
            continue
        samples.append((r, g, b))

    if not samples:
        samples = list(image.getdata())

    bucket_counts: Dict[str, int] = {}
    for rgb in samples:
        label = _classify_color(rgb)
        if label:
            bucket_counts[label] = bucket_counts.get(label, 0) + 1

    if not bucket_counts:
        return set()

    ranked = sorted(bucket_counts.items(), key=lambda kv: kv[1], reverse=True)
    dominant = {ranked[0][0]}
    if len(ranked) > 1 and ranked[1][1] >= ranked[0][1] * 0.6:
        dominant.add(ranked[1][0])
    return dominant


def _is_real_dataset_item(item: Dict) -> bool:
    source = str(item.get("source_dataset") or "").lower()
    return bool(source and source != "dummy_sample")


def _cloth_items_from_disk(dataset_name: str, dataset_dir: Path, category: str, limit: Optional[int] = None) -> List[Dict]:
    if dataset_name == "DressCode":
        cloth_images = list_dresscode_garments(dataset_dir, "upper_body" if category == "top" else "lower_body", limit)
    else:
        cloth_dir = find_viton_cloth_dir(dataset_dir)
        cloth_images = list_images(cloth_dir, limit)
    items: List[Dict] = []
    for path in cloth_images:
        tokens = tokens_from_filename(path)
        items.append(
            {
                "id": f"{dataset_name.lower()}_{category}_{safe_id_part(path)}",
                "category": category,
                "image_path": project_relative(path),
                "tags": sorted(set([dataset_name.lower(), "cloth", "clothing", category, "upper"] + tokens)),
                "manual_tags": [],
                "description": f"{dataset_name} {category} {path.stem}",
                "source_dataset": dataset_name,
                "source_path": project_relative(path),
                "needs_manual_tags": True,
            }
        )
    return items


def score_item(query_tokens: Sequence[str], item: Dict) -> int:
    item_tokens = _item_tokens(item)
    return len(set(query_tokens) & item_tokens)


def retrieve_best_clothing(description: str, category: str) -> Optional[Dict]:
    """Return the best tag-overlap match for a clothing category.

    This MVP intentionally uses transparent token matching. A future CLIP-based
    retriever can keep this function signature and replace scoring with image
    and text embeddings while preserving API behavior.
    """
    category_items = [item for item in load_metadata() if item.get("category") == category]

    if category in {"top", "bottom"}:
        dresscode_items = [item for item in category_items if str(item.get("source_dataset") or "").lower() == "dresscode"]
        if not dresscode_items:
            dresscode_items = _cloth_items_from_disk("DressCode", DRESSCODE_DIR, category)
        if dresscode_items:
            category_items = dresscode_items
        else:
            viton_items = [item for item in category_items if _is_real_dataset_item(item)]
            if not viton_items:
                viton_items = _cloth_items_from_disk("VITON-HD", VITON_HD_DIR, category)
            if viton_items:
                category_items = viton_items

    if not category_items:
        return None

    query_tokens = tokenize_text(description)
    best_item = category_items[0]
    best_score = -1

    for item in category_items:
        score = score_item(query_tokens, item)
        if score > best_score:
            best_item = item
            best_score = score

    if best_score <= 0:
        return category_items[0]

    return best_item
