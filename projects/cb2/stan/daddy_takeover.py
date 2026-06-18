#!/usr/bin/env python3
"""Daddy owns all roles · delegates when boxes live · TEMP takeover when absent.

  python3 ~/.stan/daddy_takeover.py once      # check fleet · hold dead roles on penguin
  python3 ~/.stan/daddy_takeover.py status
  python3 ~/.stan/daddy_takeover.py puppy     # force NET temp on Daddy
  python3 ~/.stan/daddy_takeover.py release   # drop temp when box returns

Law: fleet/DADDY_OWNS_ALL.txt
"""
from __future__ import annotations

import socket
import subprocess
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from bus_lane import STAN, bus_root, safe_is_file, safe_mkdir, safe_read_text

BUS = bus_root()
STALE = 120
CB1_STALE = 600
HOLD = BUS / "fleet/bus/DADDY_TEMPROLE.txt"
PUPPY_OUT = BUS / "fleet/bus/puppy_outbox.txt"
GEM_OUT = BUS / "fleet/bus/gem_to_cpt.txt"
UNCLE_OUT = BUS / "fleet/bus/uncle_to_cpt.txt"


def _now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def _host() -> str:
    return socket.gethostname()


def _mtime_age(path: Path) -> float | None:
    try:
        if not path.is_file():
            return None
        ts = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
        return (datetime.now(timezone.utc) - ts).total_seconds()
    except OSError:
        return None


def _http(port: int) -> bool:
    for path in ("/health", "/status", "/"):
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{port}{path}", timeout=2) as r:
                if r.status == 200:
                    return True
        except OSError:
            continue
    return False


def _ensure_bg(match: str, cmd: str, log_name: str) -> bool:
    try:
        r = subprocess.run(["pgrep", "-f", match], capture_output=True)
        if r.returncode == 0:
            return True
        log = STAN / "logs" / log_name
        safe_mkdir(log.parent)
        subprocess.Popen(
            ["bash", "-c", cmd],
            stdout=open(log, "a", encoding="utf-8"),
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
        return True
    except OSError:
        return False


def _puppy_live() -> bool:
    if not PUPPY_OUT.is_file():
        return False
    text = safe_read_text(PUPPY_OUT)
    if "DADDY TEMP" in text or "Daddy holding" in text:
        return False
    age = _mtime_age(PUPPY_OUT)
    if age is None or age > STALE:
        return False
    return "PUPPY CHECKIN" in text or "NET clean" in text


def _cb1_gem_live() -> bool:
    if not GEM_OUT.is_file():
        return False
    text = safe_read_text(GEM_OUT)
    if "penguin" in text.lower():
        return False
    age = _mtime_age(GEM_OUT)
    return age is not None and age <= CB1_STALE and bool(
        __import__("re").search(r"GEM (ok|REFUSE)", text, __import__("re").I)
    )


def _cb1_uncle_live() -> bool:
    if not UNCLE_OUT.is_file():
        return False
    text = safe_read_text(UNCLE_OUT)
    if "penguin" in text.lower():
        return False
    age = _mtime_age(UNCLE_OUT)
    return age is not None and age <= CB1_STALE and bool(
        __import__("re").search(r"UNCLE (CHECKIN|clean) — cb1", text, __import__("re").I | __import__("re").M)
    )


def _announce(msg: str, detail: str = "") -> None:
    try:
        from daddy_team_say import announce

        announce(msg, detail, targets="all")
    except ImportError:
        pass


def takeover_puppy() -> list[str]:
    fixed: list[str] = []
    ip = subprocess.getoutput("hostname -I").split()[0] if subprocess.getoutput("hostname -I") else "?"
    now = _now()

    if _ensure_bg("hitme_who_server.py", f"python3 {STAN}/hitme_who_server.py", "hitme_who.log"):
        fixed.append("hitme :8770")
    if _ensure_bg("mesh_radio.py", f"python3 {STAN}/mesh_radio.py", "mesh_radio.log"):
        fixed.append("mesh :8765 starting")
    if _ensure_bg("sarah_voice_sample.py", f"python3 {STAN}/sarah_voice_sample.py", "sarah.log"):
        fixed.append("sarah :8766 starting")

    m8765 = "UP" if _http(8765) else "DOWN"
    m8766 = "UP" if _http(8766) else "DOWN"
    m8770 = "UP" if _http(8770) else "DOWN"

    PUPPY_OUT.parent.mkdir(parents=True, exist_ok=True)
    PUPPY_OUT.write_text(
        f"PUPPY TEMP — Daddy holding NET — {_host()} — {ip} — {now}\n"
        f"puppy64: ABSENT (wiped or stale)\n"
        f"daddy_ports: :8765={m8765} :8766={m8766} :8770={m8770}\n"
        f"law: fleet/DADDY_OWNS_ALL.txt\n"
        f"release: real PUPPY CHECKIN from puppy64 replaces this\n",
        encoding="utf-8",
    )
    fixed.append(f"posted DADDY TEMP puppy_outbox · ports 8765={m8765} 8766={m8766}")
    _announce("Daddy TEMP NET", f"puppy absent · holding :8765 :8766 :8770 on penguin")
    return fixed


def takeover_cb1() -> list[str]:
    fixed: list[str] = []
    now = _now()
    if not _cb1_gem_live():
        subprocess.run([sys.executable, str(STAN / "cpt_gem_loop.py"), "forward"], check=False)
        subprocess.run([sys.executable, str(STAN / "cpt_gem_loop.py"), "listen"], check=False)
        fixed.append("Daddy holding Gem orders (cpt_to_gem · ack)")
    if not _cb1_uncle_live():
        subprocess.run([sys.executable, str(STAN / "cpt_uncle_sync.py")], check=False)
        subprocess.run([sys.executable, str(STAN / "cpt_gem_loop.py"), "ping"], check=False)
        fixed.append("Daddy holding Uncle orders (cpt_to_uncle · ack)")
    _announce("Daddy TEMP CB1", "orders on bus until cb1 posts fresh")
    return fixed


def write_hold_file(roles: dict[str, str]) -> None:
    lines = [
        f"DADDY TEMPROLE — {_now()}",
        f"host: {_host()}",
        "law: Daddy owns all · delegates when live · temp when dead",
        "",
    ]
    for role, state in roles.items():
        lines.append(f"  {role}: {state}")
    lines.extend(
        [
            "",
            "Brian: one door http://127.0.0.1:8770/goal",
            "Release: box posts real checkin · Daddy drops temp same tick",
        ]
    )
    HOLD.parent.mkdir(parents=True, exist_ok=True)
    HOLD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def once() -> dict:
    roles: dict[str, str] = {}
    fixed: list[str] = []

    if _puppy_live():
        roles["puppy"] = "DELEGATED (puppy64 live)"
    else:
        fixed.extend(takeover_puppy())
        roles["puppy"] = "DADDY TEMP NET on penguin"

    if _cb1_gem_live() and _cb1_uncle_live():
        roles["cb1"] = "DELEGATED (cb1 live)"
    elif _cb1_gem_live() or _cb1_uncle_live():
        roles["cb1"] = "PARTIAL · one hat on · Daddy fills other lane orders"
        fixed.extend(takeover_cb1())
    else:
        fixed.extend(takeover_cb1())
        roles["cb1"] = "DADDY TEMP orders on bus (cb1 silent)"

    roles["daddy"] = "OWNER · dashboard :8770"
    write_hold_file(roles)
    return {"roles": roles, "fixed": fixed}


def status() -> str:
    r = once()
    lines = [f"DADDY OWNS ALL — {_now()}", ""]
    for k, v in r["roles"].items():
        lines.append(f"  {k}: {v}")
    if r["fixed"]:
        lines.extend(["", "THIS TICK", *[f"  • {x}" for x in r["fixed"]]])
    lines.append(f"\n→ {HOLD}")
    return "\n".join(lines)


def main() -> int:
    cmd = (sys.argv[1] if len(sys.argv) > 1 else "once").lower()
    if cmd == "once":
        print(status())
        return 0
    if cmd == "status":
        print(status())
        return 0
    if cmd == "puppy":
        for x in takeover_puppy():
            print(x)
        return 0
    if cmd == "release":
        print("release when real checkins fresh — run once")
        once()
        return 0
    print("Usage: daddy_takeover.py once|status|puppy|release", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
