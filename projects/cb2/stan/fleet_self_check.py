#!/usr/bin/env python3
"""Fleet self-check — Brian law: every 25s until system green.

  python3 ~/.stan/fleet_self_check.py once
  python3 ~/.stan/fleet_self_check.py watch [seconds]

Writes fleet/bus/FLEET_SELF_CHECK.txt · appends SLAVE_PULSE.txt
"""
from __future__ import annotations

import os
import subprocess
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from bus_lane import bus_root, is_drive_live, safe_is_file, safe_mkdir, safe_read_text, STAN, LOGS

INTERVAL = float(os.environ.get("FLEET_CHECK_SEC", "25"))
OUT = "fleet/bus/FLEET_SELF_CHECK.txt"
PULSE = "fleet/bus/SLAVE_PULSE.txt"
LOG = LOGS / "fleet_self_check.log"


def _log(msg: str) -> None:
    safe_mkdir(LOG.parent)
    line = f"{datetime.now(timezone.utc).isoformat(timespec='seconds')} {msg}\n"
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line)


def _http(port: int, path: str = "/health") -> bool:
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}{path}", timeout=2) as r:
            return r.status == 200
    except OSError:
        return False


def _mtime_rel(bus: Path, rel: str) -> str:
    p = bus / rel
    if not safe_is_file(p):
        return "missing"
    try:
        ts = datetime.fromtimestamp(p.stat().st_mtime, tz=timezone.utc).astimezone()
        return ts.isoformat(timespec="seconds")
    except OSError:
        return "err"


def _tail_line(bus: Path, rel: str) -> str:
    p = bus / rel
    if not safe_is_file(p):
        return "(missing)"
    lines = [ln.strip() for ln in safe_read_text(p).splitlines() if ln.strip()]
    return lines[-1][:100] if lines else "(empty)"


def tick() -> dict:
    bus = bus_root()
    now = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
    host = os.uname().nodename

    try:
        subprocess.run([sys.executable, str(STAN / "cpt_slave.py")], check=False, timeout=20, capture_output=True)
    except (OSError, subprocess.SubprocessError) as exc:
        _log(f"cpt_slave err {exc}")

    try:
        subprocess.run([sys.executable, str(STAN / "aws_fleet_watch.py"), "once"], check=False, timeout=20, capture_output=True)
    except (OSError, subprocess.SubprocessError) as exc:
        _log(f"watch err {exc}")

    try:
        subprocess.run([sys.executable, str(STAN / "cpt_autopilot.py"), "once"], check=False, timeout=45, capture_output=True)
    except (OSError, subprocess.SubprocessError) as exc:
        _log(f"autopilot err {exc}")

    svc = {
        "mesh": _http(8765),
        "sarah": _http(8766),
        "desk": _http(8770),
    }
    boxes = {
        "gem_to_cpt": _mtime_rel(bus, "fleet/bus/gem_to_cpt.txt"),
        "dog_outbox": _mtime_rel(bus, "fleet/bus/dog_outbox.txt"),
        "uncle_to_cpt": _mtime_rel(bus, "fleet/bus/uncle_to_cpt.txt"),
        "lester_keys": _mtime_rel(bus, "lester/lester_keys.md"),
    }
    keys_ok = "AKIA" in safe_read_text(bus / "lester/lester_keys.md") if safe_is_file(bus / "lester/lester_keys.md") else False
    dog_ok = boxes["dog_outbox"] != "missing"
    green = all(svc.values()) and dog_ok

    lines = [
        f"FLEET SELF-CHECK — {now}",
        f"host={host} · interval={INTERVAL:.0f}s · drive={'OK' if is_drive_live() else 'FUSE?'}",
        f"system_green={'YES' if green else 'NO — keep looping'}",
        "",
        "SERVICES (CPT)",
        *[f"  • {k}: {'OK' if v else 'DOWN'}" for k, v in svc.items()],
        "",
        "BOX PULSE (mtime)",
        *[f"  • {k}: {v}" for k, v in boxes.items()],
        f"  • keys AKIA: {'YES' if keys_ok else 'NO'}",
        "",
        "TAILS",
        f"  gem: {_tail_line(bus, 'fleet/bus/gem_to_cpt.txt')}",
        f"  dog: {_tail_line(bus, 'fleet/bus/dog_outbox.txt')}",
        f"  net: {_tail_line(bus, 'fleet/bus/NET_STATUS.txt')}",
        f"  uncle: {_tail_line(bus, 'fleet/bus/uncle_to_cpt.txt')}",
        "",
        "LAW: everyone self-check every 25s until green · post plain .txt",
        "Word: SELF-CHECK · read fleet/FLEET_SELF_CHECK_LAW.txt",
    ]
    text = "\n".join(lines) + "\n"
    out = bus / OUT
    safe_mkdir(out.parent)
    out.write_text(text, encoding="utf-8")

    pulse = bus / PULSE
    pulse_line = f"[{now}] SELF-CHECK host={host} green={'YES' if green else 'NO'} desk={'OK' if svc['desk'] else 'DOWN'}\n"
    with open(pulse, "a", encoding="utf-8") as f:
        f.write(pulse_line)

    _log(f"tick green={green} svc={svc}")
    return {"now": now, "green": green, "services": svc, "boxes": boxes}


def watch_loop(sec: float) -> None:
    _log(f"START interval={sec}s")
    while True:
        try:
            tick()
        except Exception as exc:
            _log(f"ERR {exc}")
        time.sleep(sec)


def main() -> int:
    cmd = sys.argv[1] if len(sys.argv) > 1 else "once"
    if cmd == "once":
        r = tick()
        print(f"green={r['green']} · {r['now']}")
        print(f"→ {bus_root() / OUT}")
        return 0
    if cmd == "watch":
        sec = float(sys.argv[2]) if len(sys.argv) > 2 else INTERVAL
        watch_loop(sec)
        return 0
    print("Usage: fleet_self_check.py once|watch [seconds]", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
