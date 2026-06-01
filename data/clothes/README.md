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
