import argparse
import json
import sys
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[1]
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from app.config import METADATA_PATH, VITON_HD_DIR
from app.viton_utils import find_viton_cloth_dir, list_images, project_relative, safe_id_part, tokens_from_filename


def load_metadata() -> list[dict]:
    if not METADATA_PATH.exists():
        return []
    try:
        data = json.loads(METADATA_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    return data if isinstance(data, list) else []


def parse_tags(value: str) -> list[str]:
    return sorted({tag.strip().lower() for tag in value.split(",") if tag.strip()})


def main() -> int:
    parser = argparse.ArgumentParser(description="Register VITON-HD cloth images in data/clothes/metadata.json.")
    parser.add_argument("--viton-dir", type=Path, default=VITON_HD_DIR, help="Path to VITON-HD root.")
    parser.add_argument("--limit", type=int, default=30, help="Maximum number of cloth images to register.")
    parser.add_argument("--category", default="top", choices=["top", "bottom", "accessory"], help="Category to assign.")
    parser.add_argument("--manual-tags", default="", help="Comma-separated tags applied to every imported item.")
    parser.add_argument("--keep-existing", action="store_true", help="Keep existing VITON-HD metadata entries.")
    args = parser.parse_args()

    cloth_dir = find_viton_cloth_dir(args.viton_dir.resolve())
    cloth_images = list_images(cloth_dir, args.limit)

    if not cloth_images:
        print("No VITON-HD cloth images found. Existing dummy sample DB remains usable.")
        print("Run scripts/check_viton_hd.py for expected folder layouts.")
        return 0

    existing = load_metadata()
    if args.keep_existing:
        metadata = existing
    else:
        metadata = [
            item
            for item in existing
            if not (isinstance(item, dict) and item.get("source_dataset") == "VITON-HD" and item.get("category") == args.category)
        ]

    manual_tags = parse_tags(args.manual_tags)
    imported = []
    for path in cloth_images:
        rel_path = project_relative(path)
        file_tokens = tokens_from_filename(path)
        item_id = f"viton_{args.category}_{safe_id_part(path)}"
        imported.append(
            {
                "id": item_id,
                "category": args.category,
                "image_path": rel_path,
                "tags": sorted(set(["viton", "viton-hd", "cloth", "clothing", args.category, "shirt", "upper"] + file_tokens)),
                "manual_tags": manual_tags,
                "description": f"VITON-HD {args.category} {path.stem}",
                "source_dataset": "VITON-HD",
                "source_path": rel_path,
                "needs_manual_tags": True,
            }
        )

    existing_ids = {item.get("id") for item in metadata if isinstance(item, dict)}
    imported = [item for item in imported if item["id"] not in existing_ids]
    metadata.extend(imported)
    METADATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    METADATA_PATH.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    print(f"Registered {len(imported)} VITON-HD cloth records in {METADATA_PATH}")
    print(f"Cloth source: {cloth_dir}")
    if imported:
        print(f"First imported item: {imported[0]['id']} -> {imported[0]['image_path']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
