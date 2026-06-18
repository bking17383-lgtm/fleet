#!/usr/bin/env python3
"""Cursor statusLine — honest check-in · 4 lanes · 3-machine roll."""
import json
import re
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

STAN = Path.home() / ".stan"
BUS = STAN / "fleet_bus"
DRIVE_CANDIDATES = [
    Path("/mnt/shared/GoogleDrive/MyDrive"),
    Path.home() / "GoogleDrive/MyDrive",
    BUS,
]
STALE_SEC = 90
MACHINE_TOTAL = 3
BOX_ALIASES = {
    "DADDY": ("DADDY", "CPT"),
    "PUPPY": ("PUPPY", "NET"),
    "UNCLE": ("UNCLE", "STUDIO"),
    "GEM": ("GEM", "BUDDY"),
}
FLEET_TAGS = ("DADDY", "PUPPY", "UNCLE", "GEM")


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


def _mtime_age(path: Path) -> float | None:
    try:
        if not path.is_file():
            return None
        ts = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
        return (datetime.now(timezone.utc) - ts).total_seconds()
    except OSError:
        return None


def _cpt_local_ok() -> bool:
    for port in (8765, 8766, 8770):
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{port}/health", timeout=0.8) as r:
                if r.status != 200:
                    return False
        except Exception:
            return False
    return True


def _puppy_ok(body: str) -> bool:
    if not body.strip():
        return False
    if "DADDY TEMP" in body or "Daddy holding" in body or "puppy64: ABSENT" in body.lower():
        return False
    return bool(re.search(r"^PUPPY CHECKIN — puppy64", body, re.I | re.M))


def _box_from_checkin(text: str, box: str) -> str:
    names = BOX_ALIASES.get(box, (box,))
    for line in text.splitlines():
        if not line.strip().startswith(("✓", "✗", "~")):
            continue
        if not any(n in line for n in names):
            continue
        if "CHECKED IN" in line:
            return "✓"
        if "STALE" in line:
            return "~"
        return "✗"
    return "✗"


def _machine_linked(tags: list[str]) -> int:
    ok = {t[:-1]: t.endswith("✓") for t in tags}
    cb1 = ok.get("UNCLE", False) or ok.get("GEM", False)
    return sum([ok.get("DADDY", False), ok.get("PUPPY", False), cb1])


def _fallback_counts() -> tuple[int, int, list[str]]:
    bus = bus_root()
    tags: list[str] = []
    checks = [
        ("DADDY", "FLEET_SELF_CHECK.txt", lambda: _cpt_local_ok()),
        ("PUPPY", "puppy_outbox.txt", lambda: False),
        ("UNCLE", "uncle_to_cpt.txt", lambda: False),
        ("GEM", "gem_to_cpt.txt", lambda: False),
    ]
    for name, rel, extra in checks:
        age = _mtime_age(bus / "fleet/bus" / rel)
        fresh = age is not None and age <= STALE_SEC
        ok = fresh and (extra() if name == "DADDY" else False)
        if name != "DADDY" and fresh:
            body = read_text(bus / "fleet/bus" / rel)
            if name == "PUPPY":
                ok = _puppy_ok(body)
            if name == "UNCLE" and re.search(r"^UNCLE (CHECKIN|clean) — cb1", body, re.I | re.M):
                if "penguin" not in body.lower():
                    ok = True
            if name == "GEM" and re.search(r"GEM (ok|REFUSE)|read ping", body, re.I):
                if "penguin" not in body.lower():
                    ok = True
        mark = "✓" if ok else ("~" if fresh else "✗")
        tags.append(f"{name}{mark}")
    linked = min(_machine_linked(tags), MACHINE_TOTAL)
    return linked, MACHINE_TOTAL, tags


def fleet_counts() -> tuple[int, int, list[str]]:
    bus = bus_root()
    checkin = read_text(bus / "fleet/bus/FLEET_CHECKIN.txt")
    if checkin.strip():
        m = re.search(r"roll=(\d+)/(\d+)", checkin)
        if m:
            linked = min(int(m.group(1)), int(m.group(2)))
            total = int(m.group(2))
            tags = [f"{box}{_box_from_checkin(checkin, box)}" for box in FLEET_TAGS]
            return linked, total, tags
    return _fallback_counts()


def fleet_line() -> str:
    linked, total, tags = fleet_counts()
    detail = " ".join(tags)
    return f"fleet {linked}/{total} check-in  {detail}"


def main() -> None:
    try:
        json.load(sys.stdin)
    except json.JSONDecodeError:
        pass

    fl = fleet_line()
    print(f"\033[32m{fl}\033[0m")
    print("\033[90mDaddy captain · bg watch · no spin\033[0m")


if __name__ == "__main__":
    main()
