#!/usr/bin/env python3
"""Gem Live gate — Gem-controlled Gemini Live launch + transcript sink."""
from __future__ import annotations

import os
import re
import socket
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

DRIVE = Path("/mnt/shared/GoogleDrive/MyDrive")
if not DRIVE.is_dir():
    DRIVE = Path.home() / "GoogleDrive/MyDrive"

GATE_HTML = DRIVE / "lester/gem_live_gate.html"
COACH_TXT = DRIVE / "lester/gem_live_coach.txt"
LIVE_URL_FILE = DRIVE / "lester/gemini_live_url.txt"
QR_PNG = DRIVE / "drop_pile/from_cursor/GEM_LIVE_QR.png"
OUT = DRIVE / "drop_pile/from_lester"
PORT = int(os.environ.get("GEM_LIVE_PORT", "8788"))

SINK_HTML = """<!DOCTYPE html>
<html><head><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1">
<title>Gem transcript sink</title></head>
<body style="font-family:system-ui;background:#0c1f3f;color:#f5f0e6;padding:1rem;max-width:640px;margin:auto">
<h2>Gem → Drive transcript</h2>
<p style="color:#8a9bb1;font-size:.85rem">Paste Gemini Live text. Gem saves to drop_pile/from_lester/</p>
<textarea id=t rows=12 style="width:100%;font-size:16px"></textarea>
<input id=tag placeholder="tag (card1)" style="width:100%;margin:.5rem 0;font-size:16px">
<button onclick="go()" style="font-size:18px;padding:.6rem 1rem;background:#c41e3a;color:#fff;border:0;border-radius:8px">Save</button>
<pre id=o style="background:#132a4f;padding:.5rem;color:#8a9bb1"></pre>
<script>
async function go(){
  const r=await fetch('/sink/save',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({text:document.getElementById('t').value,tag:document.getElementById('tag').value})});
  document.getElementById('o').textContent=await r.text();
  if(r.ok) document.getElementById('t').value='';
}
</script></body></html>"""


def _lan_ip() -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except OSError:
        return "127.0.0.1"


def gate_url() -> str:
    return f"http://{_lan_ip()}:{PORT}/gem/live"


def write_live_url() -> str:
    url = gate_url()
    LIVE_URL_FILE.parent.mkdir(parents=True, exist_ok=True)
    LIVE_URL_FILE.write_text(
        f"# Gem-controlled Gemini Live gate · edit on Drive\n"
        f"# Updated: {datetime.now(timezone.utc).astimezone().isoformat(timespec='seconds')}\n"
        f"{url}\n",
        encoding="utf-8",
    )
    return url


def write_qr(url: str) -> Path | None:
    QR_PNG.parent.mkdir(parents=True, exist_ok=True)
    for cmd in (
        ["qrencode", "-o", str(QR_PNG), "-s", "8", "-m", "2", url],
        ["qrencode", "-o", str(QR_PNG), url],
    ):
        try:
            import subprocess

            subprocess.run(cmd, check=True, capture_output=True)
            return QR_PNG
        except (FileNotFoundError, subprocess.CalledProcessError):
            continue
    svg = QR_PNG.with_suffix(".svg")
    try:
        import subprocess

        subprocess.run(["qrencode", "-o", str(svg), "-t", "SVG", url], check=True, capture_output=True)
        return svg
    except (FileNotFoundError, subprocess.CalledProcessError):
        return None


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt: str, *args) -> None:
        return

    def _send(self, code: int, body: bytes, ctype: str = "text/html; charset=utf-8") -> None:
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path in ("/", "/gem/live"):
            html = GATE_HTML.read_text(encoding="utf-8", errors="replace") if GATE_HTML.is_file() else b"<h1>missing gate html</h1>"
            if isinstance(html, str):
                html = html.encode("utf-8")
            self._send(200, html)
            return
        if path == "/coach.txt":
            txt = COACH_TXT.read_text(encoding="utf-8", errors="replace") if COACH_TXT.is_file() else ""
            self._send(200, txt.encode("utf-8"), "text/plain; charset=utf-8")
            return
        if path == "/sink":
            self._send(200, SINK_HTML.encode("utf-8"))
            return
        if path == "/gem/qr":
            if QR_PNG.is_file():
                self._send(200, QR_PNG.read_bytes(), "image/png")
                return
            svg = QR_PNG.with_suffix(".svg")
            if svg.is_file():
                self._send(200, svg.read_bytes(), "image/svg+xml")
                return
            self._send(404, b"QR not generated - install qrencode")
            return
        if path == "/health":
            self._send(200, b'{"ok":true,"gem":"live_gate"}', "application/json")
            return
        self._send(404, b"not found")

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        if path != "/sink/save":
            self._send(404, b"not found")
            return
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length).decode("utf-8", errors="replace")
        import json

        data = json.loads(raw or "{}")
        text = (data.get("text") or "").strip()
        if not text:
            self._send(400, b'{"ok":false,"error":"empty"}', "application/json")
            return
        tag = re.sub(r"[^\w\-]", "_", (data.get("tag") or "live")[:40])
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        OUT.mkdir(parents=True, exist_ok=True)
        out = OUT / f"live_transcript_{tag}_{ts}.txt"
        out.write_text(
            f"# Gem Live transcript\n# saved: {ts}\n# gate: {gate_url()}\n\n{text}\n",
            encoding="utf-8",
        )
        body = json.dumps({"ok": True, "path": str(out), "bytes": out.stat().st_size}).encode()
        self._send(200, body, "application/json")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    url = write_live_url()
    qr = write_qr(url)
    print(f"Gem Live gate: {url}")
    if qr:
        print(f"QR: {qr}")
    else:
        print("QR: install qrencode — URL written to gemini_live_url.txt")
    server = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    print(f"listening :{PORT}")
    server.serve_forever()


if __name__ == "__main__":
    main()
