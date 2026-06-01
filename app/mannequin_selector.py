from pathlib import Path

from PIL import Image, ImageDraw

from app.config import MANNEQUIN_DIR


VALID_GENDERS = {"male", "female", "unknown"}
VALID_AGE_GROUPS = {"child", "teenager", "adult", "elderly", "unknown"}


def _safe_choice(value: str, allowed: set[str]) -> str:
    value = (value or "unknown").lower().strip()
    return value if value in allowed else "unknown"


def _create_dummy_mannequin(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    image = Image.new("RGBA", (420, 640), (255, 255, 255, 0))
    draw = ImageDraw.Draw(image)

    skin = (207, 211, 218, 255)
    outline = (92, 102, 116, 255)
    draw.ellipse((155, 45, 265, 155), fill=skin, outline=outline, width=4)
    draw.rounded_rectangle((125, 165, 295, 375), radius=55, fill=skin, outline=outline, width=4)
    draw.line((125, 190, 65, 340), fill=outline, width=22)
    draw.line((295, 190, 355, 340), fill=outline, width=22)
    draw.line((170, 370, 145, 590), fill=outline, width=28)
    draw.line((250, 370, 275, 590), fill=outline, width=28)
    image.save(path)
    return path


def select_mannequin(gender: str, age_group: str) -> Path:
    gender = _safe_choice(gender, VALID_GENDERS)
    age_group = _safe_choice(age_group, VALID_AGE_GROUPS)

    candidates = [
        MANNEQUIN_DIR / f"{gender}_{age_group}.png",
        MANNEQUIN_DIR / f"{gender}_unknown.png",
        MANNEQUIN_DIR / "unknown_unknown.png",
    ]

    for candidate in candidates:
        if candidate.exists():
            return candidate

    return _create_dummy_mannequin(MANNEQUIN_DIR / "unknown_unknown.png")
