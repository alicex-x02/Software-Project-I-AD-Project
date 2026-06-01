import sys
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[1]
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from app.clothing_retriever import retrieve_best_clothing
from app.image_generator import run_virtual_tryon
from app.mannequin_selector import select_mannequin
from app.utils import output_path_for, resolve_project_path


def item_path(item):
    return resolve_project_path(item.get("image_path")) if item else None


def main() -> None:
    gender = "male"
    age_group = "elderly"
    top = "red checkered shirt"
    bottom = "black pants"
    accessory = "black backpack"

    mannequin_path = select_mannequin(gender, age_group)
    selected_top = retrieve_best_clothing(top, "top")
    selected_bottom = retrieve_best_clothing(bottom, "bottom")
    selected_accessory = retrieve_best_clothing(accessory, "accessory")

    output_path = output_path_for("pipeline_test_result")
    generated_path = run_virtual_tryon(
        mannequin_path=mannequin_path,
        top_path=item_path(selected_top),
        bottom_path=item_path(selected_bottom),
        accessory_path=item_path(selected_accessory),
        output_path=output_path,
        prompt={
            "gender": gender,
            "age_group": age_group,
            "top": top,
            "bottom": bottom,
            "accessory": accessory,
        },
    )

    if not generated_path.exists():
        raise RuntimeError(f"Expected output was not created: {generated_path}")

    print("Pipeline test succeeded")
    print(f"Mannequin: {mannequin_path}")
    print(f"Top: {selected_top['description'] if selected_top else None}")
    print(f"Bottom: {selected_bottom['description'] if selected_bottom else None}")
    print(f"Accessory: {selected_accessory['description'] if selected_accessory else None}")
    print(f"Output: {generated_path}")


if __name__ == "__main__":
    main()
