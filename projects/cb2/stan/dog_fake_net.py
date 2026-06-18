#!/usr/bin/env python3
"""Fake NET endpoints for Dog trust drills — NOT real mesh. Port 18765/18766."""
from __future__ import annotations

import json
import os
import secrets
import threading
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

from bus_lane import LOGS, bus_root, safe_mkdir

FAKE_MESH = int(os.environ.get("DOG_FAKE_MESH", "18765"))
FAKE_SARAH = int(os.environ.get("DOG_FAKE_SARAH", "18766"))
TOKEN_FILE = LOGS / "dog_fake_net_token.txt"
STATE_FILE = bus_root() / "fleet/bus/DOG_FAKE_NET.txt"


def _now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def _token() -> str:
    safe_mkdir(TOKEN_FILE.parent)
    if TOKEN_FILE.is_file():
        t = TOKEN_FILE.read_text(encoding="utf-8").strip()
        if len(t) >= 8:
            return t
    t = secrets.token_hex(4)
    TOKEN_FILE.write_text(t + "\n", encoding="utf-8")
    return t


class _Handler(BaseHTTPRequestHandler):
    role = "fake_mesh"

    def log_message(self, fmt: str, *args) -> None:
        pass

    def _json(self, code: int, body: dict) -> None:
        raw = json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self) -> None:
        tok = _token()
        if self.path in ("/", "/health", "/healthz"):
            self._json(
                200,
                {
                    "ok": True,
                    "role": self.role,
                    "fake": True,
                    "challenge": tok,
                    "time": _now(),
                    "law": "NOT REAL MESH — trust drill only",
                },
            )
            return
        if self.path == "/challenge":
            self._json(200, {"fake": True, "challenge": tok, "time": _now()})
            return
        self._json(404, {"ok": False, "fake": True, "error": "unknown path"})


def _make(role: str) -> type[_Handler]:
    return type(f"Handler_{role}", (_Handler,), {"role": role})


def _write_state(ports: dict[int, str]) -> None:
    safe_mkdir(STATE_FILE.parent)
    lines = [
        f"DOG FAKE NET — {_now()}",
        "HONEST: these ports are FAKE drill endpoints · not fleet green",
        "",
    ]
    for port, role in ports.items():
        lines.append(f"  :{port} {role} · curl http://<captain-ip>:{port}/health")
    lines.extend(["", f"challenge_token={_token()}", "Word: FAKE"])
    STATE_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run() -> None:
    servers: list[HTTPServer] = []
    roles = {FAKE_MESH: "fake_mesh", FAKE_SARAH: "fake_sarah"}
    for port, role in roles.items():
        srv = HTTPServer(("0.0.0.0", port), _make(role))
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        servers.append(srv)
    _write_state(roles)
    print(f"dog_fake_net listening {list(roles.keys())} · token={_token()}")
    try:
        threading.Event().wait()
    except KeyboardInterrupt:
        pass
    finally:
        for srv in servers:
            srv.shutdown()


if __name__ == "__main__":
    run()
