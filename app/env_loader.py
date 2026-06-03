import os
from pathlib import Path
from typing import Iterable


def _parse_env_line(line: str) -> tuple[str, str] | None:
    stripped = line.strip()
    if not stripped or stripped.startswith("#") or "=" not in stripped:
        return None

    key, value = stripped.split("=", 1)
    key = key.strip()
    value = value.strip()

    if not key or key.startswith("export "):
        key = key.removeprefix("export ").strip()
    if not key:
        return None

    if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
        value = value[1:-1]

    return key, value


def load_project_env(env_path: Path | None = None, override: bool = False) -> Path | None:
    """Load key=value pairs from a project .env file into os.environ."""
    project_root = Path(__file__).resolve().parents[1]
    candidate_paths: Iterable[Path] = (
        (env_path.resolve() if env_path else None),
        project_root / ".env",
    )

    for candidate in candidate_paths:
        if candidate is None or not candidate.exists() or not candidate.is_file():
            continue

        for raw_line in candidate.read_text(encoding="utf-8").splitlines():
            parsed = _parse_env_line(raw_line)
            if not parsed:
                continue
            key, value = parsed
            if override or key not in os.environ:
                os.environ[key] = value
        return candidate

    return None

