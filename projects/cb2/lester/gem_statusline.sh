#!/usr/bin/env python3
"""Cursor statusLine — CB1 · 4 lanes · honest · dog not puppy."""
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

STAN = Path.home() / ".stan"
BUS = STAN / "fleet_bus"
DRIVE_CANDIDATES = [
    Path("/mnt/shared/GoogleDrive/MyDrive"),
    Path("/mnt/home/google_drive/MyDrive"),
    Path.home() / "GoogleDrive/MyDrive",
    BUS,
]
STALE_SEC = 90
MACHINE_TOTAL = 3
FLEET_TAGS = ("DADDY", "DOG", "UNCLE", "GEM")
BOX_ALIASES = {
    "DADDY": ("DADDY", "CPT"),
    "DOG": ("DOG", "NET"),
    "UNCLE": ("UNCLE",),
    "GEM": ("GEM", "BUDDY"),
}


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


def _outbox_poison(body: str) -> bool:
    low = body.lower()
    if "uncle remote" in low or "from: uncle" in low:
        return True
    if "daddy temp" in low or "puppy64: absent" in low:
        return True
    if re.search(r"\bnet clean\b", body, re.I):
        return True
    return False


def _dog_ok(body: str, fresh: bool) -> bool:
    if not fresh or not body.strip() or _outbox_poison(body):
        return False
    return bool(re.search(r"^DOG CHECKIN —", body, re.I | re.M))


def _uncle_ok(body: str, fresh: bool) -> bool:
    if not fresh or not body.strip() or "penguin" in body.lower():
        return False
    return bool(re.search(r"^UNCLE (CHECKIN|LOOP|clean) — cb1", body, re.I | re.M))


def _gem_ok(body: str, fresh: bool) -> bool:
    if not fresh or not body.strip() or "penguin" in body.lower():
        return False
    return bool(
        re.search(r"^(GEM (→ CPT|ok|REFUSE|— LOOP)|BUDDY ok —)", body, re.I | re.M)
    )


def _daddy_ok(bus: Path) -> bool:
    checkin = read_text(bus / "fleet/bus/FLEET_CHECKIN.txt")
    for line in checkin.splitlines():
        if "DADDY" in line and "CHECKED IN" in line:
            return True
    age = _mtime_age(bus / "fleet/bus/FLEET_SELF_CHECK.txt")
    return age is not None and age <= STALE_SEC


def _box_from_checkin(text: str, box: str) -> str:
    names = BOX_ALIASES.get(box, (box,))
    for line in text.splitlines():
        if not line.strip().startswith(("✓", "✗", "~")):
            continue
        if not any(n in line for n in names):
            continue
        rest = line.upper()
        if "CHECKED IN" in rest:
            return "✓"
        if any(x in rest for x in ("STALE", "MOVED", "PARTIAL", "LOOP", "ABSENT", "NOT GREEN")):
            return "~"
        return "✗"
    return "✗"


def _machine_linked(tags: list[str]) -> int:
    ok = {t[:-1]: t.endswith("✓") for t in tags}
    cb1 = ok.get("UNCLE", False) or ok.get("GEM", False)
    return sum([ok.get("DADDY", False), ok.get("DOG", False), cb1])


def _fallback_counts() -> tuple[int, int, list[str]]:
    bus = bus_root()
    tags: list[str] = []
    specs = [
        ("DADDY", "FLEET_SELF_CHECK.txt", _daddy_ok, bus),
        ("DOG", "dog_outbox.txt", None, bus),
        ("UNCLE", "uncle_to_cpt.txt", None, bus),
        ("GEM", "gem_to_cpt.txt", None, bus),
    ]
    for name, rel, daddy_fn, root in specs:
        path = root / "fleet/bus" / rel
        age = _mtime_age(path)
        fresh = age is not None and age <= STALE_SEC
        body = read_text(path)
        if name == "DADDY":
            ok = daddy_fn(root) if daddy_fn else False
        elif name == "DOG":
            ok = _dog_ok(body, fresh)
        elif name == "UNCLE":
            ok = _uncle_ok(body, fresh)
        else:
            ok = _gem_ok(body, fresh)
        mark = "✓" if ok else ("~" if fresh else "✗")
        tags.append(f"{name}{mark}")
    linked = min(_machine_linked(tags), MACHINE_TOTAL)
    return linked, MACHINE_TOTAL, tags


def fleet_counts() -> tuple[int, int, list[str]]:
    bus = bus_root()
    checkin = read_text(bus / "fleet/bus/FLEET_CHECKIN.txt")
    if checkin.strip():
        tags = [f"{box}{_box_from_checkin(checkin, box)}" for box in FLEET_TAGS]
        linked = min(_machine_linked(tags), MACHINE_TOTAL)
        return linked, MACHINE_TOTAL, tags
    return _fallback_counts()


def fleet_line() -> str:
    linked, total, tags = fleet_counts()
    detail = " ".join(tags)
    return f"fleet {linked}/{total} machines · 4 lanes  {detail}"


def _color(linked: int, total: int) -> str:
    if linked >= total:
        return "\033[32m"
    if linked > 0:
        return "\033[33m"
    return "\033[31m"


def main() -> None:
    try:
        json.load(sys.stdin)
    except json.JSONDecodeError:
        pass
    linked, total, _ = fleet_counts()
    fl = fleet_line()
    print(f"{_color(linked, total)}{fl}\033[0m")
    print("\033[90mDaddy · Dog · Uncle · Gem — cb1 one hat · read FLEET_CHECKIN\033[0m")


if __name__ == "__main__":
    main()
