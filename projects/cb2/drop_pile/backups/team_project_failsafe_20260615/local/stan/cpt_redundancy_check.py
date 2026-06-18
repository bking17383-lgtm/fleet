#!/usr/bin/env python3
"""Redundancy + worst-case probes. CPT runs without asking Brian."""
from __future__ import annotations

import json
import socket
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

DRIVE = Path("/mnt/shared/GoogleDrive/MyDrive")
OUT = DRIVE / "fleet/bus/REDUNDANCY.txt"
BACKUPS = DRIVE / "drop_pile/backups"

CHECKS = [
    ("drive", None),
    ("mesh", "http://127.0.0.1:8765/health"),
    ("sarah", "http://127.0.0.1:8766/health"),
    ("desk", "http://127.0.0.1:8770/health"),
]


def _http(url: str, ms: int = 4000) -> bool:
    try:
        with urllib.request.urlopen(url, timeout=ms / 1000) as r:
            return r.status == 200
    except Exception:
        return False


def main() -> None:
    now = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
    rows: list[str] = [f"REDUNDANCY — {now}", ""]

    ok = DRIVE.is_dir() and (DRIVE / "fleet").is_dir()
    rows.append(f"drive_mount: {'OK' if ok else 'FAIL'}")

    packs = list(BACKUPS.glob("pack_*")) if BACKUPS.is_dir() else []
    team = list(BACKUPS.glob("team_project_*")) if BACKUPS.is_dir() else []
    rows.append(f"backups: pack={len(packs)} team={len(team)}")

    for name, url in CHECKS[1:]:
        rows.append(f"{name}: {'OK' if url and _http(url) else 'DOWN'}")

    rows.extend([
        "",
        "worst_case:",
        "  CB2 dies → Drive + backups on Google · cloud CPT later",
        "  boys wiped → CLEAN_START.txt · CPT rebuild",
        "  1033 → fresh URL fleet/MESH_RADIO_URL.txt",
        "",
        "CPT may execute without Brian: fleet/CPT_EXECUTE.txt",
    ])
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(rows) + "\n", encoding="utf-8")
    print(OUT)


if __name__ == "__main__":
    main()
