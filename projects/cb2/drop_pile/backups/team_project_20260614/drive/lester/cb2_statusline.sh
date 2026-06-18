#!/usr/bin/env python3
"""Read Cursor statusLine JSON from stdin; print CB1-style footer + fleet counts."""
import json
import sys
from pathlib import Path

STAN = Path.home() / ".stan" / "handoff"
SESSION = STAN / "session_note.md"
BRIEF = STAN / "brief.json"
GEMINI = STAN / "gemini_usage.json"
FLEET_JSON = STAN / "fleet_status.json"

FLEET = (
    {"machine": "cb1", "callsign": "WRANGLER", "ack": "lester6_to_uncle.md", "hb": "cb1_heartbeat.md"},
    {"machine": "cb2", "callsign": "BEACON", "ack": "lester6_to_daddy.md", "hb": "cb2_heartbeat.md"},
    {"machine": "puppy64", "callsign": "PLATE", "ack": "lester6_to_puppy.md", "hb": "puppy_heartbeat.md"},
)


def drive_root() -> Path:
    for p in (Path("/mnt/shared/GoogleDrive/MyDrive"), Path.home() / "GoogleDrive/MyDrive"):
        if p.is_dir():
            return p
    return Path.home() / "GoogleDrive/MyDrive"


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def slave_bound(ack_path: Path, callsign: str) -> bool:
    text = read_text(ack_path)
    if not text or len(text) < 40:
        return False
    low = text.lower()
    return "mode: slave" in low and f"callsign: {callsign.lower()}" in low


def machine_linked(hb_path: Path, ack_path: Path) -> bool:
    hb = read_text(hb_path)
    if hb and "heartbeat" in hb.lower() and len(hb) > 60:
        return True
    return ack_path.is_file() and len(read_text(ack_path)) > 40


def fleet_counts() -> tuple[int, int, int, list[str]]:
    base = drive_root() / "drop_pile/from_lester"
    linked = slaves = 0
    tags: list[str] = []
    for row in FLEET:
        ack = base / row["ack"]
        hb = base / row["hb"]
        cs = row["callsign"]
        is_slave = slave_bound(ack, cs)
        is_link = machine_linked(hb, ack)
        if is_link:
            linked += 1
        if is_slave:
            slaves += 1
        tags.append(f"{row['machine']}:{cs}" + ("✓" if is_slave else "—"))
    return linked, len(FLEET), slaves, tags


def fleet_line() -> str:
    linked, total, slaves, tags = fleet_counts()
    try:
        FLEET_JSON.write_text(
            json.dumps(
                {"linked": linked, "machines": total, "slaves": slaves, "ids": tags},
                indent=2,
            ),
            encoding="utf-8",
        )
    except OSError:
        pass
    return f"fleet {linked}/{total} linked · {slaves}/{total} slaves"


def project_label() -> str:
    if BRIEF.is_file():
        try:
            b = json.loads(BRIEF.read_text(encoding="utf-8"))
            for key in ("mode", "project", "active_project"):
                p = (b.get(key) or "").strip()
                if p:
                    return p[:32]
        except (json.JSONDecodeError, OSError):
            pass
    return "design_desk"


def gemini_ultra_line() -> str:
    if not GEMINI.is_file():
        return "gemini ~?"
    try:
        g = json.loads(GEMINI.read_text(encoding="utf-8"))
        used = float(g.get("used_units", 0) or 0)
        budget = float(g.get("daily_budget_units", 100) or 100)
        pct = min(100, int(used * 100 / (budget or 100)))
        return f"gemini ~{pct}%"
    except (json.JSONDecodeError, OSError, TypeError, ValueError):
        return "gemini ~?"


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        print("show  ?  |  fleet ?/?  |  cursor ?  |  gemini ?")
        return

    model = (
        (payload.get("model") or {}).get("display_name_short")
        or (payload.get("model") or {}).get("display_name")
        or "cursor"
    )
    cw = payload.get("context_window") or {}
    pct = cw.get("used_percentage")
    ctx = f"{int(float(pct))}%" if pct is not None else "?"
    proj = project_label()
    print(
        f"\033[90mshow\033[0m  \033[36m{proj}\033[0m  |  "
        f"\033[32m{fleet_line()}\033[0m  |  "
        f"\033[33m{model}\033[0m ctx {ctx}  |  "
        f"\033[35m{gemini_ultra_line()}\033[0m"
    )


if __name__ == "__main__":
    main()
