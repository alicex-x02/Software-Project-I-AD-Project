# DressCode Data

DressCode is the preferred clothing source for lower-body and upper-body garment references in this MVP.

Official access is request-gated by the dataset maintainers, so the dataset is not auto-downloaded here.
If you have approved access, place the extracted dataset under this folder, for example:

```text
data/dresscode/
  upper_body/
    images/
    keypoints/
    label_maps/
    skeletons/
    train_pairs.txt
    test_pairs_paired.txt
    test_pairs_unpaired.txt
  lower_body/
    images/
    keypoints/
    label_maps/
    skeletons/
    train_pairs.txt
    test_pairs_paired.txt
    test_pairs_unpaired.txt
  dresses/
    images/
    keypoints/
    label_maps/
    skeletons/
    train_pairs.txt
    test_pairs_paired.txt
    test_pairs_unpaired.txt
```

After placing the data, run:

```bash
python scripts/check_dresscode.py
python scripts/import_dresscode_clothes.py --limit 80
```

The app will then prefer DressCode garments for `top` and `bottom` lookups.
