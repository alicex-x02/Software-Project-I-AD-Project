from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[1]
DIRS = [
    PROJECT_DIR / "app",
    PROJECT_DIR / "web",
    PROJECT_DIR / "data" / "mannequins",
    PROJECT_DIR / "data" / "generated_garments",
    PROJECT_DIR / "outputs",
    PROJECT_DIR / "scripts",
    PROJECT_DIR / "models",
]


def main() -> None:
    for directory in DIRS:
        directory.mkdir(parents=True, exist_ok=True)

    print(f"Project directories are ready under {PROJECT_DIR}")


if __name__ == "__main__":
    main()
