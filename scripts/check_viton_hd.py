import argparse
import sys
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[1]
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from app.config import VITON_HD_DIR
from app.viton_utils import find_viton_cloth_dir, find_viton_person_dir, list_images


def main() -> int:
    parser = argparse.ArgumentParser(description="Check whether VITON-HD is available under data/viton_hd/.")
    parser.add_argument("--viton-dir", type=Path, default=VITON_HD_DIR, help="Path to the VITON-HD dataset root.")
    parser.add_argument("--strict", action="store_true", help="Exit with code 1 when required folders are missing.")
    args = parser.parse_args()

    viton_dir = args.viton_dir.resolve()
    cloth_dir = find_viton_cloth_dir(viton_dir)
    person_dir = find_viton_person_dir(viton_dir)
    cloth_images = list_images(cloth_dir)
    person_images = list_images(person_dir)

    print(f"VITON-HD root: {viton_dir}")
    print(f"Root exists: {viton_dir.exists()}")
    print(f"Cloth directory: {cloth_dir if cloth_dir else 'not found'}")
    print(f"Cloth image count: {len(cloth_images)}")
    print(f"Person image directory: {person_dir if person_dir else 'not found'}")
    print(f"Person image count: {len(person_images)}")

    if cloth_images:
        print("Sample cloth files:")
        for path in cloth_images[:5]:
            print(f"  - {path.name}")

    if person_images:
        print("Sample person files:")
        for path in person_images[:5]:
            print(f"  - {path.name}")

    ready = bool(cloth_images and person_images)
    print(f"Status: {'ready' if ready else 'missing_or_incomplete'}")

    if not ready:
        print("Expected one of these layouts:")
        print("  data/viton_hd/test/cloth/*.jpg")
        print("  data/viton_hd/test/image/*.jpg")
        print("or:")
        print("  data/viton_hd/cloth/*.jpg")
        print("  data/viton_hd/image/*.jpg")

    return 1 if args.strict and not ready else 0


if __name__ == "__main__":
    raise SystemExit(main())
