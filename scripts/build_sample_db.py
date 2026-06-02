import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


PROJECT_DIR = Path(__file__).resolve().parents[1]
MANNEQUIN_DIR = PROJECT_DIR / "data" / "mannequins"
CLOTHES_DIR = PROJECT_DIR / "data" / "clothes"
METADATA_PATH = CLOTHES_DIR / "metadata.json"


def load_font(size: int, bold: bool = False) -> ImageFont.ImageFont:
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/dejavu/DejaVuSans.ttf",
    ]
    for candidate in candidates:
        path = Path(candidate)
        if path.exists():
            return ImageFont.truetype(str(path), size)
    return ImageFont.load_default()


def text_center(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], text: str, font: ImageFont.ImageFont, fill: tuple[int, int, int]) -> None:
    bbox = draw.textbbox((0, 0), text, font=font)
    width = bbox[2] - bbox[0]
    height = bbox[3] - bbox[1]
    x = box[0] + (box[2] - box[0] - width) // 2
    y = box[1] + (box[3] - box[1] - height) // 2
    draw.text((x, y), text, font=font, fill=fill)


def make_clothing_image(path: Path, category: str, description: str, color: tuple[int, int, int], accent: tuple[int, int, int] | None = None) -> None:
    if path.exists():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    image = Image.new("RGB", (320, 320), (248, 250, 252))
    draw = ImageDraw.Draw(image)
    title_font = load_font(23, bold=True)
    label_font = load_font(17)
    accent = accent or tuple(max(channel - 45, 0) for channel in color)

    draw.rounded_rectangle((18, 18, 302, 302), radius=24, fill=(255, 255, 255), outline=(203, 213, 225), width=2)

    if category == "top":
        draw.polygon([(100, 80), (145, 55), (175, 55), (220, 80), (250, 135), (220, 155), (205, 126), (205, 238), (115, 238), (115, 126), (100, 155), (70, 135)], fill=color, outline=accent)
    elif category == "bottom":
        draw.polygon([(112, 75), (208, 75), (218, 255), (174, 255), (162, 130), (150, 255), (102, 255)], fill=color, outline=accent)
        draw.line((160, 82, 160, 248), fill=accent, width=3)
    else:
        if "cap" in description:
            draw.pieslice((85, 95, 235, 245), 180, 360, fill=color, outline=accent)
            draw.ellipse((178, 159, 282, 193), fill=color, outline=accent)
        elif "backpack" in description:
            draw.rounded_rectangle((105, 70, 215, 250), radius=36, fill=color, outline=accent, width=3)
            draw.arc((76, 88, 128, 236), 90, 270, fill=accent, width=8)
            draw.arc((192, 88, 244, 236), 270, 90, fill=accent, width=8)
        else:
            draw.rounded_rectangle((92, 100, 228, 242), radius=18, fill=color, outline=accent, width=3)
            draw.arc((112, 62, 208, 142), 180, 360, fill=accent, width=7)

    text_center(draw, (26, 250, 294, 286), description, title_font, (31, 41, 55))
    text_center(draw, (26, 282, 294, 306), category, label_font, (100, 116, 139))
    image.save(path)


def make_mannequin_image(path: Path, gender: str, age_group: str) -> None:
    if path.exists():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    image = Image.new("RGBA", (420, 640), (255, 255, 255, 0))
    draw = ImageDraw.Draw(image)
    font = load_font(28, bold=True)
    small_font = load_font(18)

    if age_group == "kids":
        color = (227, 233, 242, 255)
        outline = (88, 100, 122, 255)
    elif gender == "male":
        color = (211, 222, 245, 255)
        outline = (45, 82, 130, 255)
    elif gender == "female":
        color = (245, 218, 226, 255)
        outline = (139, 66, 90, 255)
    else:
        color = (226, 232, 240, 255)
        outline = (71, 85, 105, 255)

    scale = {"child": 0.78, "teenager": 0.9, "adult": 1.0, "elderly": 0.96, "unknown": 1.0}.get(age_group, 1.0)
    center_x = 210
    head_r = int(50 * scale)
    head_y = 58
    body_top = head_y + head_r * 2 + 16
    body_h = int(225 * scale)
    body_w = int(150 * scale)

    draw.ellipse((center_x - head_r, head_y, center_x + head_r, head_y + head_r * 2), fill=color, outline=outline, width=4)
    draw.rounded_rectangle((center_x - body_w // 2, body_top, center_x + body_w // 2, body_top + body_h), radius=int(52 * scale), fill=color, outline=outline, width=4)
    draw.line((center_x - body_w // 2, body_top + 42, center_x - body_w, body_top + 190), fill=outline, width=int(22 * scale))
    draw.line((center_x + body_w // 2, body_top + 42, center_x + body_w, body_top + 190), fill=outline, width=int(22 * scale))
    hip_y = body_top + body_h - 8
    leg_w = int(24 * scale)
    draw.line((center_x - 35, hip_y, center_x - 58, 580), fill=outline, width=leg_w)
    draw.line((center_x + 35, hip_y, center_x + 58, 580), fill=outline, width=leg_w)

    if age_group == "elderly":
        draw.line((center_x + 95, body_top + 160, center_x + 125, 600), fill=(94, 98, 105, 255), width=6)

    if age_group == "kids":
        label = "kids"
    else:
        label = f"{gender} {age_group}".replace("unknown unknown", "unknown")
    text_center(draw, (40, 590, 380, 628), label, small_font, (55, 65, 81, 255))
    image.save(path)


def load_existing_viton_metadata() -> list[dict]:
    if not METADATA_PATH.exists():
        return []
    try:
        data = json.loads(METADATA_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    if not isinstance(data, list):
        return []
    return [
        item
        for item in data
        if isinstance(item, dict) and item.get("source_dataset") == "VITON-HD"
    ]


def main() -> None:
    MANNEQUIN_DIR.mkdir(parents=True, exist_ok=True)
    CLOTHES_DIR.mkdir(parents=True, exist_ok=True)

    clothes = [
        ("top_001", "top", "red hoodie", ["red", "hoodie", "casual"], (220, 38, 38), None),
        ("top_002", "top", "blue jacket", ["blue", "jacket", "outerwear"], (37, 99, 235), None),
        ("top_003", "top", "white shirt", ["white", "shirt", "formal"], (245, 245, 245), (148, 163, 184)),
        ("top_004", "top", "red checkered shirt", ["red", "checkered", "shirt"], (239, 68, 68), (127, 29, 29)),
        ("top_005", "top", "black t-shirt", ["black", "t-shirt", "shirt"], (31, 41, 55), None),
        ("bottom_001", "bottom", "black pants", ["black", "pants"], (31, 41, 55), None),
        ("bottom_002", "bottom", "blue jeans", ["blue", "jeans", "denim"], (29, 78, 216), None),
        ("bottom_003", "bottom", "gray skirt", ["gray", "skirt"], (107, 114, 128), None),
        ("accessory_001", "accessory", "black backpack", ["black", "backpack", "bag"], (30, 41, 59), None),
        ("accessory_002", "accessory", "white cap", ["white", "cap", "hat"], (250, 250, 250), (148, 163, 184)),
        ("accessory_003", "accessory", "brown bag", ["brown", "bag"], (146, 64, 14), None),
    ]

    metadata = []
    for item_id, category, description, tags, color, accent in clothes:
        path = CLOTHES_DIR / f"{item_id}.png"
        make_clothing_image(path, category, description, color, accent)
        metadata.append(
            {
                "id": item_id,
                "category": category,
                "image_path": f"data/clothes/{item_id}.png",
                "tags": tags,
                "manual_tags": [],
                "description": description,
                "source_dataset": "dummy_sample",
                "needs_manual_tags": False,
            }
        )

    mannequins = [
        ("male", "child"),
        ("male", "adult"),
        ("female", "child"),
        ("female", "adult"),
    ]
    created_mannequins = 0
    for gender, age_group in mannequins:
        target = MANNEQUIN_DIR / f"{gender}_{age_group}.png"
        if not target.exists():
            created_mannequins += 1
        make_mannequin_image(target, gender, age_group)
    kids_target = MANNEQUIN_DIR / "kids.png"
    if not kids_target.exists():
        created_mannequins += 1
    make_mannequin_image(kids_target, "unknown", "kids")

    viton_metadata = load_existing_viton_metadata()
    METADATA_PATH.write_text(json.dumps(metadata + viton_metadata, indent=2), encoding="utf-8")
    print(f"Created {len(metadata)} clothing records in {METADATA_PATH}")
    if viton_metadata:
        print(f"Preserved {len(viton_metadata)} VITON-HD clothing records")
    print(f"Created {created_mannequins} mannequin images in {MANNEQUIN_DIR} (existing files were preserved)")


if __name__ == "__main__":
    main()
