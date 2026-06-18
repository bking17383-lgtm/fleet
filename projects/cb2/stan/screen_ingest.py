#!/usr/bin/env python3
"""Ingest a browser screen snap → eyes/inbox + held.png (does not expire)."""
from __future__ import annotations

import base64
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path

from bus_lane import STAN, bus_root, safe_mkdir

OUT_DIR = STAN / "screen"
LATEST = OUT_DIR / "latest.png"
HELD = OUT_DIR / "held.png"
MIN_BYTES = 12_000


def _ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def ingest_b64(raw: str, note: str = "show screen") -> dict:
    if not raw or not raw.startswith("data:image"):
        return {"ok": False, "error": "bad image data"}
    try:
        head, b64 = raw.split(",", 1)
    except ValueError:
        return {"ok": False, "error": "bad image format"}
    ext = "png"
    if "jpeg" in head or "jpg" in head:
        ext = "jpg"
    try:
        img = base64.b64decode(b64)
    except (ValueError, TypeError):
        return {"ok": False, "error": "decode failed"}
    if len(img) < MIN_BYTES:
        return {"ok": False, "error": f"image too small ({len(img)} bytes)"}

    bus = bus_root()
    eyes = bus / "eyes/inbox"
    safe_mkdir(eyes)
    safe_mkdir(OUT_DIR)

    name = f"eyes_SCREEN_{_ts()}.{ext}"
    eyes_path = eyes / name
    eyes_path.write_bytes(img)

    if ext == "png":
        shutil.copyfile(eyes_path, LATEST)
        shutil.copyfile(eyes_path, HELD)
    else:
        # store jpg as latest reference; held stays png name but jpg content ok for img tag
        held_jpg = OUT_DIR / "held.jpg"
        shutil.copyfile(eyes_path, held_jpg)
        shutil.copyfile(eyes_path, OUT_DIR / "latest.jpg")
        LATEST.write_bytes(img)  # overwrite latest.png path with jpg bytes — fix mimetype in route

    meta = bus / "fleet/bus/DADDY_SCREEN.txt"
    now = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
    lines = [
        f"DADDY SCREEN — {now}",
        "host=penguin · capture=OK · source=show_screen",
        f"held=yes · bytes={len(img)} · note={note[:80]}",
        f"eyes={eyes_path}",
        f"held={HELD if HELD.is_file() else OUT_DIR / 'held.jpg'}",
        "",
        "Brian: /screen SHOW SCREEN · held until next good snap",
        "Word: SCREEN",
    ]
    safe_mkdir(meta.parent)
    meta.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {"ok": True, "name": name, "bytes": len(img), "held": True}
