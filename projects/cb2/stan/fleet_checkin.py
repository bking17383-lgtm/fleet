#!/usr/bin/env python3
"""Fleet check-in roll call — job + last ping per box.

  python3 ~/.stan/fleet_checkin.py once

Writes fleet/bus/FLEET_CHECKIN.txt (garage board · TV · /goal)
"""
from __future__ import annotations

import os
import re
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from bus_lane import bus_root, safe_is_file, safe_mkdir, safe_read_text, STAN

OUT = "fleet/bus/FLEET_CHECKIN.txt"
STALE_SEC = int(os.environ.get("FLEET_CHECKIN_STALE", "90"))
UNCLE_LINK_SEC = int(os.environ.get("UNCLE_LINK_SEC", "600"))
BUNNY_LINK_SEC = int(os.environ.get("BUNNY_LINK_SEC", "120"))
GEM_LINK_SEC = int(os.environ.get("GEM_LINK_SEC", "600"))
FLEET_BOXES = ("DADDY", "BUNNY", "CB1")


def _now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def _mtime_age(bus: Path, rel: str) -> tuple[str, float | None]:
    p = bus / rel
    if not safe_is_file(p):
        return "missing", None
    try:
        ts = datetime.fromtimestamp(p.stat().st_mtime, tz=timezone.utc)
        age = (datetime.now(timezone.utc) - ts).total_seconds()
        return ts.astimezone().isoformat(timespec="seconds"), age
    except OSError:
        return "err", None


def _tail(bus: Path, rel: str, n: int = 3) -> str:
    p = bus / rel
    if not safe_is_file(p):
        return "(missing)"
    lines = [ln.strip() for ln in safe_read_text(p).splitlines() if ln.strip()]
    return lines[-1][:90] if lines else "(empty)"


def _job_snip(bus: Path, rel: str, n: int = 2) -> str:
    p = bus / rel
    if not safe_is_file(p):
        return "(no orders file)"
    for ln in safe_read_text(p).splitlines():
        s = ln.strip()
        if s and not s.startswith("#") and not s.startswith("---") and len(s) > 8:
            if s.startswith("|") or s.startswith("━"):
                continue
            return s[:85]
    return "(read orders file)"


def _http(port: int) -> bool:
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/health", timeout=2) as r:
            return r.status == 200
    except OSError:
        return False


def _status(age: float | None, pattern_ok: bool = True) -> str:
    if age is None:
        return "MISSING"
    if age <= STALE_SEC and pattern_ok:
        return "CHECKED IN"
    if age <= STALE_SEC * 3:
        return "STALE"
    return "NO CHECK-IN"


def _status_link(age: float | None, pattern_ok: bool, link_sec: int) -> str:
    if age is None:
        return "MISSING"
    if age <= link_sec and pattern_ok:
        return "CHECKED IN"
    if age <= link_sec * 2:
        return "STALE"
    return "NO CHECK-IN"


def _bunny_live(text: str) -> bool:
    if not text.strip():
        return False
    low = text.lower()
    if text.strip() == "waiting for bunny":
        return False
    if "retired" in low or "dead word" in low:
        return False
    return bool(re.search(r"^FROM_BUNNY", text, re.I | re.M) or "from_bunny" in low)


def _bunny_lane(bus: Path) -> dict:
    ts, age = _mtime_age(bus, "fleet/indie_loop/FROM_BUNNY.txt")
    text = (
        safe_read_text(bus / "fleet/indie_loop/FROM_BUNNY.txt")
        if safe_is_file(bus / "fleet/indie_loop/FROM_BUNNY.txt")
        else ""
    )
    live = _bunny_live(text)
    bridged = "bridged-by" in text.lower()
    if live and age is not None and age <= BUNNY_LINK_SEC and not bridged:
        status = "CHECKED IN"
    elif live and age is not None and age <= BUNNY_LINK_SEC * 2:
        status = "STALE (bridged)" if bridged else "STALE"
    else:
        status = _status_link(age, live, BUNNY_LINK_SEC)
    return {
        "box": "BUNNY",
        "host": "Bunny (4GB builder · ex-puppy)",
        "job": _job_snip(bus, "fleet/indie_loop/TO_BUNNY.txt"),
        "orders": "fleet/indie_loop/TO_BUNNY.txt",
        "checkin": "fleet/indie_loop/FROM_BUNNY.txt",
        "last": ts,
        "age_s": int(age) if age is not None else None,
        "status": status,
        "tail": _tail(bus, "fleet/indie_loop/FROM_BUNNY.txt"),
    }


def _uncle_lane(bus: Path) -> dict:
    st_ts, st_age = _mtime_age(bus, "fleet/bus/uncle_to_cpt.txt")
    st_text = safe_read_text(bus / "fleet/bus/uncle_to_cpt.txt") if safe_is_file(bus / "fleet/bus/uncle_to_cpt.txt") else ""
    st_on_cb1 = "host=penguin" not in st_text.lower() and "penguin bridge" not in st_text.lower()
    st_pattern = bool(
        re.search(r"^UNCLE (clean|CHECKIN) —", st_text, re.I | re.M)
        or re.search(r"\nUNCLE (clean|CHECKIN) — cb1", st_text, re.I)
    ) and st_on_cb1 and "INVALIDATED" not in st_text
    if st_age is not None and st_age <= UNCLE_LINK_SEC and st_pattern:
        status = "CHECKED IN"
    else:
        status = _status_link(st_age, st_pattern, UNCLE_LINK_SEC)
    return {
        "box": "UNCLE",
        "host": "Uncle (CB1 Linux execute)",
        "job": _job_snip(bus, "fleet/bus/cpt_to_uncle.txt") or _job_snip(bus, "fleet/orders/CB1_ORDERS.txt"),
        "orders": "fleet/bus/cpt_to_uncle.txt",
        "checkin": "fleet/bus/uncle_to_cpt.txt",
        "last": st_ts,
        "age_s": int(st_age) if st_age is not None else None,
        "status": status,
        "tail": _tail(bus, "fleet/bus/uncle_to_cpt.txt"),
    }


def _gem_lane(bus: Path) -> dict:
    gem_ts, gem_age = _mtime_age(bus, "fleet/bus/gem_to_cpt.txt")
    gem_text = safe_read_text(bus / "fleet/bus/gem_to_cpt.txt") if safe_is_file(bus / "fleet/bus/gem_to_cpt.txt") else ""
    gem_on_cb1 = "penguin" not in gem_text.lower() and "INVALIDATED" not in gem_text
    gem_pattern = bool(
        re.search(r"^(GEM|BUDDY) (ok|REFUSE|—)", gem_text, re.I | re.M)
        or re.search(r"read ping", gem_text, re.I)
    ) and gem_on_cb1
    ack_text = safe_read_text(bus / "fleet/bus/cpt_ack_gem.txt") if safe_is_file(bus / "fleet/bus/cpt_ack_gem.txt") else ""
    ack_gem = "gem_heard: YES · CB1" in ack_text
    if gem_age is not None and gem_age <= GEM_LINK_SEC and gem_pattern:
        status = "CHECKED IN"
    elif ack_gem and gem_pattern and gem_age is not None and gem_age <= GEM_LINK_SEC * 2:
        status = "CHECKED IN"
    else:
        status = _status_link(gem_age, gem_pattern, GEM_LINK_SEC)
    return {
        "box": "CLERK",
        "host": "Clerk (CB1 Chrome · was Gem · plain .txt only)",
        "job": _job_snip(bus, "fleet/bus/cpt_to_gem.txt"),
        "orders": "fleet/bus/cpt_to_gem.txt",
        "checkin": "fleet/bus/gem_to_cpt.txt",
        "last": gem_ts,
        "age_s": int(gem_age) if gem_age is not None else None,
        "status": status,
        "tail": _tail(bus, "fleet/bus/gem_to_cpt.txt"),
    }


def roll_call() -> dict:
    bus = bus_root()
    now = _now()

    # CPT — self-check loop on CB2
    sc_ts, sc_age = _mtime_age(bus, "fleet/bus/FLEET_SELF_CHECK.txt")
    pulse_ts, pulse_age = _mtime_age(bus, "fleet/bus/SLAVE_PULSE.txt")
    cpt_age = min(a for a in (sc_age, pulse_age) if a is not None) if any(
        a is not None for a in (sc_age, pulse_age)
    ) else None
    cpt_ok = cpt_age is not None and cpt_age <= STALE_SEC
    desk = _http(8770)
    cpt_job = _job_snip(bus, "fleet/bus/CPT_DELEGATE_NOW.txt")

    bunny_row = _bunny_lane(bus)
    uncle_row = _uncle_lane(bus)
    clerk_row = _gem_lane(bus)

    rows = [
        {
            "box": "DADDY",
            "host": "Daddy (penguin)",
            "job": cpt_job,
            "orders": "fleet/bus/CPT_DELEGATE_NOW.txt",
            "checkin": "fleet/bus/FLEET_SELF_CHECK.txt",
            "last": sc_ts,
            "age_s": int(cpt_age) if cpt_age is not None else None,
            "status": "CHECKED IN" if cpt_ok and desk else ("SERVICES DOWN" if cpt_ok else _status(cpt_age)),
            "tail": _tail(bus, "fleet/bus/FLEET_SELF_CHECK.txt"),
        },
        bunny_row,
        uncle_row,
        clerk_row,
    ]

    # Roll = 3 machines · CB1 counts if Uncle OR Clerk checked in (one hat at a time)
    cb1_in = uncle_row["status"] == "CHECKED IN" or clerk_row["status"] == "CHECKED IN"
    n_in = sum(
        1
        for r in (rows[0], bunny_row)
        if r["status"] == "CHECKED IN"
    ) + (1 if cb1_in else 0)
    n_total = 3
    n_in = min(n_in, n_total)

    lines = [
        f"FLEET CHECK-IN — {now}",
        f"roll={n_in}/{n_total} machines · CB1 one hat OK (Uncle OR Clerk) · dead: DOG PUPPY lane",
        "",
        "HOW TO READ (Brian walking garage)",
        "  ✓ CHECKED IN = job on bus + fresh ping",
        "  ~ STALE = file old or wrong format",
        "  ✗ MISSING / NO CHECK-IN = box silent",
        "",
        "ONE GLANCE: /tv or /checkin on phone · this file on Drive",
        "",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
    ]
    for r in rows:
        age = f"{r['age_s']}s ago" if r["age_s"] is not None else "never"
        mark = "✓" if r["status"] == "CHECKED IN" else ("~" if "STALE" in r["status"] else "✗")
        lines.extend([
            f"{mark} {r['box']} ({r['host']}) — {r['status']}",
            f"   job: {r['job']}",
            f"   orders: {r['orders']}",
            f"   checkin: {r['checkin']} · last {age}",
            f"   tail: {r['tail']}",
            "",
        ])

    lines.extend([
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        "CHECK-IN LINES (copy format)",
        "  DADDY:  auto · fleet_self_check.py watch 25",
        "  BUNNY:  FROM_BUNNY — <host> — <time>  (native loop · not bridged-by-cb1)",
        "  UNCLE:  UNCLE CHECKIN — cb1 — <ip> — <time>  (Linux · not penguin)",
        "  CLERK:  CLERK ok — <job> — <time> · host: cb1  (was gem_to_cpt)",
        "",
        "DEAD WORDS: DOG · PUPPY lane · read fleet/DEAD_WORDS.txt",
        "",
        f"CPT services (penguin local): mesh={'OK' if _http(8765) else 'DOWN'} sarah={'OK' if _http(8766) else 'DOWN'} desk={'OK' if desk else 'DOWN'}",
        f"(NET execute on CB1 — read fleet/bus/NET_STATUS.txt for honest ports)",
    ])

    text = "\n".join(lines) + "\n"
    out = bus / OUT
    safe_mkdir(out.parent)
    out.write_text(text, encoding="utf-8")
    return {"now": now, "roll": f"{n_in}/{n_total}", "rows": rows, "text": text}


def main() -> int:
    r = roll_call()
    print(r["text"])
    print(f"→ {bus_root() / OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
