#!/usr/bin/env python3
"""CPT fleet scan — fast. Replaces slow slave. Run on CB2."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

DRIVE = Path("/mnt/shared/GoogleDrive/MyDrive")
OUT = DRIVE / "fleet/bus/FLEET_SCAN.txt"
BACKUPS = DRIVE / "drop_pile/backups"


def main() -> None:
    now = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
    lines = [f"FLEET SCAN — {now}", ""]

    packs = sorted(BACKUPS.glob("pack_*")) if BACKUPS.is_dir() else []
    lines.append("BACKUPS:")
    lines.extend(f"  {p.name}" for p in packs[-6:]) or lines.append("  (none)")

    for name, path in [
        ("puppy_outbox", DRIVE / "fleet/bus/puppy_outbox.txt"),
        ("mac_outbox", DRIVE / "fleet/bus/mac_outbox.txt"),
        ("pack_status", DRIVE / "fleet/bus/PACK_STATUS.txt"),
    ]:
        lines.append("")
        lines.append(f"{name}:")
        if path.is_file():
            tail = path.read_text(encoding="utf-8", errors="replace").strip().splitlines()[-3:]
            lines.extend(f"  {ln}" for ln in tail)
        else:
            lines.append("  (missing)")

    lines.extend(["", "ORDERS:", "  NET    fleet/orders/PUPPY_ORDERS.txt", "  STUDIO fleet/orders/CB1_ORDERS.txt", "  CPT    fleet/orders/CB2_ORDERS.txt"])
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(OUT)


if __name__ == "__main__":
    main()
