#!/usr/bin/env python3
"""Daddy ready loop — speak "I need a job." until Brian responds on bus."""
from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from bus_lane import STAN, bus_root, safe_is_file, safe_mkdir, safe_read_text, LOGS

INTERVAL = float(os.environ.get("DADDY_READY_SEC", "45"))
PHRASE = os.environ.get("DADDY_READY_PHRASE", "I need a job.")
SILENT_UNTIL = "fleet/bus/DADDY_SILENT_UNTIL.txt"
STATE = STAN / "logs/daddy_ready_loop.json"
LOG = LOGS / "daddy_ready_loop.log"
READY_FEED = "fleet/bus/READY_FEED.txt"
LAB = "fleet/bus/LAB_REPLY.txt"
CPT_READY = "fleet/bus/CPT_READY.txt"


def _log(msg: str) -> None:
    safe_mkdir(LOG.parent)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(f"{datetime.now(timezone.utc).astimezone().isoformat(timespec='seconds')} {msg}\n")


def _afk_silent(bus: Path) -> bool:
    p = bus / SILENT_UNTIL
    if not safe_is_file(p):
        return False
    try:
        line = safe_read_text(p).strip().splitlines()[0]
        until = datetime.fromisoformat(line)
        if until.tzinfo is None:
            until = until.replace(tzinfo=timezone.utc).astimezone()
        return datetime.now(timezone.utc).astimezone() < until
    except (ValueError, IndexError, OSError):
        return False


def _mtime(path: Path) -> float:
    try:
        return path.stat().st_mtime
    except OSError:
        return 0.0


def _brian_recent(bus: Path, within: float = 300) -> bool:
    now = time.time()
    paths = [
        bus / "fleet/bus/CPT_BRIAN_INBOX.txt",
        bus / "TALK.txt",
    ]
    for p in paths:
        if not safe_is_file(p):
            continue
        if now - _mtime(p) > within:
            continue
        for line in reversed(safe_read_text(p).splitlines()[-12:]):
            s = line.strip()
            if not s or "picture_inbox" in s.lower():
                continue
            if "Brian via" in s or s.startswith("CPT:") or "Brian ·" in s:
                return True
    spin = bus / "fleet/bus/FLEET_SPIN.txt"
    if safe_is_file(spin) and now - _mtime(spin) <= within:
        last = [ln.strip() for ln in safe_read_text(spin).splitlines() if ln.strip()]
        if last and last[-1].startswith("CPT:") and "ready loop" not in last[-1].lower():
            return True
    return False


def _load_state() -> dict:
    if not STATE.is_file():
        return {"loops": 0, "active": False}
    try:
        return json.loads(STATE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"loops": 0, "active": False}


def _save_state(st: dict) -> None:
    safe_mkdir(STATE.parent)
    STATE.write_text(json.dumps(st, indent=2) + "\n", encoding="utf-8")


def _write_mp3(bus: Path) -> bool:
    try:
        sys.path.insert(0, str(STAN))
        from george_tts import synthesize_mp3

        data = synthesize_mp3(PHRASE)
        if not data:
            return False
        out = bus / "drop_pile/ready/daddy.mp3"
        safe_mkdir(out.parent)
        out.write_bytes(data)
        txt = bus / "drop_pile/ready/daddy.txt"
        now = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
        txt.write_text(
            f"{now}\n{PHRASE}\nPlay: https://hitme.dev/ready/daddy.mp3\n",
            encoding="utf-8",
        )
        return True
    except Exception as exc:
        _log(f"mp3 ERR {exc}")
        return False


def _speak_local(bus: Path) -> None:
    """Always try desk speaker — REAL_ALEXA must not block ready loop."""
    try:
        import subprocess

        mp3 = bus / "drop_pile/ready/daddy.mp3"
        for cmd in (
            ["mpg123", "-q", str(mp3)],
            ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", str(mp3)],
            ["espeak-ng", "-v", "en-us+m3", "-s", "145", "-p", "55", PHRASE],
            ["espeak-ng", "-s", "145", "-p", "50", PHRASE],
        ):
            if "mp3" in cmd[0] or cmd[-1].endswith(".mp3"):
                if not mp3.is_file():
                    continue
            try:
                subprocess.run(cmd, check=True, timeout=30)
                _log(f"local speak ok via {cmd[0]}")
                return
            except (OSError, subprocess.SubprocessError):
                continue
        _log("local speak fail — no audio backend")
    except Exception as exc:
        _log(f"local speak ERR {exc}")


def _queue_echo(loops: int = 0) -> None:
    try:
        sys.path.insert(0, str(STAN))
        from alexa_queue import queue_aloud

        msg = PHRASE if loops <= 1 else f"{PHRASE.rstrip('.')} — loop {loops}."
        queue_aloud(msg, force=True)
    except Exception as exc:
        _log(f"echo ERR {exc}")


def _write_bus(bus: Path, loops: int) -> None:
    now = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
    lab = bus / LAB
    lab.write_text(
        f"{now}\nDaddy looping: \"{PHRASE}\"\n"
        f"Loop #{loops} · TAP https://hitme.dev/listen\n"
        f"mp3: https://hitme.dev/ready/daddy.mp3\n",
        encoding="utf-8",
    )
    ready = bus / CPT_READY
    ready.write_text(
        f"DADDY READY LOOP — {now}\n"
        f"mode=FREE · looping until Brian answers\n\n"
        f"\"{PHRASE}\" · loop #{loops}\n"
        f"Audio: https://hitme.dev/ready/daddy.mp3\n"
        f"Page:  https://hitme.dev/ready?loop=daddy\n",
        encoding="utf-8",
    )
    feed = bus / READY_FEED
    prev = safe_read_text(feed) if safe_is_file(feed) else ""
    line = f"{now} · daddy · https://hitme.dev/ready/daddy.mp3 · loop #{loops} · {PHRASE}\n"
    if line.strip() not in prev:
        feed.write_text(prev.rstrip() + "\n" + line, encoding="utf-8")


def tick() -> str:
    bus = bus_root()
    st = _load_state()
    if _afk_silent(bus):
        return "afk silent"
    if _brian_recent(bus):
        if st.get("active"):
            st["active"] = False
            st["stopped"] = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
            _save_state(st)
            _log("stop — Brian responded")
        return "stop"

    st["loops"] = int(st.get("loops") or 0) + 1
    st["active"] = True
    st["last"] = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
    _save_state(st)

    mp3 = _write_mp3(bus)
    _speak_local(bus)
    _queue_echo(st["loops"])
    _write_bus(bus, st["loops"])
    msg = f"loop #{st['loops']} mp3={'ok' if mp3 else 'fail'}"
    _log(msg)
    return msg


def watch() -> None:
    _log("watch start")
    while True:
        try:
            tick()
        except Exception as exc:
            _log(f"tick ERR {exc}")
        time.sleep(INTERVAL)


def main() -> None:
    if len(sys.argv) > 1 and sys.argv[1] == "watch":
        watch()
    else:
        print(tick())


if __name__ == "__main__":
    main()
