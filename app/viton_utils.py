import re
from pathlib import Path
from typing import Iterable, Optional

from app.config import BASE_DIR, DRESSCODE_DIR, VITON_HD_DIR


IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
TOKEN_PATTERN = re.compile(r"[\s,\-_./]+")


def is_image_file(path: Path) -> bool:
    return path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS


def list_images(directory: Optional[Path], limit: Optional[int] = None) -> list[Path]:
    if not directory or not directory.exists():
        return []

    images = sorted(path for path in directory.iterdir() if is_image_file(path))
    if limit is not None:
        return images[: max(limit, 0)]
    return images


def first_existing_dir(candidates: Iterable[Path]) -> Optional[Path]:
    for candidate in candidates:
        if candidate.exists() and candidate.is_dir():
            return candidate
    return None


def find_viton_cloth_dir(viton_dir: Path = VITON_HD_DIR) -> Optional[Path]:
    return first_existing_dir(
        [
            viton_dir / "test" / "cloth",
            viton_dir / "cloth",
            viton_dir / "train" / "cloth",
        ]
    )


def find_viton_person_dir(viton_dir: Path = VITON_HD_DIR) -> Optional[Path]:
    return first_existing_dir(
        [
            viton_dir / "test" / "image",
            viton_dir / "image",
            viton_dir / "train" / "image",
        ]
    )


def find_viton_cloth_mask_dir(viton_dir: Path = VITON_HD_DIR) -> Optional[Path]:
    return first_existing_dir(
        [
            viton_dir / "test" / "cloth-mask",
            viton_dir / "cloth-mask",
            viton_dir / "train" / "cloth-mask",
        ]
    )


def find_dresscode_category_dir(dresscode_dir: Path = DRESSCODE_DIR, category: str = "upper_body") -> Optional[Path]:
    category = (category or "").strip().lower()
    return first_existing_dir(
        [
            dresscode_dir / category / "images",
            dresscode_dir / "train" / category / "images",
            dresscode_dir / "test" / category / "images",
            dresscode_dir / category,
        ]
    )


def find_dresscode_cloth_dir(dresscode_dir: Path = DRESSCODE_DIR, category: str = "upper_body") -> Optional[Path]:
    return find_dresscode_category_dir(dresscode_dir, category)


def list_dresscode_garments(dresscode_dir: Path = DRESSCODE_DIR, category: str = "upper_body", limit: Optional[int] = None) -> list[Path]:
    category = (category or "").strip().lower()
    category_root = dresscode_dir / category
    images_dir = find_dresscode_cloth_dir(dresscode_dir, category)
    if images_dir is None or not category_root.exists():
        return []

    pair_files = [
        category_root / "train_pairs.txt",
        category_root / "test_pairs_paired.txt",
        category_root / "test_pairs_unpaired.txt",
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
        seen = set()
        garments: list[Path] = []
        for name in filenames:
            candidate = images_dir / name
            if candidate.exists() and candidate not in seen:
                seen.add(candidate)
                garments.append(candidate)
                if limit is not None and len(garments) >= max(limit, 0):
                    break
        return garments

    return list_images(images_dir, limit)


def project_relative(path: Path) -> str:
    try:
        return path.resolve().relative_to(BASE_DIR).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def tokens_from_filename(path: Path) -> list[str]:
    tokens = [token.lower() for token in TOKEN_PATTERN.split(path.stem) if token]
    return sorted(set(tokens))


def safe_id_part(path: Path) -> str:
    raw = path.stem.lower()
    raw = re.sub(r"[^a-z0-9]+", "_", raw)
    return raw.strip("_") or "item"
