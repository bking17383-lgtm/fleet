#!/usr/bin/env python3
"""Story Mine Phase 0 — inventory gdoc stubs on Drive mount (names + dates only).

Linux cannot read gdoc bodies. This scans the filesystem mount for .gdoc stubs
and builds story_index.json for the design helper.

Run on puppy64 or CB2 when Drive is synced:
  python3 story_inventory.py

Full export requires Drive API or Apps Script (Phase 1).
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

DRIVE = Path("/mnt/shared/GoogleDrive/MyDrive")
if not DRIVE.is_dir():
    DRIVE = Path.home() / "GoogleDrive/MyDrive"

MANIFEST = DRIVE / "gl/story_mine_manifest.json"
OUT_DIR = DRIVE / "stories_export/catalog"
OUT_FILE = OUT_DIR / "story_index.json"


def load_manifest() -> dict:
    if MANIFEST.is_file():
        return json.loads(MANIFEST.read_text(encoding="utf-8"))
    return {}


def slugify(title: str) -> str:
    s = title.removesuffix(".gdoc").strip().lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")[:80] or "untitled"


def excluded(path: Path, name: str, manifest: dict) -> bool:
    rel = path.relative_to(DRIVE).as_posix()
    for prefix in manifest.get("exclude_path_prefixes", []):
        if rel.startswith(prefix):
            return True
    for sub in manifest.get("exclude_gdoc_name_contains", []):
        if sub.lower() in name.lower():
            return True
    if name in manifest.get("exclude_gdoc_name_exact", []):
        return True
    return False


def scan(manifest: dict) -> list[dict]:
    entries: list[dict] = []
    roots = [DRIVE]
    for folder in manifest.get("include_folders", []):
        p = DRIVE / folder
        if p.is_dir():
            roots.append(p)

    seen: set[str] = set()
    for root in roots:
        if root == DRIVE and not manifest.get("include_root_gdocs", True):
            continue
        glob_root = root if root != DRIVE else DRIVE
        max_depth = 1 if root == DRIVE else 10
        for path in glob_root.rglob("*.gdoc"):
            try:
                rel_parts = path.relative_to(DRIVE).parts
            except ValueError:
                continue
            if root == DRIVE and len(rel_parts) > 1:
                continue
            if root == DRIVE and len(rel_parts) == 1 and excluded(path, path.name, manifest):
                continue
            if root != DRIVE and excluded(path, path.name, manifest):
                continue
            key = path.name.lower()
            if key in seen:
                continue
            seen.add(key)
            st = path.stat()
            modified = datetime.fromtimestamp(st.st_mtime, tz=timezone.utc).isoformat()
            title = path.name.removesuffix(".gdoc")
            entries.append(
                {
                    "id": slugify(path.name),
                    "title": title,
                    "source_gdoc": path.relative_to(DRIVE).as_posix(),
                    "export_md": f"stories_export/raw/{slugify(path.name)}.md",
                    "modified": modified,
                    "word_count": None,
                    "exported": False,
                    "era": "legacy" if st.st_mtime < datetime(2020, 1, 1, tzinfo=timezone.utc).timestamp() else "2019-2025",
                    "tags": [],
                    "game_signals": {"mechanic_hint": "unknown"},
                }
            )
    entries.sort(key=lambda e: e["title"].lower())
    return entries


def main() -> None:
    manifest = load_manifest()
    entries = scan(manifest)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "updated": datetime.now(timezone.utc).isoformat(),
        "account": manifest.get("account", "tpgoround@gmail.com"),
        "phase": 0,
        "note": "Inventory from gdoc stubs only — bodies require Phase 1 export",
        "count": len(entries),
        "entries": entries,
    }
    OUT_FILE.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {len(entries)} entries → {OUT_FILE}")


if __name__ == "__main__":
    main()
