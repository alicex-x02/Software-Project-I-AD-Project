from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]
APP_DIR = BASE_DIR / "app"
WEB_DIR = BASE_DIR / "web"
DATA_DIR = BASE_DIR / "data"
MANNEQUIN_DIR = DATA_DIR / "mannequins"
CLOTHES_DIR = DATA_DIR / "clothes"
METADATA_PATH = CLOTHES_DIR / "metadata.json"
PERSON_REF_DIR = DATA_DIR / "person_refs"
PERSON_REF_METADATA_PATH = PERSON_REF_DIR / "metadata.json"
VITON_HD_DIR = DATA_DIR / "viton_hd"
DRESSCODE_DIR = DATA_DIR / "dresscode"
OUTPUT_DIR = BASE_DIR / "outputs"
MODELS_DIR = BASE_DIR / "models"


def ensure_runtime_dirs() -> None:
    """Create folders the running API writes to or depends on."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    MANNEQUIN_DIR.mkdir(parents=True, exist_ok=True)
    CLOTHES_DIR.mkdir(parents=True, exist_ok=True)
    PERSON_REF_DIR.mkdir(parents=True, exist_ok=True)
    VITON_HD_DIR.mkdir(parents=True, exist_ok=True)
    DRESSCODE_DIR.mkdir(parents=True, exist_ok=True)
    MODELS_DIR.mkdir(parents=True, exist_ok=True)


ensure_runtime_dirs()
