#!/usr/bin/env python3
"""Lane guard — Daddy never writes Uncle/Gem outbox from penguin."""
from __future__ import annotations

import socket
import sys
from pathlib import Path

from bus_lane import bus_root, safe_mkdir

# Uncle box only — Daddy posts orders, never impersonates replies
UNCLE_BOX_LANES = frozenset(
    {
        "fleet/bus/uncle_to_cpt.txt",
        "fleet/bus/gem_to_cpt.txt",
        "fleet/bus/mac_outbox.txt",
    }
)


def fleet_box_id() -> str:
    p = Path.home() / ".stan" / "FLEET_BOX_ID"
    try:
        if p.is_file():
            return p.read_text(encoding="utf-8").strip().lower()
    except OSError:
        pass
    return ""


def is_daddy_lane() -> bool:
    fb = fleet_box_id()
    if fb == "cb1":
        return False
    if fb in ("daddy", "cb2"):
        return True
    h = socket.gethostname().lower()
    return h == "penguin" or "penguin" in h


def lane_write_allowed(rel: str) -> tuple[bool, str]:
    rel = rel.replace("\\", "/").lstrip("/")
    if rel in UNCLE_BOX_LANES and is_daddy_lane():
        return (
            False,
            f"REFUSE {rel} from Daddy lane — Uncle/Gem · set FLEET_BOX_ID=cb1 on CB1 · law fleet/NAMING_LAW.txt",
        )
    return True, ""


def safe_lane_write(rel: str, content: str, *, force: bool = False) -> Path:
    ok, reason = lane_write_allowed(rel)
    if not ok and not force:
        raise PermissionError(reason)
    path = bus_root() / rel
    safe_mkdir(path.parent)
    path.write_text(content, encoding="utf-8")
    return path


def main() -> int:
    if len(sys.argv) < 3:
        print("Usage: bus_lane_guard.py check <fleet/bus/path>", file=sys.stderr)
        print("       bus_lane_guard.py write <fleet/bus/path> < content", file=sys.stderr)
        return 1
    cmd, rel = sys.argv[1], sys.argv[2]
    if cmd == "check":
        ok, reason = lane_write_allowed(rel)
        print("OK" if ok else reason)
        return 0 if ok else 2
    if cmd == "write":
        ok, reason = lane_write_allowed(rel)
        if not ok:
            print(reason, file=sys.stderr)
            return 2
        safe_lane_write(rel, sys.stdin.read())
        print(f"→ {bus_root() / rel}")
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
