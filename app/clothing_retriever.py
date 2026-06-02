import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Set

from app.config import METADATA_PATH, VITON_HD_DIR
from app.viton_utils import find_viton_cloth_dir, list_images, project_relative, safe_id_part, tokens_from_filename


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
    return tokens


def _is_real_dataset_item(item: Dict) -> bool:
    source = str(item.get("source_dataset") or "").lower()
    return bool(source and source != "dummy_sample")


def _viton_cloth_items_from_disk(limit: Optional[int] = None) -> List[Dict]:
    cloth_dir = find_viton_cloth_dir(VITON_HD_DIR)
    cloth_images = list_images(cloth_dir, limit)
    items: List[Dict] = []
    for path in cloth_images:
        tokens = tokens_from_filename(path)
        items.append(
            {
                "id": f"viton_top_{safe_id_part(path)}",
                "category": "top",
                "image_path": project_relative(path),
                "tags": sorted(set(["viton", "viton-hd", "cloth", "clothing", "top", "upper"] + tokens)),
                "manual_tags": [],
                "description": f"VITON-HD top {path.stem}",
                "source_dataset": "VITON-HD",
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

    if category == "top":
        viton_items = [item for item in category_items if _is_real_dataset_item(item)]
        if not viton_items:
            viton_items = _viton_cloth_items_from_disk()
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
