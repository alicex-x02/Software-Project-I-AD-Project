from pathlib import Path
from typing import Dict, Optional

from app.generated_garments import generate_or_load_garment_image
from app.utils import project_relative
from app.viton_utils import safe_id_part


def _generated_clothing_item(description: str, category: str, image_path: Path) -> Dict:
    cleaned = (description or "").strip() or f"generated {category}"
    return {
        "id": f"openai_{category}_{safe_id_part(image_path)}",
        "category": category,
        "image_path": project_relative(image_path),
        "tags": sorted(set(["openai", "generated", "garment", category])),
        "manual_tags": [],
        "description": cleaned,
        "source_dataset": "OpenAI Generated",
        "source_path": project_relative(image_path),
        "needs_manual_tags": False,
    }


def retrieve_best_clothing(description: str, category: str) -> Optional[Dict]:
    """Generate a garment image for the requested category and return it.

    The app no longer searches any clothing datasets. Instead, it always
    creates or reuses a cached garment image under data/generated_garments/.
    """
    category = (category or "").strip().lower()
    if category not in {"top", "bottom"}:
        return None

    generated_path = generate_or_load_garment_image(description or f"plain {category}", category)
    if not generated_path or not generated_path.exists():
        return None

    return _generated_clothing_item(description, category, generated_path)
