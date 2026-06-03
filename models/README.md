# Models

This project uses `models/fashn_vton/` as the local cache for the optional real virtual try-on model.

Current behavior:

- The app first tries the FASHN VTON pipeline when `USE_REAL_VTON=1`.
- If model loading or inference fails, the app falls back to the PNG renderer.
- The cache directory is ignored by git because it can be large and is recreated on demand.
