#!/usr/bin/env python3
"""CPT reads Uncle · writes ack. Run after Uncle posts uncle_to_cpt.txt."""
from __future__ import annotations

import socket
from datetime import datetime, timezone
from pathlib import Path

from bus_lane import bus_root

BUS = bus_root()
UNCLE = BUS / "fleet/bus/uncle_to_cpt.txt"
ACK = BUS / "fleet/bus/cpt_ack_uncle.txt"
TO_UNCLE = BUS / "fleet/bus/cpt_to_uncle.txt"


def _now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def main() -> int:
    host = socket.gethostname()
    now = _now()
    uncle_text = ""
    if UNCLE.is_file():
        uncle_text = UNCLE.read_text(encoding="utf-8", errors="replace").strip()
    if uncle_text.strip().startswith(("WAITING —", "INVALIDATED")):
        uncle_text = ""

    if not uncle_text:
        ack = (
            f"CPT_ACK — {now}\n"
            f"from: Daddy on {host}\n"
            f"heard: NO uncle_to_cpt yet — waiting\n"
            f"uncle: write fleet/bus/uncle_to_cpt.txt from CB1 after exec\n"
        )
        ACK.parent.mkdir(parents=True, exist_ok=True)
        ACK.write_text(ack, encoding="utf-8")
        print(ack)
        return 1

    bad_box = "penguin" in uncle_text.lower() or "penguin bridge" in uncle_text.lower()
    cb1_ok = bool(__import__("re").search(r"UNCLE (CHECKIN|clean) — cb1", uncle_text, __import__("re").I | __import__("re").M))

    lines = [ln for ln in uncle_text.splitlines() if ln.strip()]
    summary = lines[-1] if lines else "(empty)"
    preview = "\n".join(lines[-8:])

    if bad_box or not cb1_ok:
        ack = (
            f"CPT_ACK — {now}\n"
        f"from: Daddy on {host}\n"
        f"heard: NO — wrong box (penguin is Daddy · not Uncle)\n"
        f"linked: NO · roll stays low until Uncle posts from CB1\n"
        f"uncle_last: {summary[:120]}\n"
        f"loop: NOT LIVE — Uncle runs uncle_exec on CB1 only\n"
        f"gem: read drop_pile/to_gemini/GEM_SELF_FIX.txt\n"
        f"law: fleet/NAMING_LAW.txt\n"
            f"\n"
            f"--- uncle tail (rejected) ---\n"
            f"{preview}\n"
            f"--- end ---\n"
        )
        ACK.parent.mkdir(parents=True, exist_ok=True)
        ACK.write_text(ack, encoding="utf-8")
        print(ack)
        print(f"→ {ACK}")
        return 2

    ack = (
        f"CPT_ACK — {now}\n"
        f"from: Daddy on {host}\n"
        f"heard: YES · CB1 confirmed\n"
        f"linked: YES · UNCLE ✓ on fleet bar\n"
        f"uncle_last: {summary[:120]}\n"
        f"loop: TWO_WAY_LIVE\n"
        f"law: fleet/CPT_UNCLE_LOOP.txt\n"
        f"\n"
        f"--- uncle tail ---\n"
        f"{preview}\n"
        f"--- end ---\n"
    )
    ACK.parent.mkdir(parents=True, exist_ok=True)
    ACK.write_text(ack, encoding="utf-8")
    print(ack)
    print(f"→ {ACK}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
