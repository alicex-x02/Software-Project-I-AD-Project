import argparse
import sys
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[1]
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from app.config import DRESSCODE_DIR
from app.viton_utils import find_dresscode_cloth_dir, list_images


def main() -> int:
    parser = argparse.ArgumentParser(description="Check whether DressCode is available under data/dresscode/.")
    parser.add_argument("--dresscode-dir", type=Path, default=DRESSCODE_DIR, help="Path to the DressCode dataset root.")
    parser.add_argument("--strict", action="store_true", help="Exit with code 1 when required folders are missing.")
    args = parser.parse_args()

    root = args.dresscode_dir.resolve()
    upper_dir = find_dresscode_cloth_dir(root, "upper_body")
    lower_dir = find_dresscode_cloth_dir(root, "lower_body")
    dress_dir = find_dresscode_cloth_dir(root, "dresses")
    upper_images = list_images(upper_dir)
    lower_images = list_images(lower_dir)
    dress_images = list_images(dress_dir)

    print(f"DressCode root: {root}")
    print(f"Root exists: {root.exists()}")
    print(f"Upper-body directory: {upper_dir if upper_dir else 'not found'}")
    print(f"Upper-body image count: {len(upper_images)}")
    print(f"Lower-body directory: {lower_dir if lower_dir else 'not found'}")
    print(f"Lower-body image count: {len(lower_images)}")
    print(f"Dress directory: {dress_dir if dress_dir else 'not found'}")
    print(f"Dress image count: {len(dress_images)}")

    if upper_images:
        print("Sample upper-body files:")
        for path in upper_images[:5]:
            print(f"  - {path.name}")

    if lower_images:
        print("Sample lower-body files:")
        for path in lower_images[:5]:
            print(f"  - {path.name}")

    ready = bool(upper_images and lower_images)
    print(f"Status: {'ready' if ready else 'missing_or_incomplete'}")

    if not ready:
        print("Expected one of these layouts:")
        print("  data/dresscode/upper_body/images/*.jpg")
        print("  data/dresscode/lower_body/images/*.jpg")
        print("or a matching train/test split with category folders.")

    return 1 if args.strict and not ready else 0


if __name__ == "__main__":
    raise SystemExit(main())
