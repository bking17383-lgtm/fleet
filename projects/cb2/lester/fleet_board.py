#!/usr/bin/env python3
"""Refresh MyDrive/fleet/FLEET_AVAILABLE.txt from Drive heartbeats (honest counts)."""
from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

FLEET = (
    {"machine": "cb1", "callsign": "WRANGLER", "ack": "lester6_to_uncle.md", "hb": "cb1_heartbeat.md"},
    {"machine": "cb2", "callsign": "BEACON", "ack": "lester6_to_daddy.md", "hb": "cb2_heartbeat.md"},
    {"machine": "puppy64", "callsign": "PLATE", "ack": "lester6_to_puppy.md", "hb": "puppy_heartbeat.md"},
)

PHONES = (
    {
        "fleet_id": "phone-moto-lte",
        "label": "Moto Play",
        "callsign": "ROVER",
        "network": "cellular",
        "ack": "lester6_to_rover.md",
        "hb": "rover_heartbeat.md",
    },
    {
        "fleet_id": "phone-samsung-wifi",
        "label": "Samsung",
        "callsign": "TESTER",
        "network": "wifi-only",
        "ack": "lester6_to_tester.md",
        "hb": "samsung_heartbeat.md",
    },
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
    m = re.search(r"time:\s*[\"']?([^\"'\s]+)", text)
    if not m:
        return None
    raw = m.group(1).strip("\"'")
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
    if "cursor: pending" in low or "lester6: awaiting" in low:
        return True
    if "paired: no" in low and "cursor: live" not in low:
        return True
    return False


def _ack_interim(text: str) -> bool:
    low = text.lower()
    return "interim" in low or "chrome must confirm" in low


def slave_ok(ack: Path, hb: Path, callsign: str) -> bool:
    t, h = read_text(ack), read_text(hb)
    if not t or "mode:" not in t.lower():
        return False
    if callsign.lower() not in t.lower():
        return False
    if _ack_interim(t):
        return False
    if not h or not _hb_fresh(h, max_hours=24.0):
        return False
    return callsign.lower() in h.lower() or "lester6: online" in h.lower()


def linked_ok(hb: Path, machine: str) -> bool:
    h = read_text(hb)
    if not h or "heartbeat" not in h.lower() or len(h) < 60 or not _hb_fresh(h) or _hb_down(h):
        return False
    if machine == "puppy64":
        ob = drive_root() / "fleet/bus/puppy_outbox.txt"
        if ob.is_file() and "hostname: penguin" in read_text(ob).lower():
            return False
    return True


def machine_status(machine: str, callsign: str, ack: Path, hb: Path) -> str:
    h = read_text(hb)
    if linked_ok(hb, machine) and slave_ok(ack, hb, callsign):
        return "WORKING"
    if linked_ok(hb, machine):
        return "PARTIAL"
    return "DOWN"


def phone_status(row: dict) -> str:
    base = drive_root() / "drop_pile/from_lester"
    ack = base / row["ack"]
    hb = base / row["hb"]
    h = read_text(hb)
    if not h or row["fleet_id"] not in h or not _hb_fresh(h, max_hours=24.0):
        return "DOWN"
    if slave_ok(ack, hb, row["callsign"]):
        return "WORKING"
    return "PARTIAL"


def main() -> None:
    root = drive_root()
    base = root / "drop_pile/from_lester"
    now = datetime.now().astimezone().isoformat()
    host = __import__("os").uname().nodename

    rows = []
    for row in FLEET:
        ack = base / row["ack"]
        hb = base / row["hb"]
        st = machine_status(row["machine"], row["callsign"], ack, hb)
        rows.append((row["machine"], row["callsign"], st, read_text(hb)[:80].replace("\n", " ")))

    cb1, cb2, pup = rows[0][2], rows[1][2], rows[2][2]
    sym = {"WORKING": "✓", "PARTIAL": "~", "DOWN": "✗"}

    phone_rows = []
    for ph in PHONES:
        st = phone_status(ph)
        phone_rows.append((ph["fleet_id"], ph["label"], ph["callsign"], ph["network"], st))

    moto_st, sam_st = phone_rows[0][4], phone_rows[1][4]

    # services on this host if CB2
    baseball = "UP" if Path("/proc").exists() else "?"
    try:
        import urllib.request

        urllib.request.urlopen("http://127.0.0.1:8002/api/health", timeout=2)
        baseball = "UP"
    except Exception:
        baseball = "DOWN"
    try:
        import urllib.request

        urllib.request.urlopen("http://127.0.0.1:8765/status", timeout=2)
        radio = "UP"
    except Exception:
        radio = "DOWN"

    compact = (
        f"CB1{sym.get(cb1,'?')} CB2{sym.get(cb2,'?')} puppy64{sym.get(pup,'?')} "
        f"moto{sym.get(moto_st,'?')} samsung{sym.get(sam_st,'?')}"
    )
    working = sum(1 for r in rows if r[2] == "WORKING") + sum(
        1 for r in phone_rows if r[4] == "WORKING"
    )
    partial = sum(1 for r in rows if r[2] == "PARTIAL") + sum(
        1 for r in phone_rows if r[4] == "PARTIAL"
    )
    down = sum(1 for r in rows if r[2] == "DOWN") + sum(1 for r in phone_rows if r[4] == "DOWN")

    text = f"""FLEET AVAILABLE — read this to design
Updated: {now}
Refreshed by: fleet_board.py on {host}

COMPUTERS (3 + Puppy host)
  CB1      {sym.get(cb1,'?')} {cb1:8}  WRANGLER + Uncle
  CB2      {sym.get(cb2,'?')} {cb2:8}  BEACON + CAPTN/Daddy
  puppy64  {sym.get(pup,'?')} {pup:8}  Puppy + PLATE

PHONES (2) — fleet_id is stable · see fleet/PHONE_FLEET_IDS.txt
  phone-moto-lte      {sym.get(moto_st,'?')} {moto_st:8}  ROVER   Moto Play · cellular · /rover
  phone-samsung-wifi  {sym.get(sam_st,'?')} {sam_st:8}  TESTER  Samsung · wifi/dongle only · /

AI AGENTS — see heartbeats in drop_pile/from_lester/

PARTS / SERVICES (CB2 host check)
  baseball :8002  {baseball}
  mesh radio :8765  {radio}
  Daddy public URL  fleet/DADDY_BASEBALL_URL.txt
  RADIO public URL  fleet/MESH_RADIO_URL.txt

DESIGN NOW
  Brian say DESK — honest board from heartbeats
  Uncle: bash ~/GoogleDrive/MyDrive/lester/install_uncle_stan.sh
  Puppy: drop_pile/to_puppy/UNCLE_LINUX_FIX.md

Compact: {compact} | {working} up · {partial} partial · {down} down
"""
    out = root / "fleet/FLEET_AVAILABLE.txt"
    out.write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
