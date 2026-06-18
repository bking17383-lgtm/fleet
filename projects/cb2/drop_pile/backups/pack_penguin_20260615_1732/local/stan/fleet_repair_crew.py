#!/usr/bin/env python3
"""
Fleet repair crew — CB2 only. Slow poll, auto-fix what we can, log the rest.

  python3 ~/.stan/fleet_repair_crew.py once
  python3 ~/.stan/fleet_repair_crew.py watch   # default 90s

Does NOT ping Brian unless human needed. Writes fleet/bus/REPAIR_LOG.txt
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

DRIVE = Path("/mnt/shared/GoogleDrive/MyDrive")
LOG = DRIVE / "fleet/bus/REPAIR_LOG.txt"
ALERT = DRIVE / "fleet/bus/REPAIR_NOW.txt"
STATE = DRIVE / "fleet/bus/repair_crew_state.json"
STAN = Path.home() / ".stan"
INTERVAL = int(os.environ.get("REPAIR_INTERVAL", "90"))

SERVICES = (
    {"name": "sarah", "port": 8766, "cmd": f"python3 {STAN}/sarah_voice_sample.py"},
    {"name": "mesh_radio", "port": 8765, "cmd": f"python3 {STAN}/mesh_radio.py"},
    {"name": "hitme_who", "port": 8770, "cmd": f"cd {STAN} && python3 hitme_who_server.py"},
    {"name": "brian_router", "port": None, "match": "brian_router.py watch",
     "cmd": f"python3 {STAN}/brian_router.py watch"},
)


def _log(msg: str) -> None:
    LOG.parent.mkdir(parents=True, exist_ok=True)
    line = f"{datetime.now(timezone.utc).isoformat(timespec='seconds')} {msg}\n"
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line)


def _health(port: int, path: str = "/health") -> bool:
    try:
        urllib.request.urlopen(f"http://127.0.0.1:{port}{path}", timeout=3)
        return True
    except Exception:
        return False


def _pgrep(pattern: str) -> bool:
    try:
        r = subprocess.run(["pgrep", "-f", pattern], capture_output=True, timeout=5)
        return r.returncode == 0
    except Exception:
        return False


def _start(cmd: str) -> None:
    subprocess.Popen(
        cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        start_new_session=True,
    )


def _mesh_up() -> bool:
    for path in ("/health", "/status"):
        try:
            urllib.request.urlopen(f"http://127.0.0.1:8765{path}", timeout=2)
            return True
        except Exception:
            pass
    return False


def _hitme_tunnel_live() -> bool:
    try:
        urllib.request.urlopen("https://sarah.hitme.dev/health", timeout=8)
        return True
    except Exception:
        return False


def _load_state() -> dict:
    if STATE.is_file():
        try:
            return json.loads(STATE.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass
    return {}


def _save_state(st: dict) -> None:
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(st, indent=2), encoding="utf-8")


def run_once() -> list[str]:
    actions: list[str] = []
    human: list[str] = []
    st = _load_state()

    for svc in SERVICES:
        name = svc["name"]
        up = _health(svc["port"], svc.get("health_path", "/health")) if svc.get("port") else _pgrep(svc["match"])
        if not up:
            _log(f"FIX start {name}")
            _start(svc["cmd"])
            actions.append(f"restarted {name}")
            time.sleep(2)
        else:
            actions.append(f"{name} ok")

    if not _mesh_up():
        human.append("mesh :8765 DOWN — repair crew will retry; or bash ~/.stan/start_mesh_radio_tunnel.sh")
    else:
        actions.append("mesh ok")

    if not _hitme_tunnel_live():
        if not st.get("tunnel_warned"):
            human.append(
                "sarah.hitme.dev not live — tunnel hostnames or API token "
                "(fleet/HITME_TUNNEL_HOSTNAMES.txt)"
            )
            st["tunnel_warned"] = datetime.now(timezone.utc).isoformat()
    else:
        st.pop("tunnel_warned", None)
        actions.append("sarah.hitme.dev ok")

    # Refresh who's who at most every 10 min
    last_who = st.get("last_who", 0)
    now = time.time()
    if now - last_who > 600:
        who = DRIVE / "lester/plate_who.py"
        if who.is_file():
            try:
                subprocess.run([sys.executable, str(who)], timeout=60, capture_output=True)
                st["last_who"] = now
                actions.append("refreshed WHO")
            except subprocess.TimeoutExpired:
                pass

    _save_state(st)

    if human:
        ALERT.write_text(
            "REPAIR CREW — human needed\n"
            f"Updated: {datetime.now(timezone.utc).isoformat()}\n\n"
            + "\n".join(f"• {h}" for h in human)
            + "\n\nAuto-fixed this pass: " + ", ".join(actions) + "\n",
            encoding="utf-8",
        )
        _log("HUMAN " + "; ".join(human))
    elif ALERT.is_file():
        ALERT.unlink(missing_ok=True)

    summary = ", ".join(actions)
    _log("PASS " + summary)
    return actions


def main() -> None:
    mode = sys.argv[1] if len(sys.argv) > 1 else "watch"
    DRIVE.mkdir(parents=True, exist_ok=True)
    _log("repair_crew boot")
    if mode == "once":
        acts = run_once()
        print("\n".join(acts))
        return
    while True:
        try:
            run_once()
        except Exception as e:
            _log(f"ERR {e}")
        time.sleep(INTERVAL)


if __name__ == "__main__":
    main()
