#!/usr/bin/env python3
"""Cursor statusLine — green fleet linked count below prompt (fresh fleet law)."""
import json
import re
import sys
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

STAN = Path.home() / ".stan"
BUS = STAN / "fleet_bus"
DRIVE_CANDIDATES = [
    Path("/mnt/shared/GoogleDrive/MyDrive"),
    Path.home() / "GoogleDrive/MyDrive",
    BUS,
]

BOXES = [
    ("CPT", "cb2", "SLAVE_PULSE.txt", "CPT_SLAVE"),
    ("NET", "puppy", "puppy_outbox.txt", "NET"),
    ("STUDIO", "cb1", "uncle_to_cpt.txt", "STUDIO"),
]


def bus_root() -> Path:
    for p in DRIVE_CANDIDATES:
        try:
            if (p / "fleet").is_dir():
                return p
        except OSError:
            continue
    return BUS


def read_text(path: Path) -> str:
    try:
        if path.is_file():
            return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        pass
    return ""


def _parse_ts(line: str) -> datetime | None:
    m = re.search(r"\[(\d{4}-\d{2}-\d{2}T[^\]]+)\]", line)
    if not m:
        return None
    try:
        return datetime.fromisoformat(m.group(1))
    except ValueError:
        return None


def _fresh(ts: datetime | None, hours: float = 12.0) -> bool:
    if not ts:
        return False
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    return datetime.now(timezone.utc) - ts.astimezone(timezone.utc) <= timedelta(hours=hours)


def _cpt_local_ok() -> bool:
    for port in (8765, 8766, 8770):
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{port}/health", timeout=0.8) as r:
                if r.status != 200:
                    return False
        except Exception:
            return False
    return True


def _box_status(name: str, bus_file: str, role: str) -> str:
    bus = bus_root()
    path = bus / "fleet/bus" / bus_file
    text = read_text(path)

    # STUDIO fallback: mac_outbox if uncle_to_cpt missing
    if name == "STUDIO" and not text.strip():
        text = read_text(bus / "fleet/bus/mac_outbox.txt")

    if name == "CPT":
        pulse = read_text(bus / "fleet/bus/SLAVE_PULSE.txt")
        for line in reversed(pulse.splitlines()):
            if "key_ok" in line and role in line:
                if _fresh(_parse_ts(line)):
                    return "✓" if _cpt_local_ok() else "~"
        return "✗"

    if name == "STUDIO":
        for line in text.splitlines():
            s = line.strip()
            if "post back" in s.lower() or s.startswith("#"):
                continue
            if re.match(r"UNCLE clean\s+—", s, re.I):
                return "✓"
            if re.match(r"(loop=TWO_WAY|aws_keys=READY)", s, re.I):
                return "✓"
        if read_text(bus / "fleet/bus/cpt_to_uncle.txt").strip():
            return "~"
        return "✗"

    if not text.strip():
        return "✗"

    low = text.lower()
    for line in text.splitlines():
        s = line.strip()
        if re.match(r"(NET|STUDIO) clean\s+—", s, re.I):
            return "✓"
    if re.search(r"key_ok host=", low) and role.lower() in low:
        return "✓"
    if re.search(r"clean|packed|alive", low) and "post back" not in low:
        return "~"
    return "✗"


def fleet_counts() -> tuple[int, int, list[str]]:
    tags: list[str] = []
    linked = 0
    for name, _machine, bus_file, role in BOXES:
        mark = _box_status(name, bus_file, role)
        tags.append(f"{name}{mark}")
        if mark == "✓":
            linked += 1
    return linked, len(BOXES), tags


def fleet_line() -> str:
    linked, total, tags = fleet_counts()
    detail = " ".join(tags)
    return f"fleet {linked}/{total} linked  {detail}"


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        print("\033[32mfleet ?/3 linked\033[0m")
        return

    model = (
        (payload.get("model") or {}).get("display_name_short")
        or (payload.get("model") or {}).get("display_name")
        or "cursor"
    )
    cw = payload.get("context_window") or {}
    pct = cw.get("used_percentage")
    ctx = f"{int(float(pct))}%" if pct is not None else "?"

    fl = fleet_line()
  # green fleet line — matches old CB1 footer style
    print(f"\033[32m{fl}\033[0m")
    print(f"\033[90m{model} ctx {ctx} · CPT captain · HOLD stops spin\033[0m")


if __name__ == "__main__":
    main()
