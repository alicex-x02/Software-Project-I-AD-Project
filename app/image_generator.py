from pathlib import Path
from typing import Dict, Optional

from PIL import Image, ImageDraw, ImageFont

from app.config import OUTPUT_DIR


USE_REAL_VTON = False


def _load_font(size: int, bold: bool = False) -> ImageFont.ImageFont:
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/dejavu/DejaVuSans.ttf",
    ]
    for candidate in candidates:
        path = Path(candidate)
        if path.exists():
            return ImageFont.truetype(str(path), size)
    return ImageFont.load_default()


def _text_size(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont) -> tuple[int, int]:
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


def _wrap_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont, max_width: int) -> list[str]:
    words = (text or "").split()
    if not words:
        return [""]

    lines: list[str] = []
    current = words[0]
    for word in words[1:]:
        candidate = f"{current} {word}"
        if _text_size(draw, candidate, font)[0] <= max_width:
            current = candidate
        else:
            lines.append(current)
            current = word
    lines.append(current)
    return lines


def _paste_image_fit(canvas: Image.Image, image_path: Optional[Path], box: tuple[int, int, int, int]) -> bool:
    if not image_path or not Path(image_path).exists():
        return False

    try:
        image = Image.open(image_path).convert("RGBA")
    except OSError:
        return False

    x1, y1, x2, y2 = box
    max_w = x2 - x1
    max_h = y2 - y1
    image.thumbnail((max_w, max_h), Image.Resampling.LANCZOS)
    x = x1 + (max_w - image.width) // 2
    y = y1 + (max_h - image.height) // 2
    canvas.alpha_composite(image, (x, y))
    return True


def _draw_placeholder_mannequin(draw: ImageDraw.ImageDraw) -> None:
    outline = (70, 76, 88)
    fill = (229, 232, 238)
    draw.ellipse((360, 120, 460, 220), fill=fill, outline=outline, width=4)
    draw.rounded_rectangle((315, 235, 505, 465), radius=65, fill=fill, outline=outline, width=4)
    draw.line((315, 270, 250, 430), fill=outline, width=24)
    draw.line((505, 270, 570, 430), fill=outline, width=24)
    draw.line((370, 460, 340, 655), fill=outline, width=30)
    draw.line((450, 460, 480, 655), fill=outline, width=30)


def _draw_label_block(
    draw: ImageDraw.ImageDraw,
    x: int,
    y: int,
    title: str,
    text: str,
    max_width: int,
    title_font: ImageFont.ImageFont,
    body_font: ImageFont.ImageFont,
) -> int:
    draw.text((x, y), title, font=title_font, fill=(35, 45, 60))
    y += 28
    for line in _wrap_text(draw, text or "-", body_font, max_width):
        draw.text((x, y), line, font=body_font, fill=(71, 85, 105))
        y += 25
    return y + 12


def fallback_generate_image(
    mannequin_path: Optional[Path],
    top_path: Optional[Path] = None,
    bottom_path: Optional[Path] = None,
    accessory_path: Optional[Path] = None,
    output_path: Optional[Path] = None,
    prompt: Optional[Dict] = None,
) -> Path:
    """Create a deterministic presentation-friendly PNG without a VTON model."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    if output_path is None:
        output_path = OUTPUT_DIR / "result.png"
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    prompt = prompt or {}
    canvas = Image.new("RGBA", (1000, 760), (255, 255, 255, 255))
    draw = ImageDraw.Draw(canvas)

    title_font = _load_font(32, bold=True)
    subtitle_font = _load_font(19)
    label_font = _load_font(18, bold=True)
    body_font = _load_font(18)
    footer_font = _load_font(16)

    draw.rectangle((0, 0, 1000, 92), fill=(245, 247, 250))
    draw.text((40, 26), "Missing Person Outfit Visualization MVP", font=title_font, fill=(24, 35, 51))
    draw.text((42, 63), "Fallback PNG renderer - ready for future virtual try-on integration", font=subtitle_font, fill=(93, 111, 131))

    mannequin_box = (75, 120, 595, 680)
    draw.rounded_rectangle((55, 110, 615, 690), radius=18, outline=(218, 225, 235), width=2)
    pasted = _paste_image_fit(canvas, mannequin_path, mannequin_box)
    if not pasted:
        _draw_placeholder_mannequin(draw)

    info_x = 650
    y = 124
    draw.text((info_x, y), "Input", font=label_font, fill=(24, 35, 51))
    y += 34
    y = _draw_label_block(draw, info_x, y, "Gender / Age", f"{prompt.get('gender', 'unknown')} / {prompt.get('age_group', 'unknown')}", 295, label_font, body_font)
    y = _draw_label_block(draw, info_x, y, "Top", prompt.get("top", ""), 295, label_font, body_font)
    y = _draw_label_block(draw, info_x, y, "Bottom", prompt.get("bottom", ""), 295, label_font, body_font)
    y = _draw_label_block(draw, info_x, y, "Accessory", prompt.get("accessory", ""), 295, label_font, body_font)

    thumb_y = max(y + 8, 460)
    draw.text((info_x, thumb_y), "Matched Clothes", font=label_font, fill=(24, 35, 51))
    thumb_y += 34

    thumb_specs = [
        ("Top", top_path),
        ("Bottom", bottom_path),
        ("Accessory", accessory_path),
    ]
    thumb_size = 88
    gap = 18
    for idx, (label, path) in enumerate(thumb_specs):
        x = info_x + idx * (thumb_size + gap)
        draw.rounded_rectangle((x, thumb_y, x + thumb_size, thumb_y + thumb_size), radius=10, outline=(203, 213, 225), width=2, fill=(248, 250, 252))
        if not _paste_image_fit(canvas, path, (x + 8, thumb_y + 8, x + thumb_size - 8, thumb_y + thumb_size - 8)):
            draw.line((x + 22, thumb_y + 44, x + thumb_size - 22, thumb_y + 44), fill=(148, 163, 184), width=3)
        text_w, _ = _text_size(draw, label, footer_font)
        draw.text((x + (thumb_size - text_w) // 2, thumb_y + thumb_size + 8), label, font=footer_font, fill=(71, 85, 105))

    footer = "Generated outfit visualization prototype"
    footer_w, footer_h = _text_size(draw, footer, footer_font)
    draw.text(((1000 - footer_w) // 2, 724 - footer_h // 2), footer, font=footer_font, fill=(100, 116, 139))

    rgb = canvas.convert("RGB")
    rgb.save(output_path, "PNG")
    return output_path


def run_virtual_tryon(
    mannequin_path,
    top_path=None,
    bottom_path=None,
    accessory_path=None,
    output_path=None,
    prompt=None,
):
    """
    Future integration point for CatVTON, IDM-VTON, or Stable Diffusion inpainting.
    For now, call fallback_generate_image().
    """
    mannequin_path = Path(mannequin_path) if mannequin_path else None
    top_path = Path(top_path) if top_path else None
    bottom_path = Path(bottom_path) if bottom_path else None
    accessory_path = Path(accessory_path) if accessory_path else None
    output_path = Path(output_path) if output_path else None

    if USE_REAL_VTON:
        # TODO:
        # 1. Load CatVTON/IDM-VTON model
        # 2. Pass mannequin image and retrieved clothing image
        # 3. Save generated image to output_path
        #
        # Keep fallback available so the web/API demo still works if model
        # dependencies or weights are missing during prototyping.
        try:
            raise NotImplementedError("Real VTON integration is not enabled in this MVP.")
        except Exception:
            return fallback_generate_image(
                mannequin_path=mannequin_path,
                top_path=top_path,
                bottom_path=bottom_path,
                accessory_path=accessory_path,
                output_path=output_path,
                prompt=prompt,
            )
    else:
        return fallback_generate_image(
            mannequin_path=mannequin_path,
            top_path=top_path,
            bottom_path=bottom_path,
            accessory_path=accessory_path,
            output_path=output_path,
            prompt=prompt,
        )
