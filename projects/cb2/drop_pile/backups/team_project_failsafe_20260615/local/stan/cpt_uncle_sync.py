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
    if not uncle_text:
        ack = (
            f"CPT_ACK — {now}\n"
            f"from: CPT {host}\n"
            f"heard: NO uncle_to_cpt yet — waiting\n"
            f"uncle: write fleet/bus/uncle_to_cpt.txt after exec\n"
        )
        ACK.parent.mkdir(parents=True, exist_ok=True)
        ACK.write_text(ack, encoding="utf-8")
        print(ack)
        return 1

  # summary: first 500 chars + last line with UNCLE clean
    lines = [ln for ln in uncle_text.splitlines() if ln.strip()]
    summary = lines[-1] if lines else "(empty)"
    preview = "\n".join(lines[-8:])

    ack = (
        f"CPT_ACK — {now}\n"
        f"from: CPT {host}\n"
        f"heard: YES\n"
        f"uncle_last: {summary[:120]}\n"
        f"loop: TWO_WAY_LIVE\n"
        f"law: fleet/CPT_UNCLE_LOOP.txt\n"
        f"\n"
        f"--- uncle tail ---\n"
        f"{preview}\n"
        f"--- end ---\n"
        f"\n"
        f"CPT: control active · reading uncle_to_cpt · orders in cpt_to_uncle.txt\n"
    )
    ACK.parent.mkdir(parents=True, exist_ok=True)
    ACK.write_text(ack, encoding="utf-8")
    print(ack)
    print(f"→ {ACK}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
