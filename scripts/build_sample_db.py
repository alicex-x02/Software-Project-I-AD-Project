from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


PROJECT_DIR = Path(__file__).resolve().parents[1]
MANNEQUIN_DIR = PROJECT_DIR / "data" / "mannequins"


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

    if age_group == "kids":
        label = "kids"
    else:
        label = f"{gender} {age_group}".replace("unknown unknown", "unknown")
    text_center(draw, (40, 590, 380, 628), label, small_font, (55, 65, 81, 255))
    image.save(path)


def main() -> None:
    MANNEQUIN_DIR.mkdir(parents=True, exist_ok=True)

    mannequins = [
        ("male", "child"),
        ("male", "adult"),
        ("female", "child"),
        ("female", "adult"),
    ]

    created = 0
    for gender, age_group in mannequins:
        target = MANNEQUIN_DIR / f"{gender}_{age_group}.png"
        if not target.exists():
            created += 1
        make_mannequin_image(target, gender, age_group)

    kids_target = MANNEQUIN_DIR / "kids.png"
    if not kids_target.exists():
        created += 1
    make_mannequin_image(kids_target, "unknown", "kids")

    print(f"Created {created} mannequin images in {MANNEQUIN_DIR} (existing files were preserved)")


if __name__ == "__main__":
    main()
