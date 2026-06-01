# Model Integration Notes

This MVP does not download or install heavy virtual try-on models. The API and web page remain usable through the Pillow fallback renderer.

Future integration candidates:

- CatVTON
- IDM-VTON
- Stable Diffusion Inpainting

Integration point:

- `app/image_generator.py`
- `run_virtual_tryon(mannequin_path, top_path, bottom_path, accessory_path, output_path, prompt)`

Suggested future flow:

1. Install model dependencies in a separate environment or optional requirements file.
2. Place model weights under `models/` or configure an external model path.
3. Set `USE_REAL_VTON = True` only after the model loader is implemented.
4. Keep `fallback_generate_image()` available so demos still work when model loading fails.
