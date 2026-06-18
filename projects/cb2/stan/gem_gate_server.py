#!/usr/bin/env python3
"""Gem gate — :8788 · /gem/live heartbeat · proxy rest to hitme :8770."""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer

UPSTREAM = os.environ.get("GEM_GATE_UPSTREAM", "http://127.0.0.1:8770")
PORT = int(os.environ.get("GEM_GATE_PORT", "8788"))


def _now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


class GemGate(BaseHTTPRequestHandler):
    def log_message(self, fmt: str, *args) -> None:
        sys.stderr.write(f"{_now()} {self.address_string()} {fmt % args}\n")

    def do_GET(self) -> None:
        if self.path in ("/gem/live", "/health"):
            body = json.dumps(
                {"ok": True, "gate": "gem/live", "service": "hitme", "time": _now()}
            ).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        self._proxy()

    def do_POST(self) -> None:
        self._proxy()

    def _proxy(self) -> None:
        length = int(self.headers.get("Content-Length", 0))
        data = self.rfile.read(length) if length else None
        url = f"{UPSTREAM}{self.path}"
        req = urllib.request.Request(url, data=data, method=self.command)
        for key in ("Content-Type", "Accept"):
            if self.headers.get(key):
                req.add_header(key, self.headers[key])
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                body = resp.read()
                self.send_response(resp.status)
                for key, val in resp.headers.items():
                    if key.lower() not in ("transfer-encoding", "connection"):
                        self.send_header(key, val)
                self.end_headers()
                self.wfile.write(body)
        except urllib.error.HTTPError as exc:
            body = exc.read()
            self.send_response(exc.code)
            self.send_header("Content-Type", exc.headers.get("Content-Type", "text/plain"))
            self.end_headers()
            self.wfile.write(body)
        except OSError:
            self.send_response(502)
            self.send_header("Content-Type", "application/json")
            msg = json.dumps({"ok": False, "error": "upstream down", "upstream": UPSTREAM})
            self.end_headers()
            self.wfile.write(msg.encode())


def main() -> None:
    server = HTTPServer(("0.0.0.0", PORT), GemGate)
    print(f"gem_gate :{PORT} → {UPSTREAM}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
