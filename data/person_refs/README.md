# Person References

`scripts/import_viton_persons.py` writes `metadata.json` here so the fallback PNG renderer can use real VITON-HD person/model images instead of dummy mannequin drawings.

By default, selected images are copied into `data/person_refs/viton/` and the original dataset path is kept in `source_path`.

Use `--no-copy` if you want metadata entries to point directly to images under `data/viton_hd/`.
