#!/usr/bin/env python3
"""
Sarah appointment voice sample — integrity echo + confirm + SNAP/OCR post-its.
NOT an LLM. Browser TTS out; mic needs HTTPS on phone (use /tunnel or TYPE/SNAP).

  python3 ~/.stan/sarah_voice_sample.py
  http://127.0.0.1:8766/sarah
  http://127.0.0.1:8766/qr   — phone link (set LAN IP if QR wrong)
"""
from __future__ import annotations

import base64
import json
import os
import re
import socket
import subprocess
import tempfile
import time
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

from flask import Flask, jsonify, request, send_file

from bus_lane import bus_root, safe_is_file, safe_read_text, safe_mkdir, STAN, LOGS

PORT = int(os.environ.get("SARAH_PORT", "8766"))
BUS = bus_root()
DRIVE = BUS
POSTIT_DIR = DRIVE / "lester" / "sarah" / "postits"
POSTIT_LOG = POSTIT_DIR / "POSTITS.txt"
PHONE_URL_FILE = DRIVE / "fleet" / "SARAH_PHONE_URL.txt"
HTTPS_URL_FILE = DRIVE / "fleet" / "SARAH_VOICE_URL.txt"
KID_FACE = DRIVE / "lester" / "sarah" / "assets" / "KID_FACE_BTN.jpg"
CAL_DIR = DRIVE / "lester" / "sarah" / "calendar"
CAL_INBOX = CAL_DIR / "inbox.ics"
ICAL_URL_FILE = Path.home() / ".stan" / "secrets" / "sarah_ical.url"
LOG = LOGS / "SARAH_VOICE_LOG.txt"
DEV_LOG = LOGS / "SARAH_DEV_LOG.txt"
DEV_RING: list[str] = []
DEV_RING_MAX = 200

app = Flask(__name__)
state: dict = {"step": 0, "draft": None, "confirmed": False}


def _log(msg: str) -> None:
    safe_mkdir(LOG.parent)
    try:
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(f"{datetime.now().isoformat()} {msg}\n")
    except OSError:
        pass


def _dev(event: str, detail: str = "") -> None:
    ts = datetime.now().isoformat(timespec="seconds")
    line = f"{ts}\t{event}\t{detail}" if detail else f"{ts}\t{event}"
    DEV_RING.append(line)
    if len(DEV_RING) > DEV_RING_MAX:
        del DEV_RING[: len(DEV_RING) - DEV_RING_MAX]
    safe_mkdir(DEV_LOG.parent)
    try:
        with open(DEV_LOG, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except OSError:
        pass


def _ics_unfold(text: str) -> str:
    out: list[str] = []
    for line in text.splitlines():
        if line.startswith((" ", "\t")) and out:
            out[-1] += line[1:]
        else:
            out.append(line)
    return "\n".join(out)


def _ics_field(block: str, key: str) -> str | None:
    for line in _ics_unfold(block).splitlines():
        if line.startswith(key + ";") or line.startswith(key + ":"):
            val = line.split(":", 1)[-1].strip()
            return val.replace("\\n", "\n").replace("\\,", ",")
    return None


def _ics_dt(raw: str | None) -> datetime | None:
    if not raw:
        return None
    raw = raw.strip()
    if len(raw) == 8 and raw.isdigit():
        return datetime.strptime(raw, "%Y%m%d")
    for fmt in ("%Y%m%dT%H%M%SZ", "%Y%m%dT%H%M%S"):
        try:
            return datetime.strptime(raw, fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            pass
    if "T" in raw and len(raw) >= 15:
        try:
            return datetime.strptime(raw[:15], "%Y%m%dT%H%M%S")
        except ValueError:
            pass
    return None


def _parse_ics(text: str) -> list[dict]:
    events: list[dict] = []
    for chunk in text.split("BEGIN:VEVENT")[1:]:
        block = chunk.split("END:VEVENT")[0]
        start = _ics_dt(_ics_field(block, "DTSTART"))
        if not start:
            continue
        summary = _ics_field(block, "SUMMARY") or "(no title)"
        desc = _ics_field(block, "DESCRIPTION") or ""
        events.append({
            "start": start.isoformat(),
            "summary": summary,
            "description": desc[:200],
        })
    events.sort(key=lambda e: e["start"])
    return events


def _load_calendar() -> tuple[list[dict], str]:
    """Sarah opts in — read ICS file or secret iCal URL (local only). No Google login."""
    sources: list[str] = []
    merged: list[dict] = []
    if CAL_INBOX.is_file():
        try:
            merged.extend(_parse_ics(CAL_INBOX.read_text(encoding="utf-8", errors="replace")))
            sources.append("inbox.ics")
        except OSError as e:
            _dev("calendar_err", f"inbox {e}")
    sample = CAL_DIR / "sample.ics"
    if sample.is_file() and not sources:
        try:
            merged.extend(_parse_ics(sample.read_text(encoding="utf-8", errors="replace")))
            sources.append("sample.ics")
        except OSError:
            pass
    if ICAL_URL_FILE.is_file():
        url = ICAL_URL_FILE.read_text(encoding="utf-8").strip().splitlines()[0]
        if url.startswith("http"):
            try:
                with urllib.request.urlopen(url, timeout=15) as resp:
                    body = resp.read().decode("utf-8", errors="replace")
                merged.extend(_parse_ics(body))
                sources.append("ical-url")
            except Exception as e:
                _dev("calendar_err", f"url {e}")
    # dedupe by start+summary
    seen: set[tuple[str, str]] = set()
    unique: list[dict] = []
    for ev in sorted(merged, key=lambda e: e["start"]):
        key = (ev["start"], ev["summary"])
        if key in seen:
            continue
        seen.add(key)
        unique.append(ev)
    now = datetime.now(timezone.utc)
    upcoming = []
    for ev in unique:
        try:
            dt = datetime.fromisoformat(ev["start"])
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
        except ValueError:
            upcoming.append(ev)
            continue
        if dt >= now - timedelta(days=1):
            upcoming.append(ev)
    _dev("calendar", f"n={len(upcoming)} src={','.join(sources) or 'none'}")
    return upcoming[:20], ",".join(sources) or "none"


def _guess_lan_ip() -> str | None:
    """Best-effort LAN IP for same-WiFi phone (not Tailscale)."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        if ip.startswith("100.64.") or ip.startswith("100.115."):
            pass
        elif ip.startswith("192.168.") or ip.startswith("10.") or ip.startswith("172."):
            return ip
    except OSError:
        pass
    for line in subprocess.check_output(["ip", "-4", "addr"], text=True).splitlines():
        m = re.search(r"inet (192\.168\.\d+\.\d+)", line)
        if m:
            return m.group(1)
    if safe_is_file(PHONE_URL_FILE):
        t = safe_read_text(PHONE_URL_FILE).strip()
        m = re.search(r"https?://([^/:]+)", t)
        if m and not m.group(1).startswith("127."):
            return m.group(1)
    return None


def _phone_base_url() -> str:
    if safe_is_file(PHONE_URL_FILE):
        line = safe_read_text(PHONE_URL_FILE).strip().splitlines()[0]
        if line.startswith("http"):
            return line.rstrip("/")
    lan = _guess_lan_ip()
    if lan:
        return f"http://{lan}:{PORT}"
    host = request.host.split(":")[0] if request else "127.0.0.1"
    if host in ("127.0.0.1", "localhost"):
        lan = _guess_lan_ip()
        if lan:
            return f"http://{lan}:{PORT}"
    return f"http://{request.host}" if request else f"http://127.0.0.1:{PORT}"


def _ocr_image(path: Path) -> str:
    try:
        r = subprocess.run(
            ["tesseract", str(path), "stdout", "-l", "eng"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if r.returncode == 0:
            return re.sub(r"\s+", " ", r.stdout).strip()
    except (FileNotFoundError, subprocess.TimeoutExpired) as e:
        _log(f"ocr fail {e}")
    return ""


def _save_postit(image_bytes: bytes) -> tuple[Path, str]:
    POSTIT_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    img_path = POSTIT_DIR / f"postit_{ts}.jpg"
    img_path.write_bytes(image_bytes)
    text = _ocr_image(img_path)
    line = f"{ts}\t{text or '(no text read)'}\t{img_path.name}\n"
    with open(POSTIT_LOG, "a", encoding="utf-8") as f:
        f.write(line)
    _log(f"postit {img_path.name} ocr={text[:80]!r}")
    return img_path, text


def _next_reply() -> dict:
    step = state["step"]
    if step == 0:
        state["step"] = 1
        return {
            "say": "Hi Sarah. I'm the appointment helper. Tell me what you need, or tap the photo to snap a post-it.",
            "expect": "input",
            "hint": "Say or type your request. Mic needs HTTPS — use Snap or Type on Wi-Fi.",
        }
    if step == 1:
        draft = state.get("draft") or "your appointment"
        state["step"] = 2
        return {
            "say": f"I heard: {draft}. Is that right? Say yes or no, or tap Yes / No.",
            "expect": "confirm",
            "draft": draft,
        }
    if step == 2:
        if state.get("confirmed"):
            state["step"] = 3
            return {
                "say": "Good. Want me to bundle anything else for that day? Like school pickup or bring something?",
                "expect": "input",
            }
        state["step"] = 1
        state["draft"] = None
        return {"say": "Okay, tell me again.", "expect": "input"}
    if step == 3:
        state["step"] = 4
        events, _ = _load_calendar()
        extra = ""
        if events:
            names = "; ".join(e["summary"] for e in events[:2])
            extra = f" I also see on your calendar: {names}."
        return {
            "say": "Sample: school event Thursday — I'll remind you to bring the permission slip and check peanut rules."
            + extra,
            "expect": "none",
        }
    return {"say": "That's the demo. Snap a post-it or type anytime.", "expect": "input"}


SARAH_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Sarah — appointment helper</title>
<style>
  * { box-sizing: border-box; }
  body { font-family: system-ui, sans-serif; max-width: 32rem; margin: 0 auto; padding: 1rem;
    background: #1a1a2e; color: #eee; min-height: 100vh; }
  h1 { font-size: 1.25rem; color: #e94560; }
  .bubble { background: #16213e; border-radius: 12px; padding: 1rem; margin: 1rem 0; min-height: 3rem; }
  .row { display: flex; gap: 0.5rem; flex-wrap: wrap; margin: 0.5rem 0; }
  button { padding: 0.75rem 1rem; font-size: 1rem; border: none; border-radius: 8px;
    background: #e94560; color: #fff; cursor: pointer; }
  button.secondary { background: #0f3460; }
  button:active { opacity: 0.85; }
  input, textarea { width: 100%; padding: 0.75rem; font-size: 1rem; border-radius: 8px;
    border: 1px solid #333; background: #0f3460; color: #fff; }
  textarea { min-height: 4rem; resize: vertical; }
  #status { font-size: 0.85rem; color: #aaa; margin-top: 0.5rem; }
  .warn { color: #ffb347; font-size: 0.9rem; margin: 0.5rem 0; }
  .ok { color: #7bed9f; }
  #snapPreview { max-width: 100%; border-radius: 8px; margin-top: 0.5rem; display: none; }
  label.snap { display: block; padding: 1rem; background: #0f3460; border-radius: 8px;
    text-align: center; cursor: pointer; border: 2px dashed #e94560; }
  label.snap input { display: none; }
  a { color: #7bed9f; }
  .face-btn { display: block; width: 7.5rem; height: 7.5rem; margin: 0.75rem auto 0.25rem;
    border-radius: 50%; border: 3px solid #e94560; padding: 0; overflow: hidden;
    background: #0f3460; cursor: pointer; box-shadow: 0 4px 18px rgba(233,69,96,0.35); }
  .face-btn img { width: 100%; height: 100%; object-fit: cover; display: block; }
  .face-caption { text-align: center; font-size: 0.9rem; color: #ccc; margin-bottom: 0.75rem; }
  .schedule { background: #16213e; border-radius: 8px; padding: 0.75rem; margin: 0.5rem 0; font-size: 0.85rem; }
  .schedule ul { margin: 0.35rem 0 0 1rem; padding: 0; }
  .schedule li { margin: 0.25rem 0; color: #ccc; }
</style>
</head>
<body>
<h1>Appointment helper</h1>
<p class="warn" id="micWarn"></p>
<div class="schedule" id="scheduleBox" style="display:none">
  <strong>Schedule (Sarah shared)</strong>
  <ul id="scheduleList"></ul>
</div>
<div class="bubble" id="assistant">Loading…</div>
<div class="row" id="confirmRow" style="display:none">
  <button type="button" id="yesBtn">Yes</button>
  <button type="button" id="noBtn" class="secondary">No</button>
</div>
<textarea id="typed" placeholder="Type here if mic doesn't work…"></textarea>
<div class="row">
  <button type="button" id="sendBtn">Send</button>
  <button type="button" id="listenBtn" class="secondary">🎤 Hold to talk</button>
</div>
<label class="snap" id="snapLabel">
  <span class="face-btn" aria-hidden="true"><img src="/assets/kid-face.jpg" alt=""></span>
  <span class="face-caption">Snap post-it — tap photo</span>
  <input type="file" id="snapInput" accept="image/*" capture="environment">
</label>
<img id="snapPreview" alt="post-it preview">
<div id="status"></div>
<p style="font-size:0.85rem"><a href="/qr">Phone QR / link</a> · <a href="/dev">dev log</a></p>
<script>
const assistant = document.getElementById('assistant');
const status = document.getElementById('status');
const micWarn = document.getElementById('micWarn');
const confirmRow = document.getElementById('confirmRow');
const secureMic = location.protocol === 'https:' || location.hostname === 'localhost' || location.hostname === '127.0.0.1';

if (!secureMic) {
  micWarn.textContent = 'Voice-in needs HTTPS on phone. Type or Snap post-it works on Wi-Fi.';
  fetch('/api/voice_url').then(r => r.json()).then(d => {
    if (d.url) micWarn.innerHTML = 'For mic: <a href="' + d.url + '">' + d.url + '</a> — or Type / Snap below.';
  }).catch(() => {});
}

function speak(text) {
  if (!text) return;
  speechSynthesis.cancel();
  const u = new SpeechSynthesisUtterance(text);
  u.rate = 0.95;
  speechSynthesis.speak(u);
  assistant.textContent = text;
}

async function api(path, body) {
  const r = await fetch(path, {
    method: body ? 'POST' : 'GET',
    headers: body ? {'Content-Type': 'application/json'} : {},
    body: body ? JSON.stringify(body) : undefined
  });
  return r.json();
}

function showConfirm(show) {
  confirmRow.style.display = show ? 'flex' : 'none';
}

async function applyReply(data) {
  if (data.say) speak(data.say);
  showConfirm(data.expect === 'confirm');
  status.textContent = data.hint || '';
  if (data.draft) status.textContent = 'Draft: ' + data.draft;
}

async function sendText(text) {
  if (!text || !text.trim()) return;
  status.textContent = 'Sending…';
  const data = await api('/api/text', { text: text.trim() });
  await applyReply(data);
  document.getElementById('typed').value = '';
}

document.getElementById('sendBtn').onclick = () => sendText(document.getElementById('typed').value);

document.getElementById('yesBtn').onclick = async () => {
  const data = await api('/api/confirm', { yes: true });
  await applyReply(data);
};
document.getElementById('noBtn').onclick = async () => {
  const data = await api('/api/confirm', { yes: false });
  await applyReply(data);
};

document.getElementById('snapInput').onchange = async (e) => {
  const file = e.target.files[0];
  if (!file) return;
  status.textContent = 'Reading post-it…';
  const preview = document.getElementById('snapPreview');
  preview.src = URL.createObjectURL(file);
  preview.style.display = 'block';
  const reader = new FileReader();
  reader.onload = async () => {
    const b64 = reader.result.split(',')[1];
    const data = await api('/api/snap', { image: b64 });
    if (data.say) speak(data.say);
    if (data.text) document.getElementById('typed').value = data.text;
    status.textContent = data.ocr_note || '';
    if (data.expect) showConfirm(data.expect === 'confirm');
  };
  reader.readAsDataURL(file);
};

let rec = null;
const listenBtn = document.getElementById('listenBtn');
if (window.SpeechRecognition || window.webkitSpeechRecognition) {
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  rec = new SR();
  rec.continuous = false;
  rec.interimResults = false;
  rec.lang = 'en-US';
  rec.onresult = (ev) => {
    const t = ev.results[0][0].transcript;
    status.textContent = 'Heard: ' + t;
    sendText(t);
  };
  rec.onerror = (ev) => {
    status.textContent = 'Mic: ' + ev.error + (ev.error === 'not-allowed' ? ' — allow mic or use Type/Snap' : '');
  };
  listenBtn.onmousedown = listenBtn.ontouchstart = (e) => { e.preventDefault(); if (secureMic) { try { rec.start(); status.textContent = 'Listening…'; } catch(x) {} } else { status.textContent = 'Mic blocked on HTTP — type or snap'; } };
  listenBtn.onmouseup = listenBtn.ontouchend = () => { try { rec.stop(); } catch(x) {} };
} else {
  listenBtn.style.display = 'none';
}

(async () => {
  const cal = await api('/api/calendar');
  if (cal.events && cal.events.length) {
    const box = document.getElementById('scheduleBox');
    const ul = document.getElementById('scheduleList');
    cal.events.slice(0, 5).forEach(ev => {
      const li = document.createElement('li');
      const when = ev.start.slice(0, 16).replace('T', ' ');
      li.textContent = when + ' — ' + ev.summary;
      ul.appendChild(li);
    });
    box.style.display = 'block';
  }
  const data = await api('/api/start');
  await applyReply(data);
})();
</script>
</body>
</html>"""

QR_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Sarah — phone link</title>
<style>
  body { font-family: system-ui; max-width: 28rem; margin: 1rem auto; padding: 1rem; background: #1a1a2e; color: #eee; }
  input { width: 100%; padding: 0.75rem; font-size: 1rem; margin: 0.5rem 0; }
  img { max-width: 100%; background: #fff; padding: 8px; border-radius: 8px; }
  a { color: #7bed9f; word-break: break-all; }
  button { padding: 0.75rem 1rem; background: #e94560; color: #fff; border: none; border-radius: 8px; font-size: 1rem; }
  .tip { color: #ffb347; font-size: 0.9rem; }
</style>
</head>
<body>
<h1>Phone link</h1>
<p class="tip">Same Wi-Fi: use your Chromebook Wi-Fi IP (often 192.168.x.x), not 127.0.0.1 or Tailscale-only.</p>
<label>URL for Sarah's phone:</label>
<input id="url" value="{{ base }}/sarah">
<button type="button" id="go">Update QR</button>
<button type="button" id="save" class="secondary" style="background:#0f3460;margin-left:0.5rem">Save for next time</button>
<p><a id="link" href="{{ base }}/sarah">{{ base }}/sarah</a></p>
<p><img id="qr" src="" alt="QR code"></p>
<script>
const inp = document.getElementById('url');
const qr = document.getElementById('qr');
const link = document.getElementById('link');
function update() {
  const u = inp.value.trim();
  link.href = u;
  link.textContent = u;
  qr.src = 'https://quickchart.io/qr?size=280&text=' + encodeURIComponent(u);
}
document.getElementById('go').onclick = update;
document.getElementById('save').onclick = async () => {
  await fetch('/api/phone_url', { method: 'POST', headers: {'Content-Type':'application/json'},
    body: JSON.stringify({ url: inp.value.trim() }) });
  alert('Saved — QR will use this next time.');
};
update();
</script>
</body>
</html>"""

DEV_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Sarah — developer log</title>
<style>
  body { font-family: ui-monospace, monospace; max-width: 48rem; margin: 0 auto; padding: 1rem;
    background: #0d1117; color: #c9d1d9; font-size: 0.85rem; }
  h1 { font-family: system-ui; font-size: 1.1rem; color: #58a6ff; }
  .meta { background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 0.75rem; margin: 1rem 0; }
  pre { background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 0.75rem;
    overflow-x: auto; white-space: pre-wrap; word-break: break-word; max-height: 70vh; overflow-y: auto; }
  a { color: #58a6ff; }
  .dim { color: #8b949e; }
</style>
</head>
<body>
<h1>Developer log</h1>
<p class="dim">Auto-refresh 5s · Drive: fleet/bus/SARAH_DEV_LOG.txt</p>
<div class="meta" id="meta">loading…</div>
<pre id="lines"></pre>
<p><a href="/sarah">← Sarah app</a></p>
<script>
async function refresh() {
  const r = await fetch('/api/devlog');
  const d = await r.json();
  document.getElementById('meta').textContent =
    'step=' + d.state.step + ' draft=' + JSON.stringify(d.state.draft) +
    ' confirmed=' + d.state.confirmed + ' · ring=' + d.ring_count;
  document.getElementById('lines').textContent = d.lines.join('\\n') || '(empty)';
}
refresh();
setInterval(refresh, 5000);
</script>
</body>
</html>"""


@app.route("/assets/kid-face.jpg")
def kid_face():
    path = KID_FACE if safe_is_file(KID_FACE) else DRIVE / "convert_inbox" / "20260615_052625.jpg"
    if safe_is_file(path):
        return send_file(path, mimetype="image/jpeg", max_age=3600)
    return ("", 404)


@app.route("/dev")
def dev_page():
    return DEV_HTML


@app.route("/api/devlog")
def api_devlog():
    if safe_is_file(DEV_LOG):
        lines = safe_read_text(DEV_LOG).splitlines()[-120:]
    else:
        lines = list(DEV_RING)[-120:]
    return jsonify({
        "state": dict(state),
        "ring_count": len(DEV_RING),
        "lines": lines,
    })


@app.route("/both")
def both_links():
    lte_file = DRIVE / "fleet/SARAH_LTE_URL.txt"
    wifi_file = DRIVE / "fleet/SARAH_WIFI_URL.txt"
    lte = safe_read_text(lte_file).strip().splitlines()[0] if safe_is_file(lte_file) else ""
    wifi_lines = safe_read_text(wifi_file, "").splitlines() if safe_is_file(wifi_file) else []
    wifi = next((ln.strip() for ln in wifi_lines if ln.strip().startswith("http")), "")
    html = f"""<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Sarah — both links</title><style>body{{font-family:system-ui;padding:1rem;background:#1a1520;color:#eee}}
a.btn{{display:block;margin:0.75rem 0;padding:1rem;background:#2a2235;border-radius:10px;color:#7bed9f;text-decoration:none;font-size:1.05rem}}
small{{color:#888}}</style></head><body>
<h1>Sarah — pick your network</h1>
<p><small>Both work in parallel. Bookmark both.</small></p>
<a class="btn" href="{lte}/sarah">Cellular / full (mic)<br><small>{lte}</small></a>
<a class="btn" href="{wifi}/sarah">Home WiFi backup<br><small>{wifi}</small></a>
<p><a href="/sarah">Open default app</a></p></body></html>"""
    return html


@app.route("/sarah")
def sarah_page():
    return SARAH_HTML


@app.route("/qr")
def qr_page():
    base = _phone_base_url()
    return QR_HTML.replace("{{ base }}", base)


@app.route("/api/start", methods=["GET"])
def api_start():
    state["step"] = 0
    state["draft"] = None
    state["confirmed"] = False
    _dev("start", f"ip={request.remote_addr}")
    return jsonify(_next_reply())


@app.route("/api/text", methods=["POST"])
def api_text():
    data = request.get_json(force=True) or {}
    text = (data.get("text") or "").strip()
    if not text:
        return jsonify({"say": "I didn't catch that. Type or snap a post-it.", "expect": "input"})
    _log(f"text {text[:120]}")
    _dev("text", f"step={state['step']} len={len(text)} {text[:80]!r}")
    if state["step"] == 2:
        low = text.lower()
        if any(w in low for w in ("yes", "yeah", "yep", "correct", "right")):
            state["confirmed"] = True
            return jsonify(_next_reply())
        if any(w in low for w in ("no", "nope", "wrong")):
            state["confirmed"] = False
            return jsonify(_next_reply())
    state["draft"] = text
    if state["step"] == 0:
        state["step"] = 1
    return jsonify(_next_reply())


@app.route("/api/confirm", methods=["POST"])
def api_confirm():
    data = request.get_json(force=True) or {}
    state["confirmed"] = bool(data.get("yes"))
    _log(f"confirm {state['confirmed']}")
    _dev("confirm", f"yes={state['confirmed']} step={state['step']}")
    return jsonify(_next_reply())


@app.route("/api/snap", methods=["POST"])
def api_snap():
    data = request.get_json(force=True) or {}
    b64 = data.get("image") or ""
    if not b64:
        return jsonify({"say": "No image received.", "expect": "input"})
    try:
        raw = base64.b64decode(b64.split(",")[-1])
    except Exception:
        return jsonify({"say": "Could not read that photo.", "expect": "input"})
    _, text = _save_postit(raw)
    _dev("snap", f"bytes={len(raw)} ocr={text[:60]!r}")
    if text:
        state["draft"] = text
        if state["step"] == 0:
            state["step"] = 1
        reply = _next_reply()
        reply["text"] = text
        reply["ocr_note"] = "OCR saved to Drive postits folder."
        return jsonify(reply)
    return jsonify({
        "say": "Got the photo but couldn't read text. Type what the post-it says.",
        "expect": "input",
        "ocr_note": "Photo saved — add text manually.",
    })


@app.route("/api/calendar", methods=["GET"])
def api_calendar():
    events, source = _load_calendar()
    return jsonify({"events": events, "source": source})


@app.route("/api/calendar/paste", methods=["POST"])
def api_calendar_paste():
    data = request.get_json(force=True) or {}
    ics = (data.get("ics") or "").strip()
    if not ics or "BEGIN:VCALENDAR" not in ics:
        return jsonify({"ok": False, "say": "Paste must look like calendar export (.ics)."})
    CAL_DIR.mkdir(parents=True, exist_ok=True)
    CAL_INBOX.write_text(ics, encoding="utf-8")
    events, source = _load_calendar()
    _dev("calendar_paste", f"n={len(events)}")
    return jsonify({"ok": True, "events": events, "source": source})


@app.route("/api/voice_url", methods=["GET"])
def api_voice_url():
    if safe_is_file(HTTPS_URL_FILE):
        url = safe_read_text(HTTPS_URL_FILE).strip().splitlines()[0]
        if url.startswith("http"):
            return jsonify({"url": url})
    return jsonify({"url": None})


@app.route("/api/phone_url", methods=["POST"])
def api_phone_url():
    data = request.get_json(force=True) or {}
    url = (data.get("url") or "").strip().rstrip("/")
    if url:
        PHONE_URL_FILE.parent.mkdir(parents=True, exist_ok=True)
        PHONE_URL_FILE.write_text(url + "\n", encoding="utf-8")
        _log(f"phone_url saved {url}")
        _dev("phone_url", url)
    return jsonify({"ok": True})


@app.route("/health")
def health():
    return jsonify({"ok": True, "lan": _guess_lan_ip(), "port": PORT})


def main():
    safe_mkdir(LOGS)
    safe_mkdir(DRIVE)
    _log("start sarah_voice_sample v5 calendar")
    _dev("boot", f"port={PORT}")
    app.run(host="0.0.0.0", port=PORT, threaded=True)


if __name__ == "__main__":
    main()
