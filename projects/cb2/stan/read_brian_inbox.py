#!/usr/bin/env python3
"""Read Brian inbox — local always, Drive when mounted."""
from __future__ import annotations

import sys
from pathlib import Path

LOCAL = Path.home() / ".stan/BRIAN_INBOX_LOCAL.txt"
DRIVE_PATHS = [
    Path("/mnt/shared/GoogleDrive/MyDrive/fleet/bus/BRIAN_INBOX.txt"),
    Path("/mnt/home/google_drive/MyDrive/fleet/bus/BRIAN_INBOX.txt"),
    Path.home() / "GoogleDrive/MyDrive/fleet/bus/BRIAN_INBOX.txt",
]
MARKER = "--- TYPE BELOW (one line) ---"


def _read(path: Path) -> str | None:
    if not path.is_file():
        return None
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    if MARKER not in text:
        return None
    for ln in text.split(MARKER, 1)[1].splitlines():
        s = ln.strip()
        if s and not s.startswith("#"):
            return s
    return None


def main() -> None:
    line = _read(LOCAL)
    source = "local"
    for p in DRIVE_PATHS:
        try:
            if (d := _read(p)) and (not line or p.stat().st_mtime > LOCAL.stat().st_mtime):
                line, source = d, f"drive:{p.parent.parent.name}"
                break
        except OSError:
            continue
    if not line:
        print("INBOX EMPTY")
        return
    print(f"INBOX OK ({source}): {line}")


if __name__ == "__main__":
    main()
