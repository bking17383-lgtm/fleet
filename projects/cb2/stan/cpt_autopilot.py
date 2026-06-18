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

    try:
        from daddy_team_say import announce

        announce("autopilot tick start", "delegate-only · no silent bus writes")
    except ImportError:
        pass

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

    # Bunny alive = native FROM_BUNNY (puppy_outbox lane retired)
    bunny_text = (
        safe_read_text(bus / "fleet/indie_loop/FROM_BUNNY.txt")
        if safe_is_file(bus / "fleet/indie_loop/FROM_BUNNY.txt")
        else ""
    )
    bunny_native = (
        bunny_text.strip() != "waiting for bunny"
        and "FROM_BUNNY" in bunny_text
        and "bridged-by" not in bunny_text.lower()
    )
    bunny_age = _mtime_age(bus, "fleet/indie_loop/FROM_BUNNY.txt")[1]

    # Legacy puppy_outbox — ignore for roll (DEAD_WORDS)
    puppy_live = False
    if puppy_live:
        for name, preset in (("mesh", "mesh"), ("sarah", "sarah")):
            pup = bus / "fleet/bus/cpt_to_puppy.txt"
            tag = f"delegate {name}:"
            if not safe_is_file(pup) or tag not in safe_read_text(pup)[-800:]:
                _run_py("daddy_delegate.py", "puppy", preset if preset != "mesh" else "checkin")
                fixed.append(f"delegated {name} → Puppy")
    else:
        _run_py("daddy_takeover.py", "once", timeout=45)
        fixed.append("Daddy TEMP services on penguin (bunny/native NET not live)")
        if not _http(8765):
            waiting.append("mesh :8765 still down on Daddy — check logs/mesh_radio.log")
        if not _http(8766):
            waiting.append("sarah :8766 still down on Daddy — check logs/sarah.log")
    for match, cmd in (
        ("fleet_self_check.py watch", f"python3 {STAN}/fleet_self_check.py watch 25"),
        ("brian_router.py watch", f"python3 {STAN}/brian_router.py watch 12"),
        ("cpt_bunny_watch.sh", f"bash {STAN}/cpt_bunny_watch.sh"),
        ("hitme_always.sh", f"bash {STAN}/hitme_always.sh"),
    ):
        if a := _ensure_bg(match, cmd):
            fixed.append(a)

    try:
        from daddy_indie_status import snapshot, write_cpt_bunny_loop

        bunny_snap = snapshot(bus)
        write_cpt_bunny_loop()
        if bunny_snap["watch"] == "LIVE":
            fixed.append(f"bunny loop watch LIVE · daddy_post {bunny_snap['daddy_post']}")
        else:
            waiting.append("Bunny loop watch DOWN — bash ~/.stan/cpt_bunny_watch.sh")
        if bunny_snap["bunny_live"] == "SILENT":
            waiting.append(f"Bunny box SILENT — {bunny_snap['bunny_head'][:60]}")
    except ImportError:
        waiting.append("daddy_indie_status missing — bunny loop blind")

    if not bunny_native:
        waiting.append("Bunny not native on bus — run bbunny_loop on Bunny box (not bridged-by-cb1)")

    # Puppy lane retired — do not wait on puppy_outbox

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
    grab_hold = safe_is_file(bus / "fleet/bus/GEM_GRAB_HOLD.txt") and "hold=YES" in safe_read_text(
        bus / "fleet/bus/GEM_GRAB_HOLD.txt"
    )
    if not grab_hold and (ping_age is None or ping_age > 300):
        _run_py("cpt_gem_loop.py", "ping", timeout=20)
        fixed.append("loop ping → Gem+Uncle inbox")
    elif grab_hold:
        fixed.append("GEM GRAB HOLD — ping skipped · cpt_to_gem protected")
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
            "brian_fix=CB1 keyboard · read DADDY_DOWN_FIX.txt\n"
            "pickup=Clerk Drive bridge · Uncle execute · NOT captain promotion\n"
            "read: fleet/DADDY_FAILOVER.txt · fleet/FLEET_FAILOVER.txt\n"
        )
        failover.write_text(fo, encoding="utf-8")
        waiting.append("Clerk stale — Brian on CB1 Chrome · read DEAD_WORDS.txt")
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

    # Picture inbox — OCR + execute (sandbox if unclear)
    if _run_py("picture_inbox_watch.py", "once", timeout=90):
        fixed.append("picture inbox scanned")

    # Roll call only — no local repair crew (delegate all)
    _run_py("fleet_checkin.py", "once", timeout=15)

    checkin = safe_read_text(bus / "fleet/bus/FLEET_CHECKIN.txt")
    roll_m = re.search(r"roll=(\d+/(\d+))", checkin)
    roll = roll_m.group(1) if roll_m else "?/?"

    repair = safe_read_text(bus / "fleet/bus/REPAIR_NOW.txt") if safe_is_file(bus / "fleet/bus/REPAIR_NOW.txt") else ""

    ready_loop = STAN / "logs/daddy_ready_loop.json"
    loop_active = False
    if ready_loop.is_file():
        try:
            import json

            loop_active = bool(json.loads(ready_loop.read_text(encoding="utf-8")).get("active"))
        except (json.JSONDecodeError, OSError):
            loop_active = False

    if loop_active:
        lines = [
            f"DADDY READY LOOP — {now}",
            "mode=FREE · looping \"I need a job.\" until Brian answers",
            "",
            "Audio: https://hitme.dev/ready/daddy.mp3",
            "Page:  https://hitme.dev/ready?loop=daddy",
            "",
            "DELEGATED THIS TICK",
            *([f"  • {x}" for x in fixed[:8]] if fixed else ["  • (none)"]),
            "",
        ]
    else:
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
    try:
        from daddy_indie_status import snapshot

        bs = snapshot(bus)
        lines.extend(
            [
                "BUNNY INDIE LOOP (read fleet/bus/CPT_BUNNY_LOOP.txt)",
                f"  watch={bs['watch']} · daddy_post={bs['daddy_post']} ({bs['daddy_age']})",
                f"  bunny={bs['bunny_live']} · job={bs['job'][:80]}",
                f"  ui: /bunny · /inbox · TO_BUNNY.txt",
                "",
            ]
        )
    except ImportError:
        pass
    lines.extend([
        "BOARDS",
        "  fleet/FLEET_ARCHITECTURE.txt · FLEET_FAILOVER.txt · AWS_FIX_ANYONE.txt",
        "  fleet/bus/FLEET_CHECKIN.txt",
        "  fleet/bus/FLEET_SELF_CHECK.txt",
        "  /checkin · /goal · /tv",
        "",
        "BOX WORDS",
        "  Daddy: DADDY (this box · background only)",
        "  Bunny: BUNNY (builder · indie_loop)",
        "  Uncle: UNCLE + uncle_exec on CB1 only",
        "  Clerk: CLERK (CB1 Chrome · was Gem)",
        "",
        "DEAD: DOG · PUPPY lane · fleet/DEAD_WORDS.txt",
        "Word: WAIT · team at 3/3 before Daddy moves",
    ])
    text = "\n".join(lines) + "\n"
    out = bus / READY
    safe_mkdir(out.parent)
    out.write_text(text, encoding="utf-8")
    _log(f"tick roll={roll} fixed={len(fixed)} wait={len(waiting)}")
    try:
        from daddy_team_say import announce

        announce(
            "autopilot tick done",
            f"roll={roll} · fixed={len(fixed)} · waiting={len(waiting)}",
        )
    except ImportError:
        pass
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
