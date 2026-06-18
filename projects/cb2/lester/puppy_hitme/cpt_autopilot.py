#!/usr/bin/env python3
"""CPT autopilot — boxes self-heal what they can · report to bus · CPT always ready.

  python3 ~/.stan/cpt_autopilot.py once
  python3 ~/.stan/cpt_autopilot.py watch [seconds]

Writes fleet/bus/CPT_READY.txt — one file CPT reads every session.
Does NOT block Brian in chat.
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from bus_lane import bus_root, is_drive_live, safe_is_file, safe_mkdir, safe_read_text, STAN, LOGS

INTERVAL = float(os.environ.get("AUTOPILOT_SEC", "25"))
READY = "fleet/bus/CPT_READY.txt"
LOG = LOGS / "cpt_autopilot.log"
PUPPY_LAN = os.environ.get("PUPPY_LAN", "192.168.1.4")
STALE = int(os.environ.get("FLEET_CHECKIN_STALE", "90"))


def _log(msg: str) -> None:
    safe_mkdir(LOG.parent)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(f"{datetime.now(timezone.utc).isoformat(timespec='seconds')} {msg}\n")


def _http(port: int) -> bool:
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/health", timeout=2) as r:
            return r.status == 200
    except OSError:
        return False


def _buddy_pending_check(bus: Path) -> bool:
    fwd = bus / "fleet/bus/GEM_BUDDY_FORWARDED.txt"
    if safe_is_file(fwd) and "answered=NO" in safe_read_text(fwd):
        return True
    return False


def _ping(host: str) -> bool:
    try:
        r = subprocess.run(
            ["ping", "-c", "1", "-W", "2", host],
            capture_output=True,
            timeout=5,
        )
        return r.returncode == 0
    except (OSError, subprocess.SubprocessError):
        return False


def _mtime_age(bus: Path, rel: str) -> float | None:
    p = bus / rel
    if not safe_is_file(p):
        return None
    try:
        ts = datetime.fromtimestamp(p.stat().st_mtime, tz=timezone.utc)
        return (datetime.now(timezone.utc) - ts).total_seconds()
    except OSError:
        return None


def _run_py(script: str, *args: str, timeout: int = 25) -> bool:
    try:
        r = subprocess.run(
            [sys.executable, str(STAN / script), *args],
            capture_output=True,
            timeout=timeout,
        )
        return r.returncode == 0
    except (OSError, subprocess.SubprocessError):
        return False


def _ensure_bg(match: str, cmd: str) -> str | None:
    try:
        r = subprocess.run(["pgrep", "-f", match], capture_output=True, timeout=3)
        if r.returncode == 0:
            return None
        subprocess.Popen(
            cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True
        )
        return f"started {match}"
    except (OSError, subprocess.SubprocessError):
        return None


def tick() -> dict:
    bus = bus_root()
    now = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
    fixed: list[str] = []
    waiting: list[str] = []
    human: list[str] = []

    net_up = _ping(PUPPY_LAN)

    # Daddy thin infra on CB2 — dashboard + eyes only
    for name, port, match, cmd in (
        ("hitme", 8770, "hitme_who_server.py", f"python3 {STAN}/hitme_who_server.py"),
    ):
        if not _http(port):
            if a := _ensure_bg(match, cmd):
                fixed.append(a)
                time.sleep(1)
            if not _http(port):
                waiting.append(f"{name} :{port} still down after restart")
        else:
            fixed.append(f"{name} ok")

    if a := _ensure_bg("screen_watch.py watch", f"python3 {STAN}/screen_watch.py watch 20"):
        fixed.append(a)

    # mesh · sarah · desk — DELEGATE ONLY (never start on Daddy)
    for name, preset in (("mesh", "mesh"), ("sarah", "sarah")):
        port = 8765 if name == "mesh" else 8766
        if _http(port):
            waiting.append(f"{name} up on Daddy temp — still delegate to Puppy for real")
        pup = bus / "fleet/bus/cpt_to_puppy.txt"
        tag = f"delegate {name}:"
        if not safe_is_file(pup) or tag not in safe_read_text(pup)[-800:]:
            _run_py("daddy_delegate.py", "puppy", preset if preset != "mesh" else "checkin")
            fixed.append(f"delegated {name} → Puppy")
        waiting.append(f"Puppy owns {name} — Daddy waits")

    # Background crew — watchers only (no repair execute)
    for match, cmd in (
        ("fleet_self_check.py watch", f"python3 {STAN}/fleet_self_check.py watch 25"),
        ("brian_router.py watch", f"python3 {STAN}/brian_router.py watch 12"),
        ("hitme_always.sh", f"bash {STAN}/hitme_always.sh"),
    ):
        if a := _ensure_bg(match, cmd):
            fixed.append(a)

    # Puppy check-in — orders only · Daddy waits
    net_age = _mtime_age(bus, "fleet/bus/puppy_outbox.txt")
    if net_age is None or net_age > STALE:
        _run_py("daddy_delegate.py", "puppy", "checkin")
        fixed.append("delegated Puppy checkin")
        waiting.append("Puppy — post PUPPY CHECKIN on Drive (word: PUPPY)")
    else:
        fixed.append("Puppy check-in fresh")

    # Uncle + Gem — same CB1 box · listen every tick · stop boot spam when linked
    UNCLE_LINK_SEC = 600
    _run_py("cpt_gem_loop.py", "listen", timeout=20)
    ack_gem = safe_read_text(bus / "fleet/bus/cpt_ack_gem.txt")
    ack_uncle = safe_read_text(bus / "fleet/bus/cpt_ack_uncle.txt")
    linked = (
        "loop: LIVE" in ack_gem
        and "gem_heard: YES · CB1" in ack_gem
        and "uncle_heard: YES · CB1" in ack_gem
        and "heard: YES · CB1 confirmed" in ack_uncle
    )

    ping_age = _mtime_age(bus, "fleet/bus/GEM_LOOP_PING.txt")
    if ping_age is None or ping_age > 300:
        _run_py("cpt_gem_loop.py", "ping", timeout=20)
        fixed.append("loop ping → Gem+Uncle inbox")
    elif linked:
        fixed.append("Uncle+Gem loop LINKED")

    _run_py("cpt_gem_loop.py", "reconnect", timeout=20)
    _run_py("cpt_gem_loop.py", "forward", timeout=15)
    _run_py("cpt_gem_loop.py", "listen", timeout=15)
    if _buddy_pending_check(bus):
        waiting.append("Gem — answer Brian on gem_to_cpt (cpt_to_gem has job)")
        fixed.append("BUDDY → cpt_to_gem forwarded")

    if linked:
        fixed.append("acks refreshed · cpt_to_uncle=LINKED hold")
    else:
        uncle_age = _mtime_age(bus, "fleet/bus/uncle_to_cpt.txt")
        last_delegate = _mtime_age(bus, "fleet/bus/.last_delegate_studio_loop")
        if uncle_age is None or uncle_age > UNCLE_LINK_SEC:
            if last_delegate is None or last_delegate > 600:
                _run_py("daddy_delegate.py", "studio", "loop")
                stamp = bus / "fleet/bus/.last_delegate_studio_loop"
                safe_mkdir(stamp.parent)
                stamp.write_text(now, encoding="utf-8")
                fixed.append("delegated Uncle loop (cold start)")
            waiting.append("Uncle+Gem — post from CB1 (Gem loader · Uncle Linux)")
        else:
            waiting.append("Gem or Uncle — finish loop ack from cb1")

    # Failover — Gem stale → NET pickup · AWS WAIT → fleet AWS FIX
    gem_age = _mtime_age(bus, "fleet/bus/gem_to_cpt.txt")
    keys_md = safe_read_text(bus / "lester/lester_keys.md") if safe_is_file(bus / "lester/lester_keys.md") else ""
    aws_status = safe_read_text(bus / "fleet/bus/AWS_STATUS.txt") if safe_is_file(bus / "fleet/bus/AWS_STATUS.txt") else ""
    failover = bus / "fleet/bus/FAILOVER_ACTIVE.txt"

    if gem_age is not None and gem_age > STALE * 3:
        fo = (
            f"FAILOVER_ACTIVE — {now}\n"
            "trigger=gem_stale\n"
            "captain=Daddy CB2 only · Gem NEVER becomes Daddy\n"
            "brian_fix=puppy keyboard + Gem Chrome · read DADDY_DOWN_FIX.txt\n"
            "pickup=NET execute · Gem Drive bridge · NOT captain promotion\n"
            "read: fleet/DADDY_FAILOVER.txt · fleet/FLEET_FAILOVER.txt\n"
            "net_job: mirror Drive bus · post NET CHECKIN · optional PUPPY_HITME\n"
        )
        failover.write_text(fo, encoding="utf-8")
        waiting.append("Gem stale — Brian on puppy + Gem repair · Gem NOT captain")
        pup = bus / "fleet/bus/cpt_to_puppy.txt"
        if net_up and safe_is_file(pup) and "failover pickup" not in safe_read_text(pup)[-400:]:
            pup.write_text(
                safe_read_text(pup).rstrip()
                + f"\n\nfailover pickup: {now} — Gem down · NET read FAILOVER_ACTIVE.txt · Drive hands\n",
                encoding="utf-8",
            )
            fixed.append("failover orders → NET")
    elif failover.is_file():
        failover.unlink(missing_ok=True)

    if "AKIA" not in keys_md or "ok=WAIT" in aws_status or "SANDBOX_OK" not in aws_status:
        waiting.append("AWS not green — any box: bash lester/aws_fix_anyone.sh")
        for rel in ("fleet/bus/cpt_to_puppy.txt", "fleet/bus/cpt_to_uncle.txt"):
            p = bus / rel
            if safe_is_file(p) and "AWS FIX" not in safe_read_text(p)[-500:]:
                p.write_text(
                    safe_read_text(p).rstrip()
                    + f"\n\nAWS FIX: {now} — read fleet/AWS_FIX_ANYONE.txt · run lester/aws_fix_anyone.sh\n",
                    encoding="utf-8",
                )
        fixed.append("AWS FIX delegated fleet-wide")

    # Needs on server for Brian / phone
    _run_py("daddy_needs_push.py", "once", timeout=15)

    # Roll call only — no local repair crew (delegate all)
    _run_py("fleet_checkin.py", "once", timeout=15)

    checkin = safe_read_text(bus / "fleet/bus/FLEET_CHECKIN.txt")
    roll_m = re.search(r"roll=(\d+/(\d+))", checkin)
    roll = roll_m.group(1) if roll_m else "?/?"

    repair = safe_read_text(bus / "fleet/bus/REPAIR_NOW.txt") if safe_is_file(bus / "fleet/bus/REPAIR_NOW.txt") else ""

    lines = [
        f"DADDY WAIT — {now}",
        f"mode=DELEGATE ALL · waiting for team · roll={roll}",
        "",
        "BRIAN: Daddy posts orders · does NOT execute · waits for 3/3",
        "",
        "DELEGATED THIS TICK",
        *([f"  • {x}" for x in fixed[:8]] if fixed else ["  • (none)"]),
        "",
        "WAITING FOR TEAM",
        *([f"  • {x}" for x in waiting[:8]] if waiting else ["  • none"]),
        "",
    ]
    if roll.startswith("3/"):
        lines.insert(4, "TEAM UP — Daddy can delegate work · not hold infra")
    elif roll.startswith("2/"):
        lines.insert(4, "ALMOST — one machine missing · check FLEET_CHECKIN.txt")
    if human:
        lines.extend(["KEYBOARD (Brian once per missing box)", *[f"  • {x}" for x in human], ""])
    if repair.strip():
        lines.extend(["REPAIR_NOW", repair.strip()[:800], ""])
    lines.extend([
        "BOARDS",
        "  fleet/FLEET_ARCHITECTURE.txt · FLEET_FAILOVER.txt · AWS_FIX_ANYONE.txt",
        "  fleet/bus/FLEET_CHECKIN.txt",
        "  fleet/bus/FLEET_SELF_CHECK.txt",
        "  /checkin · /goal · /tv",
        "",
        "BOX WORDS",
        "  Daddy: DADDY (this box · background only)",
        "  Puppy: PUPPY + ONE_COMMAND",
        "  Uncle: UNCLE + uncle_exec on CB1 only",
        "",
        "Word: WAIT · team at 3/3 before Daddy moves",
    ])
    text = "\n".join(lines) + "\n"
    out = bus / READY
    safe_mkdir(out.parent)
    out.write_text(text, encoding="utf-8")
    _log(f"tick roll={roll} fixed={len(fixed)} wait={len(waiting)}")
    return {"now": now, "roll": roll, "fixed": fixed, "waiting": waiting}


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
        print(f"ready roll={r['roll']} · {len(r['fixed'])} fixed · {len(r['waiting'])} waiting")
        print(f"→ {bus_root() / READY}")
        return 0
    if cmd == "watch":
        sec = float(sys.argv[2]) if len(sys.argv) > 2 else INTERVAL
        watch_loop(sec)
        return 0
    print("Usage: cpt_autopilot.py once|watch [seconds]", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
