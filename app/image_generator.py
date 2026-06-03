import os
import tempfile
import threading
from pathlib import Path
from typing import Dict, Optional

from PIL import Image, ImageDraw, ImageFont

from app.config import MODELS_DIR, OUTPUT_DIR


USE_REAL_VTON = os.getenv("USE_REAL_VTON", "1").lower() not in {"0", "false", "no", "off"}
REAL_VTON_MODEL_ID = os.getenv("VTON_MODEL_ID", "fashn-ai/fashn-vton-1.5")
REAL_VTON_WEIGHTS_DIR = MODELS_DIR / "fashn_vton"

_REAL_VTON_PIPELINE = None
_REAL_VTON_PIPELINE_ERROR: Optional[Exception] = None
_REAL_VTON_LOCK = threading.Lock()


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


def _has_real_vton_assets() -> bool:
    return True


def _prepare_model_image(image_path: Optional[Path], size: tuple[int, int] = (768, 1024)) -> Optional[Image.Image]:
    if not image_path:
        return None

    path = Path(image_path)
    if not path.exists():
        return None

    try:
        image = Image.open(path).convert("RGBA")
    except OSError:
        return None

    canvas = Image.new("RGBA", size, (255, 255, 255, 255))
    image.thumbnail(size, Image.Resampling.LANCZOS)
    x = (size[0] - image.width) // 2
    y = (size[1] - image.height) // 2
    canvas.alpha_composite(image, (x, y))
    return canvas.convert("RGB")


def _prepare_garment_image(image_path: Optional[Path], size: tuple[int, int] = (768, 1024)) -> Optional[Image.Image]:
    if not image_path:
        return None

    path = Path(image_path)
    if not path.exists():
        return None

    try:
        image = Image.open(path).convert("RGB")
    except OSError:
        return None

    canvas = Image.new("RGB", size, (255, 255, 255))
    image.thumbnail((size[0] // 2, size[1] // 2), Image.Resampling.LANCZOS)
    x = (size[0] - image.width) // 2
    y = (size[1] - image.height) // 2
    canvas.paste(image, (x, y))
    return canvas


def _combine_tryon_images(top_image: Image.Image, bottom_image: Optional[Image.Image] = None) -> Image.Image:
    if bottom_image is None:
        return top_image

    top_rgba = top_image.convert("RGBA")
    bottom_rgba = bottom_image.convert("RGBA").resize(top_rgba.size, Image.Resampling.LANCZOS)
    width, height = top_rgba.size

    waist = int(height * 0.58)
    feather = max(28, int(height * 0.06))
    lower_start = max(0, waist - feather)

    final = top_rgba.copy()

    lower_crop = bottom_rgba.crop((0, lower_start, width, height))
    crop_height = lower_crop.height
    if crop_height <= 0:
        return top_rgba

    mask = Image.new("L", (width, crop_height), 0)
    mask_draw = ImageDraw.Draw(mask)
    fade_start = max(0, int(crop_height * 0.08))
    fade_end = max(fade_start + 1, int(crop_height * 0.18))
    body_start = max(0, int(crop_height * 0.18))
    mask_draw.rectangle((0, body_start, width, crop_height), fill=255)
    mask_draw.rectangle((0, fade_start, width, fade_end), fill=160)

    final.paste(lower_crop, (0, lower_start), mask)
    return final


def _download_fashn_weights(weights_dir: Path) -> None:
    from huggingface_hub import hf_hub_download

    weights_dir.mkdir(parents=True, exist_ok=True)
    model_path = weights_dir / "model.safetensors"
    dwpose_dir = weights_dir / "dwpose"
    dwpose_dir.mkdir(parents=True, exist_ok=True)

    if not model_path.exists():
        hf_hub_download(
            repo_id=REAL_VTON_MODEL_ID,
            filename="model.safetensors",
            local_dir=str(weights_dir),
            local_dir_use_symlinks=False,
        )

    for filename in ("yolox_l.onnx", "dw-ll_ucoco_384.onnx"):
        target = dwpose_dir / filename
        if not target.exists():
            hf_hub_download(
                repo_id="fashn-ai/DWPose",
                filename=filename,
                local_dir=str(dwpose_dir),
                local_dir_use_symlinks=False,
            )


def _load_real_vton_pipeline():
    global _REAL_VTON_PIPELINE, _REAL_VTON_PIPELINE_ERROR

    if _REAL_VTON_PIPELINE is not None:
        return _REAL_VTON_PIPELINE

    if _REAL_VTON_PIPELINE_ERROR is not None:
        raise _REAL_VTON_PIPELINE_ERROR

    with _REAL_VTON_LOCK:
        if _REAL_VTON_PIPELINE is not None:
            return _REAL_VTON_PIPELINE
        if _REAL_VTON_PIPELINE_ERROR is not None:
            raise _REAL_VTON_PIPELINE_ERROR

        try:
            from fashn_vton import TryOnPipeline
        except Exception as exc:  # pragma: no cover - dependency fallback
            _REAL_VTON_PIPELINE_ERROR = exc
            raise

        try:
            _download_fashn_weights(REAL_VTON_WEIGHTS_DIR)
            pipe = TryOnPipeline(weights_dir=str(REAL_VTON_WEIGHTS_DIR))
            _REAL_VTON_PIPELINE = pipe
            return pipe
        except Exception as exc:
            _REAL_VTON_PIPELINE_ERROR = exc
            raise


def _run_real_vton(
    mannequin_path: Optional[Path],
    top_path: Optional[Path] = None,
    bottom_path: Optional[Path] = None,
    accessory_path: Optional[Path] = None,
    output_path: Optional[Path] = None,
    prompt: Optional[Dict] = None,
) -> Optional[Path]:
    if not _has_real_vton_assets():
        return None

    pipe = _load_real_vton_pipeline()
    input_image = _prepare_model_image(mannequin_path)
    if input_image is None:
        return None

    garment_jobs: list[tuple[Path, str]] = []
    if top_path and Path(top_path).exists():
        garment_jobs.append((Path(top_path), "tops"))
    if bottom_path and Path(bottom_path).exists():
        garment_jobs.append((Path(bottom_path), "bottoms"))
    if not garment_jobs and accessory_path and Path(accessory_path).exists():
        garment_jobs.append((Path(accessory_path), "tops"))

    if not garment_jobs:
        return None

    try:
        with __import__("torch").inference_mode():
            generated_images: list[Optional[Image.Image]] = []
            for garment_source, garment_category in garment_jobs:
                garment_image = _prepare_garment_image(garment_source)
                if garment_image is None:
                    generated_images.append(None)
                    continue
                generated = pipe(
                    person_image=input_image,
                    garment_image=garment_image,
                    category=garment_category,
                    garment_photo_type="model",
                    num_samples=1,
                    num_timesteps=28,
                    guidance_scale=1.5,
                    seed=42,
                    segmentation_free=True,
                )
                generated_images.append(generated.images[0] if hasattr(generated, "images") else None)

        valid_images = [img for img in generated_images if img is not None]
        if not valid_images:
            return None

        merged = _combine_tryon_images(valid_images[0], valid_images[1] if len(valid_images) > 1 else None)

        with tempfile.NamedTemporaryFile(suffix=".png", delete=False, dir=str(OUTPUT_DIR)) as tmp:
            temp_generated_path = Path(tmp.name)
        merged.save(temp_generated_path, "PNG")

        final_output = fallback_generate_image(
            mannequin_path=temp_generated_path,
            top_path=top_path,
            bottom_path=bottom_path,
            accessory_path=accessory_path,
            output_path=output_path,
            prompt=prompt,
        )
        try:
            temp_generated_path.unlink(missing_ok=True)
        except OSError:
            pass
        return final_output
    except Exception:
        return None


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
        generated = _run_real_vton(
            mannequin_path=mannequin_path,
            top_path=top_path,
            bottom_path=bottom_path,
            accessory_path=accessory_path,
            output_path=output_path,
            prompt=prompt,
        )
        if generated is not None and generated.exists():
            return generated

    return fallback_generate_image(
        mannequin_path=mannequin_path,
        top_path=top_path,
        bottom_path=bottom_path,
        accessory_path=accessory_path,
        output_path=output_path,
        prompt=prompt,
    )
