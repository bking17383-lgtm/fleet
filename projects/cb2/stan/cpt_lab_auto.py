#!/usr/bin/env python3
"""CPT lab auto — Brian types /lab or /goal (CPT lane) · Daddy wakes via cursor-agent.

  python3 ~/.stan/cpt_lab_auto.py once
  python3 ~/.stan/cpt_lab_auto.py watch [seconds]
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from bus_lane import LOGS, STAN, bus_root, safe_is_file, safe_mkdir, safe_read_text

INTERVAL = float(os.environ.get("LAB_AUTO_SEC", "8"))
TIMEOUT = int(os.environ.get("LAB_AUTO_TIMEOUT", "420"))
def _resolve_agent_bin() -> str:
    for key in ("CPT_CURSOR_AGENT", "LAB_CURSOR_AGENT"):
        cand = os.environ.get(key, "").strip()
        if cand and Path(cand).is_file():
            return cand
    found = shutil.which("cursor-agent")
    if found and Path(found).is_file():
        return found
    default = Path.home() / ".local/bin/cursor-agent"
    return str(default)


AGENT_BIN = _resolve_agent_bin()
WORKSPACE = os.environ.get("LAB_AUTO_WORKSPACE", str(Path.home()))

STATE_REL = "fleet/bus/cpt_lab_auto_state.json"
STATUS_REL = "fleet/bus/CPT_LAB_AUTO.txt"
REPLY_REL = "fleet/bus/LAB_REPLY.txt"
LAST_POST_REL = "fleet/bus/BRIAN_LAST_POST.txt"
LOCK = STAN / "cpt_lab_auto.lock"
LOG = LOGS / "cpt_lab_auto.log"

LAB_LANES = frozenset({"cpt", "daddy", "captn", "captain"})


def _now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def _log(msg: str) -> None:
    safe_mkdir(LOG.parent)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(f"{_now()} {msg}\n")
    print(msg, flush=True)


def _write_status(bus: Path, **fields: str) -> None:
    p = bus / STATUS_REL
    safe_mkdir(p.parent)
    lines = [f"CPT LAB AUTO — {_now()}", f"host=penguin · watcher=cpt_lab_auto.py"]
    for k, v in fields.items():
        lines.append(f"{k}={v}")
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _load_state(bus: Path) -> dict:
    p = bus / STATE_REL
    raw = safe_read_text(p)
    if not raw.strip():
        return {"processed": []}
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return {"processed": []}
    if not isinstance(data.get("processed"), list):
        data["processed"] = []
    return data


def _save_state(bus: Path, data: dict) -> None:
    p = bus / STATE_REL
    safe_mkdir(p.parent)
    data["last_run"] = _now()
    data["processed"] = data.get("processed", [])[-80:]
    p.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def _parse_last_post(text: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for ln in text.splitlines():
        if "=" in ln:
            k, v = ln.split("=", 1)
            out[k.strip()] = v.strip()
    return out


def _extract_brian_message(line: str) -> str:
    m = re.match(r"^\[[^\]]+\]\s*(?:\[[^\]]+\]\s*)?(.*)$", line.strip())
    if m:
        return m.group(1).strip()
    return line.strip()


def _pending_from_last_post(bus: Path) -> tuple[str, str] | None:
    post = bus / LAST_POST_REL
    if not safe_is_file(post):
        return None
    meta = _parse_last_post(safe_read_text(post))
    lane = (meta.get("lane") or "").lower()
    raw_line = meta.get("line") or ""
    if not raw_line:
        return None
    if lane not in LAB_LANES and "goal/cpt" not in raw_line and "via lab" not in raw_line and "via daddy" not in raw_line:
        return None
    msg = _extract_brian_message(raw_line)
    if not msg:
        return None
    h = hashlib.sha256(raw_line.encode()).hexdigest()[:16]
    return h, msg


def _agent_busy() -> bool:
    if LOCK.is_file():
        try:
            pid = int(LOCK.read_text(encoding="utf-8").strip().split()[0])
            os.kill(pid, 0)
            return True
        except (OSError, ValueError):
            try:
                LOCK.unlink(missing_ok=True)
            except OSError:
                pass
    try:
        r = subprocess.run(
            ["pgrep", "-f", "cursor-agent.*--print"],
            capture_output=True,
            timeout=3,
        )
        return r.returncode == 0
    except (OSError, subprocess.SubprocessError):
        return False


def _build_prompt(message: str, bus: Path) -> str:
    reply_path = bus / REPLY_REL
    return (
        "LAB AUTO — Brian typed on /lab or /goal (CPT lane).\n\n"
        f'Brian says: "{message}"\n\n'
        "You are Daddy (CPT captain) on penguin CB2. Brian is typing, not speaking.\n"
        "Read drop_pile/to_cursor/DADDY_DELEGATE_ONLY.md if fleet delegation applies.\n\n"
        "Do:\n"
        "1. Answer or execute what Brian asked (lab/infra on CB2; delegate fleet per law).\n"
        f"2. Write a short plain reply to {reply_path} "
        "(first line: timestamp, then 1-4 sentences Brian can read on /lab).\n"
        "3. Be concise — token discipline.\n\n"
        "Do not tell Brian to say check lab."
    )


def _wake_agent(bus: Path, message: str) -> str:
    prompt = _build_prompt(message, bus)
    _write_status(
        bus,
        status="busy",
        brian=message[:120],
        agent=AGENT_BIN,
    )
    safe_mkdir(LOCK.parent)
    LOCK.write_text(f"{os.getpid()} {_now()}\n", encoding="utf-8")
    try:
        _log(f"WAKE brian={message[:80]!r}")
        r = subprocess.run(
            [AGENT_BIN, "-p", "--trust", "--force", "--workspace", WORKSPACE, prompt],
            capture_output=True,
            text=True,
            timeout=TIMEOUT,
            cwd=WORKSPACE,
        )
        out = (r.stdout or "").strip()
        err = (r.stderr or "").strip()
        if r.returncode != 0:
            fail = err or out or f"exit {r.returncode}"
            reply = f"{_now()}\nDaddy auto error: {fail[:500]}"
            (bus / REPLY_REL).write_text(reply + "\n", encoding="utf-8")
            _write_status(bus, status="error", brian=message[:120], detail=fail[:200])
            _log(f"ERROR {fail[:200]}")
            return "error"
        if out and not safe_is_file(bus / REPLY_REL):
            (bus / REPLY_REL).write_text(f"{_now()}\n{out[:2000]}\n", encoding="utf-8")
        _write_status(bus, status="idle", brian=message[:120], last_ok=_now())
        _log(f"OK bytes={len(out)}")
        return "ok"
    except subprocess.TimeoutExpired:
        reply = f"{_now()}\nDaddy auto timed out after {TIMEOUT}s — try a shorter ask."
        (bus / REPLY_REL).write_text(reply + "\n", encoding="utf-8")
        _write_status(bus, status="error", brian=message[:120], detail="timeout")
        _log("TIMEOUT")
        return "timeout"
    finally:
        try:
            LOCK.unlink(missing_ok=True)
        except OSError:
            pass


def once() -> bool:
    bus = bus_root()
    pending = _pending_from_last_post(bus)
    if not pending:
        return False
    h, msg = pending
    state = _load_state(bus)
    if h in state.get("processed", []):
        return False
    if _agent_busy():
        _write_status(bus, status="queued", brian=msg[:120])
        _log(f"BUSY skip {msg[:60]!r}")
        return False
    result = _wake_agent(bus, msg)
    if result == "ok":
        state.setdefault("processed", []).append(h)
        _save_state(bus, state)
        return True
    return False


def watch(interval: float = INTERVAL) -> None:
    bus = bus_root()
    _write_status(bus, status="watching", interval=str(interval))
    _log(f"watching {LAST_POST_REL} every {interval}s · lanes={','.join(sorted(LAB_LANES))}")
    while True:
        try:
            once()
        except Exception as exc:
            _log(f"watch error: {exc}")
            _write_status(bus, status="error", detail=str(exc)[:200])
        time.sleep(interval)


def main() -> None:
    cmd = sys.argv[1] if len(sys.argv) > 1 else "watch"
    if cmd == "once":
        sys.exit(0 if once() else 1)
    if cmd == "watch":
        watch(float(sys.argv[2]) if len(sys.argv) > 2 else INTERVAL)
        return
    print("Usage: cpt_lab_auto.py once|watch [seconds]", file=sys.stderr)
    sys.exit(2)


if __name__ == "__main__":
    main()
