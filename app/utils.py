import re
from datetime import datetime
from pathlib import Path
from typing import Optional


SAFE_NAME_PATTERN = re.compile(r"[^A-Za-z0-9_.-]+")


def sanitize_filename(filename: Optional[str], default_prefix: str = "result") -> str:
    """Return a safe filename stem suitable for writing under outputs/."""
    raw = (filename or "").strip()
    if not raw:
        raw = f"{default_prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    name = Path(raw).name
    if name.lower().endswith(".png"):
        name = name[:-4]

    name = name.replace(" ", "_")
    name = SAFE_NAME_PATTERN.sub("_", name)
    name = name.strip("._-")

    if not name:
        name = f"{default_prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    return name[:80]


def output_path_for(filename: Optional[str]) -> Path:
    from app.config import OUTPUT_DIR

    safe_stem = sanitize_filename(filename)
    return OUTPUT_DIR / f"{safe_stem}.png"


def project_relative(path: Optional[Path]) -> Optional[str]:
    if path is None:
        return None

    from app.config import BASE_DIR

    try:
        return path.resolve().relative_to(BASE_DIR).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def resolve_project_path(path_value: Optional[str]) -> Optional[Path]:
    if not path_value:
        return None

    from app.config import BASE_DIR

    path = Path(path_value)
    if not path.is_absolute():
        path = BASE_DIR / path
    return path


def normalize_gender(value: Optional[str]) -> str:
    value = (value or "male").lower().strip()
    return value if value in {"male", "female"} else "male"


def normalize_age_group(value: Optional[str]) -> str:
    value = (value or "adult").lower().strip()
    if value in {"adult", "kids"}:
        return value
    if value in {"child", "teenager", "elderly", "unknown"}:
        return "adult" if value != "child" else "kids"
    return "adult"
