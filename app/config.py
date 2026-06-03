from app.env_loader import load_project_env
from pathlib import Path


load_project_env()

BASE_DIR = Path(__file__).resolve().parents[1]
APP_DIR = BASE_DIR / "app"
WEB_DIR = BASE_DIR / "web"
DATA_DIR = BASE_DIR / "data"
MANNEQUIN_DIR = DATA_DIR / "mannequins"
GENERATED_GARMENT_DIR = DATA_DIR / "generated_garments"
OUTPUT_DIR = BASE_DIR / "outputs"
MODELS_DIR = BASE_DIR / "models"


def ensure_runtime_dirs() -> None:
    """Create folders the running API writes to or depends on."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    MANNEQUIN_DIR.mkdir(parents=True, exist_ok=True)
    GENERATED_GARMENT_DIR.mkdir(parents=True, exist_ok=True)
    MODELS_DIR.mkdir(parents=True, exist_ok=True)


ensure_runtime_dirs()
