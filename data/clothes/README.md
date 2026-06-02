# Clothes Data

`metadata.json` stores clothing records used by the MVP retriever.

Run this from the project root to create sample PNG assets and metadata:

```bash
python scripts/build_sample_db.py
```

Each record uses this shape:

```json
{
  "id": "top_001",
  "category": "top",
  "image_path": "data/clothes/top_001.png",
  "tags": ["red", "hoodie", "casual"],
  "description": "red hoodie"
}
```

VITON-HD import records may point directly to files under `data/viton_hd/`:

```json
{
  "id": "viton_top_000001_00",
  "category": "top",
  "image_path": "data/viton_hd/test/cloth/000001_00.jpg",
  "tags": ["viton", "viton-hd", "cloth", "top", "shirt"],
  "manual_tags": [],
  "description": "VITON-HD top 000001_00",
  "source_dataset": "VITON-HD",
  "source_path": "data/viton_hd/test/cloth/000001_00.jpg",
  "needs_manual_tags": true
}
```

Use `manual_tags` for human-added labels such as color, pattern, or garment type.
