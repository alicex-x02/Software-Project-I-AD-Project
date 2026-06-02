import argparse
import json
import sys
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[1]
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from app.config import METADATA_PATH, DRESSCODE_DIR
from app.viton_utils import find_dresscode_cloth_dir, list_images, project_relative, safe_id_part, tokens_from_filename


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


def category_specs(include_dresses: bool) -> list[tuple[str, str, list[str]]]:
    specs = [
        ("upper_body", "top", ["shirt", "top", "upper", "garment"]),
        ("lower_body", "bottom", ["pants", "bottom", "lower", "trousers"]),
    ]
    if include_dresses:
        specs.append(("dresses", "dress", ["dress", "one-piece"]))
    return specs


def collect_garment_files(category_root: Path, category_dir: str, limit: int) -> list[Path]:
    pair_files = [
        category_root / f"train_pairs.txt",
        category_root / f"test_pairs_paired.txt",
        category_root / f"test_pairs_unpaired.txt",
    ]

    filenames: list[str] = []
    for pair_file in pair_files:
        if not pair_file.exists():
            continue
        for line in pair_file.read_text(encoding="utf-8").splitlines():
            parts = line.strip().split()
            if len(parts) >= 2:
                filenames.append(parts[1])

    if filenames:
        images_dir = find_dresscode_cloth_dir(category_root.parent, category_dir)
        if images_dir is None:
            return []

        seen = set()
        paths: list[Path] = []
        for name in filenames:
            candidate = images_dir / name
            if candidate.exists() and candidate not in seen:
                seen.add(candidate)
                paths.append(candidate)
                if len(paths) >= limit:
                    break
        return paths

    images_dir = find_dresscode_cloth_dir(category_root.parent, category_dir)
    return list_images(images_dir, limit)


def main() -> int:
    parser = argparse.ArgumentParser(description="Register DressCode garment images in data/clothes/metadata.json.")
    parser.add_argument("--dresscode-dir", type=Path, default=DRESSCODE_DIR, help="Path to the DressCode dataset root.")
    parser.add_argument("--limit", type=int, default=80, help="Maximum number of images to register per category.")
    parser.add_argument("--manual-tags", default="", help="Comma-separated tags applied to every imported item.")
    parser.add_argument("--keep-existing", action="store_true", help="Keep existing DressCode metadata entries.")
    parser.add_argument("--include-dresses", action="store_true", help="Also import DressCode dresses.")
    args = parser.parse_args()

    root = args.dresscode_dir.resolve()
    manual_tags = parse_tags(args.manual_tags)
    existing = load_metadata()
    metadata = existing if args.keep_existing else [
        item
        for item in existing
        if not (isinstance(item, dict) and str(item.get("source_dataset") or "").lower() == "dresscode")
    ]

    imported = []
    for folder_name, category, default_tags in category_specs(args.include_dresses):
        category_root = root / folder_name
        cloth_images = collect_garment_files(category_root, folder_name, args.limit)
        for path in cloth_images:
            rel_path = project_relative(path)
            item_id = f"dresscode_{category}_{safe_id_part(path)}"
            imported.append(
                {
                    "id": item_id,
                    "category": category,
                    "image_path": rel_path,
                    "tags": sorted(set(["dresscode", folder_name, category, "garment"] + default_tags + tokens_from_filename(path))),
                    "manual_tags": manual_tags,
                    "description": f"DressCode {category} {path.stem}",
                    "source_dataset": "DressCode",
                    "source_path": rel_path,
                    "needs_manual_tags": True,
                }
            )

    existing_ids = {item.get("id") for item in metadata if isinstance(item, dict)}
    imported = [item for item in imported if item["id"] not in existing_ids]
    metadata.extend(imported)
    METADATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    METADATA_PATH.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    print(f"Registered {len(imported)} DressCode cloth records in {METADATA_PATH}")
    print(f"DressCode source: {root}")
    if imported:
        print(f"First imported item: {imported[0]['id']} -> {imported[0]['image_path']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
