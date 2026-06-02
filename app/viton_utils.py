import re
from pathlib import Path
from typing import Iterable, Optional

from app.config import BASE_DIR, VITON_HD_DIR


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
