#!/usr/bin/env python3
"""Push fleet needs to hitme server (local :8770 · public /api/needs).

  python3 ~/.stan/daddy_needs_push.py once
  python3 ~/.stan/daddy_needs_push.py watch [seconds]
"""
from __future__ import annotations

import json
import re
import socket
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from bus_lane import bus_root, safe_is_file, safe_read_text, STAN

PORT = int(__import__("os").environ.get("HITME_PORT", "8770"))
BUS = bus_root()
OUT_TXT = BUS / "fleet/bus/FLEET_NEEDS_SERVER.txt"
OUT_JSON = BUS / "fleet/bus/FLEET_NEEDS.json"


def _now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def _snip(rel: str, n: int = 12) -> str:
    p = BUS / rel
    if not safe_is_file(p):
        return ""
    return "\n".join(safe_read_text(p).strip().splitlines()[:n])


def collect_needs() -> dict:
    host = socket.gethostname()
    checkin = safe_read_text(BUS / "fleet/bus/FLEET_CHECKIN.txt")
    roll_m = re.search(r"roll=(\d+/\d+)", checkin)
    roll = roll_m.group(1) if roll_m else "?/?"

    needs: list[str] = []
    blockers: list[str] = []
    keyboard: list[str] = []

    if "PUPPY" in checkin and "NO CHECK-IN" in checkin:
        needs.append("Puppy fresh check-in: PUPPY CHECKIN — puppy64 — <ip> — <time>")
    if "puppy_needs" in _snip("fleet/bus/puppy_needs.txt", 30) or safe_is_file(BUS / "fleet/bus/puppy_needs.txt"):
        pn = safe_read_text(BUS / "fleet/bus/puppy_needs.txt")
        if "BLOCKER" in pn or "CLOSED" in pn:
            for line in pn.splitlines():
                s = line.strip()
                if s.startswith(("BLOCKER", "RUN ON PUPPY", ":22", ":8765", ":8766", ":8002")):
                    blockers.append(s[:120])
        if "PUPPY_JAILBREAK" in pn or "keyboard" in pn.lower():
            keyboard.append("bash ~/GoogleDrive/MyDrive/lester/PUPPY_JAILBREAK.sh")

    fix_truth = safe_read_text(BUS / "fleet/bus/PUPPY_FIX_TRUTH.txt")
    if fix_truth:
        if "CANNOT" in fix_truth:
            blockers.append("Puppy: no SSH · wrong :8002 app · needs keyboard once")
        if "JAILBREAK" in fix_truth:
            keyboard.append("bash ~/GoogleDrive/MyDrive/lester/PUPPY_JAILBREAK.sh")

    ready = safe_read_text(BUS / "fleet/bus/CPT_READY.txt")
    for line in ready.splitlines():
        if line.strip().startswith("•") and "waiting" not in line.lower():
            s = line.strip()[1:].strip()
            if s and s not in needs:
                needs.append(s[:140])

    if "AWS not green" in ready or "ok=WAIT" in _snip("fleet/bus/AWS_STATUS.txt", 5):
        needs.append("AWS: bash lester/aws_fix_anyone.sh on any box")

    hitme = safe_read_text(BUS / "fleet/HITME_STATUS.txt")
    if "530" in hitme or "public=530" in hitme:
        blockers.append("hitme.dev public 530 — tunnel DNS/ingress or hitme_cf_provision.sh")

    payload = {
        "time": _now(),
        "from": f"Daddy on {host}",
        "roll": roll,
        "needs": needs[:12],
        "blockers": blockers[:12],
        "keyboard": keyboard[:6],
        "sources": [
            "fleet/bus/FLEET_CHECKIN.txt",
            "fleet/bus/puppy_needs.txt",
            "fleet/bus/PUPPY_FIX_TRUTH.txt",
            "fleet/bus/CPT_READY.txt",
        ],
    }
    return payload


def _write_local(payload: dict) -> None:
    OUT_TXT.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        f"FLEET NEEDS — {payload['time']}",
        f"from: {payload['from']}",
        f"roll: {payload['roll']}",
        "",
        "NEEDS",
        *[f"  • {n}" for n in payload.get("needs") or ["(none)"]],
        "",
        "BLOCKERS",
        *[f"  • {b}" for b in payload.get("blockers") or ["(none)"]],
        "",
        "KEYBOARD (Brian once)",
        *[f"  • {k}" for k in payload.get("keyboard") or ["(none)"]],
        "",
        f"api: http://127.0.0.1:{PORT}/api/needs",
    ]
    OUT_TXT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    OUT_JSON.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def push_once(base: str = f"http://127.0.0.1:{PORT}") -> dict:
    payload = collect_needs()
    _write_local(payload)
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"{base.rstrip('/')}/api/needs",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=8) as r:
            resp = json.loads(r.read().decode("utf-8", errors="replace"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        return {"ok": False, "error": f"HTTP {e.code}", "body": body, "payload": payload}
    except OSError as e:
        return {"ok": False, "error": str(e), "payload": payload, "local": str(OUT_TXT)}
    return {"ok": True, "server": resp, "payload": payload, "local": str(OUT_TXT)}


def watch(sec: float) -> None:
    while True:
        r = push_once()
        print(json.dumps({"ok": r.get("ok"), "roll": r.get("payload", {}).get("roll"), "error": r.get("error")}))
        time.sleep(sec)


def main() -> int:
    cmd = sys.argv[1] if len(sys.argv) > 1 else "once"
    if cmd == "watch":
        sec = float(sys.argv[2]) if len(sys.argv) > 2 else 120.0
        watch(sec)
        return 0
    r = push_once()
    print(json.dumps(r, indent=2))
    return 0 if r.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
