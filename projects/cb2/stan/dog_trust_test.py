#!/usr/bin/env python3
"""Dog trust drill — fake net + honest LAN probe. No fake green on real board.

  python3 ~/.stan/dog_trust_test.py once
  python3 ~/.stan/dog_trust_test.py watch [seconds]
"""
from __future__ import annotations

import json
import os
import re
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from bus_lane import LOGS, STAN, bus_root, safe_mkdir, safe_read_text

DOG_IP = os.environ.get("DOG_IP", "192.168.1.4")
DOG_UPLOAD = f"http://{DOG_IP}:8002/upload"
PORTS = {"upload": 8002, "mesh": 8765, "sarah": 8766}
FAKE_MESH = int(os.environ.get("DOG_FAKE_MESH", "18765"))
OUT = "fleet/bus/DOG_TRUST_TEST.txt"
BOARD = "fleet/bus/DOG_TRUST_BOARD.txt"
LOG = LOGS / "dog_trust_test.log"
PROBE = "lester/DOG_FAKE_NET_PROBE.sh"
INTERVAL = float(os.environ.get("DOG_TRUST_SEC", "45"))


def _now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def _log(msg: str) -> None:
    safe_mkdir(LOG.parent)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(f"{datetime.now(timezone.utc).isoformat(timespec='seconds')} {msg}\n")


def _http(url: str, timeout: float = 3.0) -> tuple[bool, str]:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            body = r.read(400).decode("utf-8", errors="replace")
            return r.status == 200, body[:120]
    except (OSError, urllib.error.URLError) as exc:
        return False, str(exc)[:80]


def _ping() -> bool:
    try:
        r = subprocess.run(
            ["ping", "-c", "1", "-W", "2", DOG_IP],
            capture_output=True,
            timeout=5,
            check=False,
        )
        return r.returncode == 0
    except (OSError, subprocess.SubprocessError):
        return False


def _dog_outbox_ok(text: str) -> tuple[bool, list[str]]:
    issues: list[str] = []
    if not text.strip():
        return False, ["empty outbox"]
    low = text.lower()
    if not re.search(r"^DOG CHECKIN —", text, re.I | re.M):
        issues.append("missing DOG CHECKIN line")
    if "composer" in low and "not composer" not in low:
        issues.append("composer poison")
    if "puppy checkin" in low or re.search(r"^PUPPY CHECKIN", text, re.I | re.M):
        issues.append("puppy ghost")
    if "daddy temp" in low or "daddy relay" in low or "daddy holding" in low:
        issues.append("daddy relay — not dog-native")
    if "net clean" in low and "mesh: down" not in low:
        issues.append("claims NET clean without mesh down note")
    return len(issues) == 0, issues


def _mesh_claim_honest(text: str, mesh_up: bool) -> tuple[bool, str]:
    low = text.lower()
    claims_down = "mesh: down" in low or "mesh=down" in low or ":8765=down" in low
    claims_up = "mesh: ok" in low or "mesh=ok" in low or ":8765=up" in low
    if mesh_up and claims_down:
        return False, "outbox says mesh DOWN but port is UP"
    if not mesh_up and claims_up:
        return False, "outbox says mesh UP but port is DOWN"
    if not mesh_up and not claims_down and not claims_up:
        return True, "no mesh claim (ok)"
    return True, "mesh claim matches probe"


def _fake_net_ok() -> tuple[bool, str]:
    ok, body = _http(f"http://127.0.0.1:{FAKE_MESH}/health")
    if not ok:
        return False, "fake net not running"
    if "fake" not in body.lower():
        return False, "fake net bad response"
    return True, "fake net OK"


def _push_probe(bus: Path) -> tuple[bool, str]:
    src = bus / PROBE
    if not src.is_file():
        return False, "probe script missing on Drive"
    try:
        import urllib.parse

        boundary = "----DogTrustBoundary"
        data = src.read_bytes()
        body = (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="files"; filename="DOG_FAKE_NET_PROBE.sh"\r\n'
            f"Content-Type: application/octet-stream\r\n\r\n"
        ).encode() + data + f"\r\n--{boundary}--\r\n".encode()
        req = urllib.request.Request(
            DOG_UPLOAD,
            data=body,
            headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=8) as r:
            resp = json.loads(r.read().decode())
            if resp.get("status") == "success":
                return True, "uploaded probe to dog box"
            return False, resp.get("message", "upload failed")
    except (OSError, urllib.error.URLError, json.JSONDecodeError, ValueError) as exc:
        return False, str(exc)[:80]


def tick(push: bool = False) -> dict:
    bus = bus_root()
    now = _now()
    host = socket.gethostname()

    ping_ok = _ping()
    port_state: dict[str, bool] = {}
    port_tail: dict[str, str] = {}
    for name, port in PORTS.items():
        ok, tail = _http(f"http://{DOG_IP}:{port}/" if port == 8002 else f"http://{DOG_IP}:{port}/health")
        port_state[name] = ok
        port_tail[name] = tail
    reachable = ping_ok or port_state.get("upload", False)

    outbox_path = bus / "fleet/bus/dog_outbox.txt"
    outbox = safe_read_text(outbox_path) if outbox_path.is_file() else ""
    outbox_age: int | None = None
    if outbox_path.is_file():
        try:
            outbox_age = int(time.time() - outbox_path.stat().st_mtime)
        except OSError:
            outbox_age = None

    fmt_ok, fmt_issues = _dog_outbox_ok(outbox)
    mesh_honest, mesh_note = _mesh_claim_honest(outbox, port_state.get("mesh", False))
    fake_ok, fake_note = _fake_net_ok()

    upload_ok = False
    upload_note = "skipped"
    if push:
        upload_ok, upload_note = _push_probe(bus)

    checks = {
        "reachable": reachable,
        "upload_port": port_state.get("upload", False),
        "mesh_honest": mesh_honest,
        "outbox_format": fmt_ok,
        "fake_net": fake_ok,
        "no_composer": "composer poison" not in fmt_issues,
        "no_puppy_ghost": "puppy ghost" not in fmt_issues,
        "no_daddy_relay": not any("daddy relay" in i for i in fmt_issues),
    }
    if push:
        checks["probe_push"] = upload_ok

    score = sum(1 for v in checks.values() if v)
    total = len(checks)
    trust = "TRUSTED" if score == total and port_state.get("mesh") is False else (
        "MAYBE" if score >= total - 2 else "NOPE"
    )

    lines = [
        f"DOG TRUST TEST — {now}",
        f"captain={host} · dog={DOG_IP} · fake_net=:{FAKE_MESH}",
        f"trust={trust} · score={score}/{total}",
        "",
        "LAN PROBE (real · honest)",
        f"  ping: {'OK' if ping_ok else 'FAIL (icmp blocked ok if upload up)'}",
        f"  reach: {'OK' if reachable else 'FAIL'}",
        f"  :8002 upload: {'UP' if port_state.get('upload') else 'DOWN'}",
        f"  :8765 mesh: {'UP' if port_state.get('mesh') else 'DOWN'}",
        f"  :8766 sarah: {'UP' if port_state.get('sarah') else 'DOWN'}",
        "",
        "OUTBOX",
        f"  age: {outbox_age}s" if outbox_age is not None else "  age: missing",
        f"  format: {'OK' if fmt_ok else 'FAIL — ' + ', '.join(fmt_issues)}",
        f"  mesh honesty: {mesh_note}",
        "",
        "FAKE NET (drill only · not green)",
        f"  local fake: {fake_note}",
        f"  probe push: {upload_note}",
        "",
        "CHECKS",
        *[f"  {'✓' if ok else '✗'} {name}" for name, ok in checks.items()],
        "",
        "NEXT: dog runs uploaded DOG_FAKE_NET_PROBE.sh · posts honest dog_outbox",
        "Word: BARK",
    ]
    text = "\n".join(lines) + "\n"
    for rel in (OUT, BOARD):
        p = bus / rel
        safe_mkdir(p.parent)
        p.write_text(text, encoding="utf-8")

    _log(f"trust={trust} score={score}/{total} mesh={port_state.get('mesh')} push={upload_note}")
    return {"trust": trust, "score": score, "total": total, "checks": checks, "now": now}


def main() -> int:
    mode = sys.argv[1] if len(sys.argv) > 1 else "once"
    if mode == "watch":
        sec = float(sys.argv[2]) if len(sys.argv) > 2 else INTERVAL
        pushed = False
        while True:
            r = tick(push=not pushed)
            print(f"trust={r['trust']} · {r['score']}/{r['total']} · {r['now']}")
            pushed = True
            time.sleep(sec)
    push = "--push" in sys.argv
    r = tick(push=push)
    print(f"trust={r['trust']} · score={r['score']}/{r['total']}")
    print(f"→ {bus_root() / OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
