import argparse
import json
import shutil
import sys
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[1]
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from app.config import PERSON_REF_DIR, PERSON_REF_METADATA_PATH, VITON_HD_DIR
from app.viton_utils import find_viton_person_dir, list_images, project_relative, safe_id_part, tokens_from_filename


def load_metadata() -> list[dict]:
    if not PERSON_REF_METADATA_PATH.exists():
        return []
    try:
        data = json.loads(PERSON_REF_METADATA_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    return data if isinstance(data, list) else []


def parse_tags(value: str) -> list[str]:
    return sorted({tag.strip().lower() for tag in value.split(",") if tag.strip()})


def main() -> int:
    parser = argparse.ArgumentParser(description="Register VITON-HD person images as fallback person references.")
    parser.add_argument("--viton-dir", type=Path, default=VITON_HD_DIR, help="Path to VITON-HD root.")
    parser.add_argument("--limit", type=int, default=12, help="Maximum number of person images to register.")
    parser.add_argument("--manual-tags", default="", help="Comma-separated tags applied to every imported person.")
    parser.add_argument("--keep-existing", action="store_true", help="Keep existing VITON-HD person metadata entries.")
    parser.add_argument("--no-copy", action="store_true", help="Reference original VITON-HD files instead of copying into data/person_refs/viton/.")
    args = parser.parse_args()

    person_dir = find_viton_person_dir(args.viton_dir.resolve())
    person_images = list_images(person_dir, args.limit)

    if not person_images:
        print("No VITON-HD person images found. Existing dummy mannequins remain usable.")
        print("Run scripts/check_viton_hd.py for expected folder layouts.")
        return 0

    existing = load_metadata()
    if args.keep_existing:
        metadata = existing
    else:
        metadata = [
            item
            for item in existing
            if not (isinstance(item, dict) and item.get("source_dataset") == "VITON-HD")
        ]

    manual_tags = parse_tags(args.manual_tags)
    copy_dir = PERSON_REF_DIR / "viton"
    if not args.no_copy:
        copy_dir.mkdir(parents=True, exist_ok=True)

    imported = []
    for path in person_images:
        source_rel_path = project_relative(path)
        if args.no_copy:
            image_rel_path = source_rel_path
        else:
            copy_path = copy_dir / f"{safe_id_part(path)}{path.suffix.lower()}"
            shutil.copy2(path, copy_path)
            image_rel_path = project_relative(copy_path)

        file_tokens = tokens_from_filename(path)
        item_id = f"viton_person_{safe_id_part(path)}"
        imported.append(
            {
                "id": item_id,
                "category": "person",
                "image_path": image_rel_path,
                "gender": "unknown",
                "age_group": "unknown",
                "tags": sorted(set(["viton", "viton-hd", "person", "model", "reference"] + file_tokens)),
                "manual_tags": manual_tags,
                "description": f"VITON-HD person {path.stem}",
                "source_dataset": "VITON-HD",
                "source_path": source_rel_path,
                "needs_manual_tags": True,
            }
        )

    existing_ids = {item.get("id") for item in metadata if isinstance(item, dict)}
    imported = [item for item in imported if item["id"] not in existing_ids]
    metadata.extend(imported)
    PERSON_REF_METADATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    PERSON_REF_METADATA_PATH.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    print(f"Registered {len(imported)} VITON-HD person records in {PERSON_REF_METADATA_PATH}")
    print(f"Person source: {person_dir}")
    if not args.no_copy:
        print(f"Copied selected person images to {copy_dir}")
    if imported:
        print(f"First imported person: {imported[0]['id']} -> {imported[0]['image_path']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
