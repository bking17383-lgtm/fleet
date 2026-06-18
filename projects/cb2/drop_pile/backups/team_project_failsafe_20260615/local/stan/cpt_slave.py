#!/usr/bin/env python3
"""CPT slave — fast. One file. Vital for Brian + gaps for CPT."""
from __future__ import annotations

import re
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from bus_lane import bus_root, is_drive_live, LOCAL_INBOX, STAN, safe_is_file

MARKER = "--- TYPE BELOW (one line) ---"


def _bus_root() -> Path:
    return bus_root()


def _drive_live() -> bool:
    return is_drive_live()


def _http(url: str) -> bool:
    try:
        with urllib.request.urlopen(url, timeout=3) as r:
            return r.status == 200
    except Exception:
        return False


def _tail(path: Path, n: int = 3) -> list[str]:
    if not path.is_file():
        return []
    return [ln.strip() for ln in path.read_text(encoding="utf-8", errors="replace").splitlines() if ln.strip()][-n:]


def _inbox(drive_inbox: Path) -> str | None:
    for path in (LOCAL_INBOX, drive_inbox):
        try:
            if not path.is_file() or MARKER not in path.read_text(encoding="utf-8", errors="replace"):
                continue
            for ln in path.read_text(encoding="utf-8", errors="replace").split(MARKER, 1)[1].splitlines():
                s = ln.strip()
                if s and not s.startswith("#"):
                    return s
        except OSError:
            continue
    return None


def _box_signal(path: Path) -> str | None:
    for ln in reversed(_tail(path, 5)):
        if ln.startswith("--- from:") or "Lester loop" in ln:
            continue
        if re.search(r"clean|PACKED|ALIVE|FAIL|DOWN|wipe|pending", ln, re.I):
            return ln[:100]
    return None


def run() -> str:
    bus = _bus_root()
    live = _drive_live()
    out = bus / "fleet/bus/CPT_SLAVE.txt"
    vital_path = bus / "fleet/bus/BRIAN_VITAL.txt"
    inbox = bus / "fleet/bus/BRIAN_INBOX.txt"
    now = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
    vital: list[str] = []
    gaps: list[str] = []
    status: list[str] = []

    if msg := _inbox(inbox):
        vital.append(f"Brian said: {msg[:90]}")

    for name, path in [("NET", bus / "fleet/bus/puppy_outbox.txt"), ("STUDIO", bus / "fleet/bus/mac_outbox.txt")]:
        sig = _box_signal(path)
        if sig and re.search(r"clean|PACKED", sig, re.I):
            status.append(f"{name}: {sig}")
        elif sig:
            status.append(f"{name}: {sig}")
        else:
            gaps.append(f"{name}: no clean post yet — wiping?")

    pending = bus / "fleet/bus/CPT_PENDING.txt"
    if pending.is_file():
        for ln in pending.read_text(encoding="utf-8", errors="replace").splitlines():
            if not ln.startswith("|") or ln.startswith("| Task") or ln.startswith("|------"):
                continue
            cols = [c.strip() for c in ln.split("|") if c.strip()]
            if len(cols) < 2:
                continue
            task, who = (cols[0], cols[1]) if len(cols) == 2 else (cols[1], cols[2])
            if "Brian" in who:
                vital.append(f"NEED BRIAN: {task[:80]}")
            elif "NET" in who or "STUDIO" in who:
                gaps.append(f"{who}: {task[:70]}")

    svc = {
        "mesh": _http("http://127.0.0.1:8765/health"),
        "sarah": _http("http://127.0.0.1:8766/health"),
        "desk": _http("http://127.0.0.1:8770/health"),
    }
    down = [k for k, ok in svc.items() if not ok]
    if down:
        gaps.append(f"CPT restart: {', '.join(down)}")

    backups = bus / "drop_pile/backups"
    packs = len(list(backups.glob("pack_*"))) if backups.is_dir() else 0
    lane = "drive OK" if live else "LOCAL staging (Drive fuse down — slave still running)"
    status.append(f"CPT: {lane} · backups={packs} · " + " · ".join(f"{k}={'OK' if v else 'DOWN'}" for k, v in svc.items()))

    if not vital:
        vital.append("Nothing vital — CPT executing")

    gap_lines = [f"  • {g}" for g in gaps[:6]] or ["  • none"]
    inbox_local = LOCAL_INBOX
    snaps = len(list(inbox_local.glob("*"))) if inbox_local.is_dir() else 0
    if snaps:
        vital.append(f"Brian inbox: {snaps} file(s) in ~/.stan/local_inbox")

    stuck = bus / "fleet/STUCK_BOARD.txt"
    if safe_is_file(stuck):
        vital.append("STUCK board updated — read fleet/STUCK_BOARD.txt")

    lines = [
        f"CPT SLAVE — {now}",
        "",
        "VITAL",
        *[f"  • {v}" for v in vital[:5]],
        "",
        "BOXES",
        *[f"  • {s}" for s in status[:4]],
        "",
        "GAPS",
        *gap_lines,
        "",
        "Word: SLAVE (refresh) · CPT · NET · STUDIO",
    ]
    text = "\n".join(lines) + "\n"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")

    vital_only = [
        f"BRIAN VITAL — {now}",
        "",
        *[f"  • {v}" for v in vital[:5]],
        "",
        f"Full: {out.relative_to(bus) if out.is_relative_to(bus) else out}",
    ]
    vital_path.write_text("\n".join(vital_only) + "\n", encoding="utf-8")
    return text


def main() -> None:
    result = run().strip()
    print(result)
    bus = _bus_root()
    print(f"\n→ {bus / 'fleet/bus/CPT_SLAVE.txt'}")
    if not _drive_live():
        print("(local lane — will sync when Drive fuse returns)")


if __name__ == "__main__":
    main()
