# Generated Garments Cache

This folder stores cached clothing images generated from text prompts via the OpenAI API.

Behavior:

- The app hashes `category + description` to produce a stable cache filename.
- If the same clothing prompt is requested again, the cached PNG is reused.
- Generated garments are used as virtual try-on inputs before the VTON model runs.

Expected layout:

```text
data/generated_garments/
  index.json
  top/
    <hash>.png
  bottom/
    <hash>.png
    <hash>.png
```

This directory is ignored by git because it is runtime-generated cache data.
