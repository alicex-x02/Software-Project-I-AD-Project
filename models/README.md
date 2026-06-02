# Model Integration Notes

This project now connects to a real virtual try-on model by default:

- Active model: `fashn-ai/fashn-vton-1.5`
- Weight cache: `models/fashn_vton/`
- Integration point: `app/image_generator.py`

Runtime flow:

1. The app loads `FASHN VTON v1.5` through `fashn_vton.TryOnPipeline`.
2. If weights are missing, they are downloaded from Hugging Face on first use.
3. The model receives a person image plus a garment image and returns a try-on result.
4. The result is wrapped back into the existing PNG presentation layout.
5. If anything fails, the Pillow fallback renderer still generates a usable PNG.

Future model candidates remain:

- CatVTON
- IDM-VTON
- Stable Diffusion Inpainting
