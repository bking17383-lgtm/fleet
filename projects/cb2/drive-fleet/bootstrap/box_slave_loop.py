#!/usr/bin/env python3
"""Box slave loop — Bunny or Daddy. Copy to each box · run once · no Brian."""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

BOXES = {
    "bunny": {
        "to": "fleet/indie_loop/TO_BUNNY.txt",
        "from": "fleet/indie_loop/FROM_BUNNY.txt",
        "ack_dir": "drop_pile/from_bbbunny",
        "key": None,
    },
    "daddy": {
        "to": "fleet/indie_loop/TO_DADDY.txt",
        "from": "fleet/indie_loop/FROM_DADDY.txt",
        "ack_dir": "drop_pile/from_lester",
        "key": "f770e0dc",
    },
}

INTERVAL = float(os.environ.get("BOX_SLAVE_SEC", "30"))


def drive() -> Path:
    for p in (
        Path("/mnt/shared/GoogleDrive/MyDrive"),
        Path.home() / "GoogleDrive/MyDrive",
    ):
        if (p / "fleet").is_dir():
            return p
    raise SystemExit("NO_DRIVE")


def now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def digest(path: Path) -> str:
    if not path.is_file():
        return ""
    return hashlib.sha256(path.read_bytes()).hexdigest()[:16]


def main() -> int:
    box = (sys.argv[1] if len(sys.argv) > 1 else os.environ.get("BOX_SLAVE", "")).lower()
    if box not in BOXES:
        print("Usage: box_slave_loop.py bunny|daddy")
        return 1
    cfg = BOXES[box]
    root = drive()
    to_p = root / cfg["to"]
    from_p = root / cfg["from"]
    ack = root / cfg["ack_dir"]
    ack.mkdir(parents=True, exist_ok=True)
    state_f = Path.home() / f".{box}_slave_state.json"
    host = subprocess.getoutput("hostname -s") or box
    ip = subprocess.getoutput("hostname -I").split()[0] or "?"
    prev = ""
    if state_f.is_file():
        try:
            prev = json.loads(state_f.read_text()).get("to_hash", "")
        except json.JSONDecodeError:
            pass

    while True:
        job = to_p.read_text(encoding="utf-8", errors="replace") if to_p.is_file() else "(no job)"
        h = digest(to_p)
        if h and h != prev:
            if "start_hitme_proxy" in job:
                sh = root / "lester/hitme_simple/start_hitme_proxy.sh"
                if sh.is_file():
                    subprocess.run(["bash", str(sh)], timeout=300, check=False)
            if box == "bunny":
                pub = subprocess.getoutput("curl -4 -sf --max-time 8 ifconfig.me") or "unknown"
                (ack / "PUBLIC_IP.txt").write_text(pub.strip() + "\n", encoding="utf-8")
        prev = h
        if state_f.parent.is_dir() or True:
            state_f.write_text(json.dumps({"to_hash": h, "time": now()}) + "\n")

        body = [
            f"FROM_{box.upper()} — {host} — {now()}",
            f"slave: box_slave_loop.py · box={box}",
            f"host={host} ip={ip}",
            f"to_mtime={to_p.stat().st_mtime if to_p.is_file() else 0}",
            "--- TO ---",
            job.splitlines()[0] if job else "(empty)",
            job.splitlines()[1] if job.count("\n") else "",
        ]
        from_p.parent.mkdir(parents=True, exist_ok=True)
        from_p.write_text("\n".join(body[:8]) + "\n", encoding="utf-8")
        (ack / "ACK.txt").write_text(
            f"ACK {box} {host} {now()}\nip={ip}\njob={job.splitlines()[0][:60]}\n",
            encoding="utf-8",
        )
        if box == "daddy":
            lester = ack / "lester6_to_daddy.md"
            lester.write_text(
                f"# BEACON ack — {now()}\n\n"
                f"- read: `{cfg['to']}`\n"
                f"- job: {job.splitlines()[0][:80]}\n"
                f"- slave: LIVE on {host}\n",
                encoding="utf-8",
            )
        time.sleep(INTERVAL)


if __name__ == "__main__":
    raise SystemExit(main())
