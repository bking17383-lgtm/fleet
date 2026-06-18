#!/usr/bin/env python3
"""Brian sees VITAL only — not CPT noise."""
from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path

DRIVE = Path("/mnt/shared/GoogleDrive/MyDrive")
OUT = DRIVE / "fleet/bus/BRIAN_VITAL.txt"
PENDING = DRIVE / "fleet/bus/CPT_PENDING.txt"
INBOX = DRIVE / "fleet/bus/BRIAN_INBOX.txt"
SCAN = DRIVE / "fleet/bus/FLEET_SCAN.txt"

MARKER = "--- TYPE BELOW (one line) ---"


def _tail(path: Path, n: int = 5) -> list[str]:
    if not path.is_file():
        return []
    return [ln.strip() for ln in path.read_text(encoding="utf-8", errors="replace").splitlines() if ln.strip()][-n:]


def _inbox_line() -> str | None:
    if not INBOX.is_file():
        return None
    text = INBOX.read_text(encoding="utf-8", errors="replace")
    if MARKER not in text:
        return None
    below = text.split(MARKER, 1)[1].strip()
    for ln in below.splitlines():
        s = ln.strip()
        if s and not s.startswith("#"):
            return s
    return None


def main() -> None:
    now = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
    vital: list[str] = []

    inbox = _inbox_line()
    if inbox:
        vital.append(f"ACTION: Brian typed → {inbox[:120]}")

    for label, path in [
        ("puppy", DRIVE / "fleet/bus/puppy_outbox.txt"),
        ("studio", DRIVE / "fleet/bus/mac_outbox.txt"),
    ]:
        for ln in _tail(path, 2):
            if "Lester loop" in ln or "PUPPY_ONE_COMMAND" in ln or ln.startswith("--- from:"):
                continue
            if re.search(r"clean|PACKED|FAIL|DOWN|wipe|NET clean|STUDIO clean", ln, re.I):
                vital.append(f"{label.upper()}: {ln[:140]}")

    if PENDING.is_file():
        for ln in PENDING.read_text(encoding="utf-8", errors="replace").splitlines():
            if ln.startswith("|") and "Brian" in ln and "paste" in ln.lower():
                vital.append(f"NEED YOU: {ln.split('|')[2].strip()[:100]}")

    if not vital:
        vital.append("CLEAR: nothing needs Brian right now — CPT executing")

    lines = [
        f"BRIAN VITAL — {now}",
        "(read this only — ignore the rest)",
        "",
        *vital[:8],
        "",
        "One word: fleet/ONE_WORD.txt",
        "Start boot: fleet/START.txt",
    ]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(OUT)


if __name__ == "__main__":
    main()
