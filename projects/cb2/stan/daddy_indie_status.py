#!/usr/bin/env python3
"""Daddy indie loop status — write fleet/indie_loop/FROM_DADDY.txt every poll."""
from __future__ import annotations

import socket
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from bus_lane import STAN, bus_root, safe_is_file, safe_mkdir, safe_read_text

INDIE = "fleet/indie_loop"
FROM_DADDY = f"{INDIE}/FROM_DADDY.txt"
FROM_BUNNY = f"{INDIE}/FROM_BUNNY.txt"
TO_BUNNY = f"{INDIE}/TO_BUNNY.txt"
CPT_BUNNY = "fleet/bus/CPT_BUNNY_LOOP.txt"
DOING = "fleet/bus/DADDY_DOING_NOW.txt"
BACKRUB = "backrub.txt"
BACKRUB_DROP = "drop_pile/backrub.txt"
LOG = STAN / "logs" / "daddy_indie_status.log"


def _now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def _host() -> str:
    return socket.gethostname()


def _port_up(port: int) -> str:
    import urllib.request

    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/health", timeout=2) as r:
            return "up" if r.status == 200 else f"http{r.status}"
    except OSError:
        return "down"


def _doing_line(bus: Path) -> str:
    p = bus / DOING
    if not safe_is_file(p):
        return "(idle)"
    action = detail = ""
    for ln in safe_read_text(p).splitlines():
        if ln.startswith("action: "):
            action = ln[8:].strip()
        elif ln.startswith("detail: "):
            detail = ln[8:].strip()
    if detail and detail != "(none)":
        return f"{action} — {detail}"[:160]
    return action or "(idle)"


def _watch_live() -> bool:
    import subprocess

    try:
        r = subprocess.run(["pgrep", "-f", "cpt_bunny_watch.sh"], capture_output=True, timeout=3)
        return r.returncode == 0
    except (OSError, subprocess.SubprocessError):
        return False


def _file_age_sec(bus: Path, rel: str) -> float | None:
    p = bus / rel
    if not safe_is_file(p):
        return None
    try:
        return max(0.0, time.time() - p.stat().st_mtime)
    except OSError:
        return None


def snapshot(bus: Path | None = None) -> dict[str, str]:
    root = bus or bus_root()
    bunny_raw = safe_read_text(root / FROM_BUNNY).strip() if safe_is_file(root / FROM_BUNNY) else ""
    bunny_head = bunny_raw.splitlines()[0] if bunny_raw else "(missing)"
    bunny_live = bool(bunny_raw) and bunny_head != "waiting for bunny"
    daddy_age = _file_age_sec(root, FROM_DADDY)
    watch = _watch_live()
    return {
        "bunny_head": bunny_head[:120],
        "bunny_live": "LIVE" if bunny_live else "SILENT",
        "daddy_post": "fresh" if daddy_age is not None and daddy_age < 90 else "stale",
        "daddy_age": f"{int(daddy_age)}s" if daddy_age is not None else "?",
        "watch": "LIVE" if watch else "DOWN",
        "job": _job_line(root),
        "to_bunny": _to_bunny_block(root)[:400],
    }


def write_cpt_bunny_loop() -> str:
    bus = bus_root()
    snap = snapshot(bus)
    ts = _now()
    gem_tail = ""
    gem_p = bus / "fleet/indie_loop/FROM_GEM.txt"
    if safe_is_file(gem_p):
        for ln in safe_read_text(gem_p).splitlines():
            if ln.startswith("bunny_tail:"):
                gem_tail = ln.split(":", 1)[1].strip()
                break
    body = "\n".join(
        [
            f"CPT BUNNY LOOP — {_host()} — {ts}",
            f"watch: {snap['watch']} · daddy_post: {snap['daddy_post']} ({snap['daddy_age']})",
            f"bunny: {snap['bunny_live']} · head: {snap['bunny_head']}",
            f"gem_bunny_tail: {gem_tail or '(unknown)'}",
            f"job: {snap['job']}",
            "",
            "READ FIRST (every session · Brian hates re-explaining):",
            "  fleet/bus/CPT_BUNNY_LOOP.txt  ← this file",
            "  fleet/indie_loop/FROM_DADDY.txt · FROM_BUNNY.txt · TO_BUNNY.txt",
            "  hitme.dev/bunny · hitme.dev/inbox (indie loop row)",
            "",
            "DADDY IN LOOP:",
            "  cpt_bunny_watch.sh must run on penguin (daddy_background.sh starts it)",
            "  FROM_DADDY.txt refreshes every ~30s while watch is live",
            "  Post jobs via /bunny or overwrite TO_BUNNY.txt",
            "",
            "IF bunny=SILENT — paste on Bunny box once:",
            "  nohup bash ~/GoogleDrive/MyDrive/lester/bbunny_loop.sh >>~/bbuny_loop.log 2>&1 &",
            "",
            "--- TO_BUNNY (current) ---",
            snap["to_bunny"] or "(empty)",
        ]
    )
    out = bus / CPT_BUNNY
    safe_mkdir(out.parent)
    out.write_text(body + "\n", encoding="utf-8")
    return body


def _job_line(bus: Path) -> str:
    p = bus / TO_BUNNY
    if not safe_is_file(p):
        return "(no TO_BUNNY)"
    lines = [ln.strip() for ln in safe_read_text(p).splitlines() if ln.strip()]
    for ln in lines:
        if ln.startswith("JOB:") or ln.startswith("FROM:"):
            continue
        if ln.startswith("Word:"):
            break
        if not ln.startswith("TIME:") and ln:
            return ln[:120]
    return (lines[4] if len(lines) > 4 else lines[-1] if lines else "(empty)")[:120]


def _to_bunny_block(bus: Path) -> str:
    p = bus / TO_BUNNY
    if not safe_is_file(p):
        return "(no job — say BUNNY on /bunny)"
    lines = safe_read_text(p).strip().splitlines()
    body: list[str] = []
    for ln in lines:
        s = ln.strip()
        if s.startswith("Word:"):
            break
        if s.startswith("JOB:") or s.startswith("TIME:") or s.startswith("FROM:"):
            continue
        if s:
            body.append(s)
    return "\n".join(body) if body else safe_read_text(p).strip()


def write_backrub() -> str:
    bus = bus_root()
    ts = _now()
    bunny_job = _to_bunny_block(bus)
    text = "\n".join(
        [
            f"backrub — Brian · {ts}",
            "hitme.dev/backrub · hitme.dev/team",
            "",
            "SMALL WORDS: DADDY · BUNNY · UNCLE · CLERK",
            "",
            "--- copy BUNNY block ---",
            bunny_job,
            "",
            "--- copy DADDY block ---",
            "CPT: ",
            "",
            "--- bunny loop once (if silent) ---",
            "nohup bash ~/GoogleDrive/MyDrive/lester/bbunny_loop.sh >>~/bbuny_loop.log 2>&1 &",
            "",
        ]
    )
    for rel in (BACKRUB, BACKRUB_DROP):
        path = bus / rel
        safe_mkdir(path.parent)
        path.write_text(text, encoding="utf-8")
    return text


def write_once() -> str:
    bus = bus_root()
    out = bus / FROM_DADDY
    safe_mkdir(out.parent)
    bunny = safe_read_text(bus / FROM_BUNNY).strip().splitlines()[0] if safe_is_file(bus / FROM_BUNNY) else "(missing)"
    body = "\n".join(
        [
            f"FROM_DADDY — {_host()} — {_now()}",
            "in_loop: yes · cpt_bunny_watch",
            f"doing: {_doing_line(bus)}",
            f"to_bunny: {_job_line(bus)}",
            f"bunny_tail: {bunny[:80]}",
            f"local: :8770={_port_up(8770)}",
            "backrub: MyDrive/backrub.txt · hitme.dev/backrub",
            "watch: cpt_bunny_watch · picture_inbox · fleet_self_check",
            "next_poll: ~30s",
        ]
    )
    out.write_text(body + "\n", encoding="utf-8")
    try:
        write_cpt_bunny_loop()
    except OSError:
        pass
    try:
        write_backrub()
    except OSError:
        pass
    safe_mkdir(LOG.parent)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(f"{_now()} wrote {FROM_DADDY}\n")
    return body


def watch(interval: float = 30.0) -> None:
    write_once()
    while True:
        time.sleep(interval)
        try:
            write_once()
        except OSError as exc:
            safe_mkdir(LOG.parent)
            with open(LOG, "a", encoding="utf-8") as f:
                f.write(f"{_now()} error: {exc}\n")


def main() -> int:
    if len(sys.argv) > 1 and sys.argv[1] == "watch":
        sec = float(sys.argv[2]) if len(sys.argv) > 2 else 30.0
        watch(sec)
        return 0
    print(write_once())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
