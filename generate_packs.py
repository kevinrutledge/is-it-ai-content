#!/usr/bin/env python3
"""Regenerate packs.json with computed itemCount and sizeMb from disk."""

import json
from pathlib import Path

REPO_ROOT = Path(__file__).parent
PACKS_DIR = REPO_ROOT / "packs"
PACKS_JSON = REPO_ROOT / "packs.json"


def compute_pack_stats(pack_dir: Path) -> dict:
    manifest_path = pack_dir / "manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"No manifest.json in {pack_dir.name}")

    with open(manifest_path) as f:
        items = json.load(f)

    images_dir = pack_dir / "images"
    total_bytes = sum(f.stat().st_size for f in images_dir.iterdir() if f.is_file())
    size_mb = round(total_bytes / (1024 * 1024), 1)

    return {"itemCount": len(items), "sizeMb": size_mb}


def load_existing_metadata() -> dict[str, dict]:
    if not PACKS_JSON.exists():
        return {}
    with open(PACKS_JSON) as f:
        packs = json.load(f)
    return {pack["id"]: pack for pack in packs}


def generate():
    existing_metadata = load_existing_metadata()
    pack_dirs = sorted(d for d in PACKS_DIR.iterdir() if d.is_dir())

    packs = []
    for pack_dir in pack_dirs:
        manifest_path = pack_dir / "manifest.json"
        if not manifest_path.exists():
            continue

        pack_id = pack_dir.name
        stats = compute_pack_stats(pack_dir)
        existing = existing_metadata.get(pack_id, {})

        pack_entry = {
            "id": pack_id,
            "name": existing.get("name", pack_id),
            "description": existing.get("description", ""),
            "itemCount": stats["itemCount"],
            "sizeMb": stats["sizeMb"],
        }
        packs.append(pack_entry)

        status = "updated" if pack_id in existing_metadata else "new"
        print(f"  {pack_id}: {stats['itemCount']} items, {stats['sizeMb']} MB ({status})")

    with open(PACKS_JSON, "w") as f:
        json.dump(packs, f, indent=2)
        f.write("\n")

    print(f"\nWrote {len(packs)} pack(s) to packs.json")


if __name__ == "__main__":
    generate()
