#!/usr/bin/env python3
"""Read Cursor statusLine JSON from stdin; print CB1-style footer + fleet counts."""
import json
import re
import sys
from datetime import datetime, timedelta, timezone
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


def _hb_time(text: str) -> datetime | None:
    m = re.search(r"time:\s*(\S+)", text)
    if not m:
        return None
    raw = m.group(1)
    try:
        return datetime.fromisoformat(raw)
    except ValueError:
        return None


def _hb_fresh(text: str, max_hours: float = 8.0) -> bool:
    ts = _hb_time(text)
    if not ts:
        return False
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    return datetime.now(timezone.utc) - ts.astimezone(timezone.utc) <= timedelta(hours=max_hours)


def _hb_down(text: str) -> bool:
    low = text.lower()
    down_markers = (
        "cursor: pending",
        "lester6: awaiting",
        "status: down",
        "status: dead",
        "status: offline",
        "paired: no",
    )
    if any(m in low for m in down_markers):
        # cb2 can be paired yes while captain tab is off — only block explicit pending/awaiting
        if "cursor: pending" in low or "lester6: awaiting" in low:
            return True
        if "paired: no" in low and "cursor: live" not in low:
            return True
    return False


def _ack_interim(text: str) -> bool:
    low = text.lower()
    return "interim" in low or "chrome must confirm" in low or "t3 interim" in low


def slave_bound(ack_path: Path, hb_path: Path, callsign: str) -> bool:
    text = read_text(ack_path)
    hb = read_text(hb_path)
    if not text or len(text) < 40:
        return False
    low = text.lower()
    if not ("mode: slave" in low and f"callsign: {callsign.lower()}" in low):
        return False
    if _ack_interim(text):
        return False
    if not hb or _hb_down(hb):
        return False
    if not _hb_fresh(hb):
        return False
    return callsign.lower() in hb.lower() or "lester6: online" in hb.lower()


def machine_linked(hb_path: Path, ack_path: Path, machine: str) -> bool:
    hb = read_text(hb_path)
    if not hb or "heartbeat" not in hb.lower() or len(hb) < 60:
        return False
    if not _hb_fresh(hb):
        return False
    if _hb_down(hb):
        return False
    if machine == "puppy64":
        outbox = drive_root() / "fleet/bus/puppy_outbox.txt"
        if outbox.is_file() and "hostname: penguin" in read_text(outbox).lower():
            return False
    return True


def fleet_counts() -> tuple[int, int, int, list[str]]:
    base = drive_root() / "drop_pile/from_lester"
    linked = slaves = 0
    tags: list[str] = []
    for row in FLEET:
        ack = base / row["ack"]
        hb = base / row["hb"]
        cs = row["callsign"]
        is_slave = slave_bound(ack, hb, cs)
        is_link = machine_linked(hb, ack, row["machine"])
        if is_link:
            linked += 1
        if is_slave:
            slaves += 1
        mark = "✓" if is_slave else ("~" if is_link else "✗")
        tags.append(f"{row['machine']}:{cs}{mark}")
    return linked, len(FLEET), slaves, tags


def fleet_line() -> str:
    linked, total, slaves, tags = fleet_counts()
    try:
        FLEET_JSON.write_text(
            json.dumps(
                {
                    "linked": linked,
                    "machines": total,
                    "slaves": slaves,
                    "ids": tags,
                    "updated": "live",
                },
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
    if SESSION.is_file():
        try:
            text = SESSION.read_text(encoding="utf-8", errors="replace")
            for line in text.splitlines():
                s = line.strip()
                if s.startswith("**Active program:**"):
                    return s.replace("**Active program:**", "", 1).strip()[:32]
                if s.startswith("**Project:**"):
                    return s.replace("**Project:**", "", 1).strip()[:32]
        except OSError:
            pass
    return "design_desk"


def gemini_ultra_line() -> str:
    if not GEMINI.is_file():
        return "gemini ~?"
    try:
        g = json.loads(GEMINI.read_text(encoding="utf-8"))
        used = float(g.get("used_units", 0) or 0)
        budget = float(g.get("daily_budget_units", 100) or 100)
        if budget <= 0:
            budget = 100
        pct = min(100, int(used * 100 / budget))
        plan = (g.get("plan") or "ultra").strip()
        return f"gemini {plan} ~{pct}%"
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
    if pct is not None:
        ctx = f"{int(float(pct))}%"
        inp = cw.get("total_input_tokens")
        if inp:
            ctx = f"{ctx} ({int(inp)//1000}k)"
    else:
        ctx = "?"

    proj = project_label()
    fl = fleet_line()
    gem = gemini_ultra_line()
    print(
        f"\033[90mshow\033[0m  \033[36m{proj}\033[0m  |  "
        f"\033[32m{fl}\033[0m  |  "
        f"\033[33m{model}\033[0m ctx {ctx}  |  "
        f"\033[35m{gem}\033[0m"
    )


if __name__ == "__main__":
    main()
