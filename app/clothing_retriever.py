import json
import re
from functools import lru_cache
from typing import Dict, List, Optional, Sequence, Set

from app.config import METADATA_PATH


TOKEN_SPLIT_PATTERN = re.compile(r"[\s,\-]+")


@lru_cache(maxsize=1)
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
    tags = item.get("tags") or []
    description = item.get("description") or ""
    tokens = tokenize_text(description)
    for tag in tags:
        tokens.update(tokenize_text(str(tag)))
    return tokens


def score_item(query_tokens: Sequence[str], item: Dict) -> int:
    item_tokens = _item_tokens(item)
    return len(set(query_tokens) & item_tokens)


def retrieve_best_clothing(description: str, category: str) -> Optional[Dict]:
    """Return the best tag-overlap match for a clothing category.

    This MVP intentionally uses transparent token matching. A future CLIP-based
    retriever can keep this function signature and replace scoring with image
    and text embeddings while preserving API behavior.
    """
    category_items = [
        item for item in load_metadata() if item.get("category") == category
    ]
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
