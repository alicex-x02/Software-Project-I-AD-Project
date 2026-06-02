from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[1]
DIRS = [
    PROJECT_DIR / "app",
    PROJECT_DIR / "web",
    PROJECT_DIR / "data" / "mannequins",
    PROJECT_DIR / "data" / "clothes",
    PROJECT_DIR / "data" / "person_refs",
    PROJECT_DIR / "data" / "viton_hd",
    PROJECT_DIR / "outputs",
    PROJECT_DIR / "scripts",
    PROJECT_DIR / "models",
]


def main() -> None:
    for directory in DIRS:
        directory.mkdir(parents=True, exist_ok=True)

    metadata_path = PROJECT_DIR / "data" / "clothes" / "metadata.json"
    if not metadata_path.exists():
        metadata_path.write_text("[]\n", encoding="utf-8")

    person_metadata_path = PROJECT_DIR / "data" / "person_refs" / "metadata.json"
    if not person_metadata_path.exists():
        person_metadata_path.write_text("[]\n", encoding="utf-8")

    print(f"Project directories are ready under {PROJECT_DIR}")


if __name__ == "__main__":
    main()
