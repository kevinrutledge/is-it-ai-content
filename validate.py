import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent
PACKS_DIR = REPO_ROOT / "packs"
PACKS_JSON = REPO_ROOT / "packs.json"
CONTENT_JSON = REPO_ROOT / "content.json"
REQUIRED_ITEM_FIELDS = {"id", "filename", "type"}
VALID_TYPES = {"ai", "real"}
errors = 0


def error(msg: str):
    global errors
    print(f"  ERROR: {msg}")
    errors += 1


def validate_content_json():
    print("Validating content.json...")
    if not CONTENT_JSON.exists():
        error("content.json not found")
        return
    try:
        items = json.loads(CONTENT_JSON.read_text())
    except json.JSONDecodeError as e:
        error(f"Invalid JSON: {e}")
        return
    if not isinstance(items, list):
        error("content.json must be an array")
        return
    for item in items:
        validate_item(item, REPO_ROOT)


def validate_item(item: dict, base_path: Path):
    missing = REQUIRED_ITEM_FIELDS - item.keys()
    if missing:
        error(f"Item missing fields {missing}: {item.get('id', '???')}")
        return
    if item["type"] not in VALID_TYPES:
        error(f"Invalid type '{item['type']}' for {item['id']}")
    image_path = base_path / item["filename"]
    if not image_path.exists():
        error(f"Image not found: {item['filename']} (referenced by {item['id']})")


def validate_packs_json():
    print("Validating packs.json...")
    if not PACKS_JSON.exists():
        error("packs.json not found")
        return []
    try:
        packs = json.loads(PACKS_JSON.read_text())
    except json.JSONDecodeError as e:
        error(f"Invalid JSON: {e}")
        return []
    if not isinstance(packs, list):
        error("packs.json must be an array")
        return []
    return packs


def validate_pack_directories(registered_packs: list):
    registered_ids = {p["id"] for p in registered_packs}
    actual_dirs = {d.name for d in PACKS_DIR.iterdir() if d.is_dir()} if PACKS_DIR.exists() else set()

    for pack_id in registered_ids - actual_dirs:
        error(f"Pack '{pack_id}' in packs.json but directory packs/{pack_id}/ not found")
    for pack_dir in actual_dirs - registered_ids:
        error(f"Directory packs/{pack_dir}/ exists but not listed in packs.json")


def validate_pack_manifests():
    print("Validating pack manifests...")
    if not PACKS_DIR.exists():
        return
    all_ids = set()
    for pack_dir in sorted(PACKS_DIR.iterdir()):
        if not pack_dir.is_dir():
            continue
        manifest_path = pack_dir / "manifest.json"
        if not manifest_path.exists():
            error(f"No manifest.json in packs/{pack_dir.name}/")
            continue
        try:
            items = json.loads(manifest_path.read_text())
        except json.JSONDecodeError as e:
            error(f"Invalid JSON in packs/{pack_dir.name}/manifest.json: {e}")
            continue
        if not isinstance(items, list):
            error(f"packs/{pack_dir.name}/manifest.json must be an array")
            continue

        manifest_filenames = set()
        for item in items:
            validate_item(item, pack_dir)
            if item.get("id") in all_ids:
                error(f"Duplicate item ID: {item['id']}")
            all_ids.add(item.get("id"))
            if "filename" in item:
                manifest_filenames.add(item["filename"])

        images_dir = pack_dir / "images"
        if images_dir.exists():
            actual_files = {f"images/{f.name}" for f in images_dir.iterdir() if f.is_file()}
            for orphan in actual_files - manifest_filenames:
                error(f"Image not referenced by manifest: packs/{pack_dir.name}/{orphan}")


def main():
    validate_content_json()
    registered_packs = validate_packs_json()
    validate_pack_directories(registered_packs)
    validate_pack_manifests()

    if errors == 0:
        print(f"\nAll checks passed.")
    else:
        print(f"\n{errors} error(s) found.")
    sys.exit(1 if errors > 0 else 0)


if __name__ == "__main__":
    main()
