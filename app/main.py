from pathlib import Path
from typing import Dict, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.clothing_retriever import retrieve_best_clothing
from app.config import BASE_DIR, OUTPUT_DIR, WEB_DIR, ensure_runtime_dirs
from app.image_generator import run_virtual_tryon
from app.mannequin_selector import select_mannequin
from app.schemas import GenerateRequest, GenerateResponse
from app.utils import output_path_for, project_relative, resolve_project_path


ensure_runtime_dirs()

app = FastAPI(
    title="Missing Person Outfit Visualization MVP",
    description="Simple FastAPI MVP for outfit visualization with a fallback PNG generator.",
    version="0.1.0",
)

app.mount("/static", StaticFiles(directory=WEB_DIR), name="static")


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "status": "error",
            "message": "Invalid request payload. Check gender, age_group, and text fields.",
            "detail": exc.errors(),
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "message": f"Image generation failed: {exc}",
        },
    )


@app.get("/")
def index():
    index_path = WEB_DIR / "index.html"
    if not index_path.exists():
        raise HTTPException(status_code=404, detail="web/index.html was not found.")
    return FileResponse(index_path)


def _selected_label(item: Optional[Dict]) -> Optional[str]:
    if not item:
        return None
    description = item.get("description") or item.get("id") or "unknown item"
    image_path = item.get("image_path")
    return f"{description} ({image_path})" if image_path else description


def _item_image_path(item: Optional[Dict]) -> Optional[Path]:
    if not item:
        return None
    return resolve_project_path(item.get("image_path"))


@app.post("/generate", response_model=GenerateResponse)
def generate(payload: GenerateRequest):
    output_path = output_path_for(payload.output_filename)
    mannequin_path = select_mannequin(payload.gender, payload.age_group)

    selected_top = retrieve_best_clothing(payload.top, "top") if payload.top.strip() else None
    selected_bottom = retrieve_best_clothing(payload.bottom, "bottom") if payload.bottom.strip() else None
    selected_accessory = retrieve_best_clothing(payload.accessory, "accessory") if payload.accessory.strip() else None

    prompt = {
        "gender": payload.gender,
        "age_group": payload.age_group,
        "top": payload.top,
        "bottom": payload.bottom,
        "accessory": payload.accessory,
    }

    generated_path = run_virtual_tryon(
        mannequin_path=mannequin_path,
        top_path=_item_image_path(selected_top),
        bottom_path=_item_image_path(selected_bottom),
        accessory_path=_item_image_path(selected_accessory),
        output_path=output_path,
        prompt=prompt,
    )

    image_url = f"/outputs/{generated_path.name}"
    return GenerateResponse(
        status="success",
        image_url=image_url,
        selected_mannequin=project_relative(mannequin_path) or str(mannequin_path),
        selected_clothes={
            "top": _selected_label(selected_top),
            "bottom": _selected_label(selected_bottom),
            "accessory": _selected_label(selected_accessory),
        },
        message="PNG generated successfully using the fallback MVP renderer.",
    )


@app.get("/outputs/{filename}")
def get_output(filename: str):
    requested_name = Path(filename).name
    if requested_name != filename or not requested_name.lower().endswith(".png"):
        raise HTTPException(status_code=400, detail="Only PNG files under outputs/ can be served.")

    output_path = (OUTPUT_DIR / requested_name).resolve()
    try:
        output_path.relative_to(BASE_DIR.resolve())
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid output path.")

    if not output_path.exists():
        raise HTTPException(status_code=404, detail="Output image was not found.")

    return FileResponse(output_path, media_type="image/png", filename=output_path.name)
