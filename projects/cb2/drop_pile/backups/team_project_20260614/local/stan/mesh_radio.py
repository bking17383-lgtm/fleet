#!/usr/bin/env python3
"""MESH RADIO — phone extension over Tailscale. Camera + mic + SSE replies. Drive bus."""
from __future__ import annotations

import base64
import json
import os
import queue
import threading
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from flask import Flask, Response, jsonify, request

DRIVE = Path(os.environ.get("DRIVE", Path.home() / "GoogleDrive/MyDrive"))
if Path("/mnt/shared/GoogleDrive/MyDrive").is_dir():
    DRIVE = Path("/mnt/shared/GoogleDrive/MyDrive")

EYES_OUT = DRIVE / "eyes/inbox"
PHONE_INBOX = DRIVE / "phone/inbox"
PHONE_DIR = DRIVE / "phone"
SAY_FILE = PHONE_DIR / "say.txt"
STATE_FILE = PHONE_DIR / "radio_state.json"
PENDING_MD = PHONE_DIR / "PENDING_FOR_CAPTN.md"
EYES_PENDING = DRIVE / "eyes/EYES_PENDING_FOR_CAPTN.md"
COUNT_LAST = DRIVE / "eyes/COUNT_LAST.json"
DEV_LOG_FILE = PHONE_DIR / "mesh_dev.log"

for d in (EYES_OUT, PHONE_INBOX, PHONE_DIR):
    d.mkdir(parents=True, exist_ok=True)

app = Flask(__name__)
_event_q: queue.Queue[dict] = queue.Queue()
_say_mtime: float = 0.0
_lock = threading.Lock()
_dev_lines: list[str] = []
_DEV_MAX = 120


def _now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat()


def _ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _dev_log(tag: str, detail: object = "") -> None:
    ts = datetime.now().strftime("%H:%M:%S")
    if isinstance(detail, dict):
        body = json.dumps(detail, ensure_ascii=False)
    else:
        body = str(detail)
    line = f"[{ts}] {tag}: {body}"
    with _lock:
        _dev_lines.append(line)
        if len(_dev_lines) > _DEV_MAX:
            _dev_lines[:] = _dev_lines[-_DEV_MAX:]
    try:
        with DEV_LOG_FILE.open("a", encoding="utf-8") as f:
            f.write(line + "\n")
    except OSError:
        pass


def _broadcast(event: dict) -> None:
    event = {**event, "time": _now()}
    _event_q.put(event)
    _dev_log("event", event)
    try:
        state = {}
        if STATE_FILE.is_file():
            state = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        state["last_event"] = event
        state["updated"] = _now()
        STATE_FILE.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
    except (OSError, json.JSONDecodeError):
        pass


def _save_snap(raw: str) -> str | None:
    if not raw.startswith("data:image"):
        return None
    try:
        img = base64.b64decode(raw.split(",", 1)[1])
    except (IndexError, ValueError):
        return None
    if len(img) < 500:
        return None
    name = f"eyes_{_ts()}.jpg"
    path = EYES_OUT / name
    path.write_bytes(img)
    return name


def _write_pending(record: dict) -> None:
    img = record.get("image")
    lines = [
        "# Phone — waiting for CAPTN",
        f"Updated: {_now()}",
        "",
        f"**Time:** {record.get('time')}",
        f"**You said:** {record.get('text', '')}",
        f"**Frame:** {img or 'none'}",
        "",
        "CAPTN: write one short line to `phone/say.txt` or POST /api/reply",
        "",
    ]
    PENDING_MD.write_text("\n".join(lines), encoding="utf-8")
    if img:
        _write_eyes_pending(record)


def _write_eyes_pending(record: dict) -> None:
    img = record.get("image") or ""
    path = EYES_OUT / img if img else None
    lines = [
        "# EYES — CAPTN read this snap",
        f"Updated: {_now()}",
        "",
        f"**Snap:** `{img}`",
        f"**Path:** `{path}`" if path else "**Path:** (missing)",
        f"**Time:** {record.get('time')}",
        f"**Brian said:** {record.get('text', '(snap)')}",
        "",
        "CAPTN: open the jpg above — that is Daddy's eyes.",
        "Reply one line → phone/say.txt",
        "",
    ]
    EYES_PENDING.write_text("\n".join(lines), encoding="utf-8")
    _dev_log("eyes", {"snap": img, "pending": str(EYES_PENDING)})


def _groq_key() -> str | None:
    if os.environ.get("GROQ_API_KEY"):
        return os.environ["GROQ_API_KEY"].strip()
    keys = DRIVE / "lester/lester_keys.md"
    if keys.is_file():
        for line in keys.read_text(encoding="utf-8").splitlines():
            s = line.strip()
            if s.startswith("gsk_"):
                return s
    return None


def _gemini_key() -> str | None:
    if os.environ.get("GEMINI_API_KEY"):
        return os.environ["GEMINI_API_KEY"].strip()
    keys = DRIVE / "lester/lester_keys.md"
    if keys.is_file():
        for line in keys.read_text(encoding="utf-8").splitlines():
            s = line.strip()
            if s.startswith("AIza"):
                return s
    return None


def _http_post_json(url: str, headers: dict, payload: dict, timeout: float = 15) -> dict:
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _one_line(text: str, limit: int = 220) -> str:
    line = (text or "").strip().replace("\n", " ")
    return line[:limit] if line else "Got it — I'm with you."


def _groq_reply(user_text: str) -> str:
    key = _groq_key()
    if not key:
        return "Heard you. CAPTN is here."
    prompt = user_text if user_text != "(snap)" else "Brian sent a snap from the drive."
    try:
        data = _http_post_json(
            "https://api.groq.com/openai/v1/chat/completions",
            {"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            {
                "model": "llama-3.1-8b-instant",
                "max_tokens": 90,
                "temperature": 0.5,
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "You are CAPTN, Brian's coach while he drives. "
                            "Reply in ONE short sentence for text-to-speech. Plain English. Warm."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
            },
        )
        return _one_line(data["choices"][0]["message"]["content"])
    except (urllib.error.URLError, KeyError, IndexError, json.JSONDecodeError) as exc:
        _dev_log("groq_err", str(exc)[:100])
        return "Got it — I'm listening."


def _gemini_reply(user_text: str, image_path: Path) -> str:
    key = _gemini_key()
    if not key:
        return _groq_reply(user_text)
    prompt = (
        f"Brian on a drive says: {user_text}. "
        "Reply in ONE short spoken sentence as CAPTN, his coach. Mention what you see if useful."
    )
    try:
        img_b64 = base64.b64encode(image_path.read_bytes()).decode("ascii")
        url = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"gemini-2.0-flash:generateContent?key={key}"
        )
        data = _http_post_json(
            url,
            {"Content-Type": "application/json"},
            {
                "contents": [
                    {
                        "parts": [
                            {"text": prompt},
                            {"inline_data": {"mime_type": "image/jpeg", "data": img_b64}},
                        ]
                    }
                ],
                "generationConfig": {"maxOutputTokens": 90},
            },
        )
        parts = data["candidates"][0]["content"]["parts"]
        text = " ".join(p.get("text", "") for p in parts)
        return _one_line(text)
    except (urllib.error.URLError, KeyError, IndexError, json.JSONDecodeError, OSError) as exc:
        _dev_log("gemini_err", str(exc)[:100])
        return _groq_reply(user_text)


def _parse_json_blob(text: str) -> dict | None:
    raw = (text or "").strip()
    if raw.startswith("```"):
        raw = raw.split("```", 2)[1]
        if raw.startswith("json"):
            raw = raw[4:]
    try:
        return json.loads(raw.strip())
    except json.JSONDecodeError:
        start, end = raw.find("{"), raw.rfind("}")
        if start >= 0 and end > start:
            try:
                return json.loads(raw[start : end + 1])
            except json.JSONDecodeError:
                return None
    return None


def _latest_snap(max_age_sec: int = 300) -> str | None:
    now = time.time()
    for path in sorted(EYES_OUT.glob("eyes_*.jpg"), key=lambda p: p.stat().st_mtime, reverse=True):
        try:
            if now - path.stat().st_mtime <= max_age_sec:
                return path.name
        except OSError:
            continue
    return None


def _wants_count(text: str) -> bool:
    """Voice count only when Brian clearly asks — not shelf chatter or 1-2-3."""
    low = (text or "").lower().strip()
    if low.startswith("(count)") or low.startswith("count:"):
        return True
    if not any(w in low for w in ("count", "how many", "number of", "inventory")):
        return False
    # ignore steady-count noise picked up by mic
    import re
    noise = re.sub(r"[^a-z0-9\s]", "", low)
    if re.fullmatch(r"(one|two|three|four|five|six|seven|eight|nine|ten|\d+)(\s+(one|two|three|four|five|six|seven|eight|nine|ten|\d+))*", noise):
        return False
    return True


def _is_count_request(text: str) -> bool:
    t = (text or "").strip().lower()
    return t.startswith("(count)") or t.startswith("count:") or t == "count"


def _count_hint(text: str) -> str:
    t = (text or "").strip()
    low = t.lower()
    if low.startswith("(count)"):
        rest = t[7:].strip(" -:")
        return rest or "items on table in clumps"
    if low.startswith("count:"):
        return t[6:].strip() or "items on table in clumps"
    return "items on table in clumps"


def _format_count_speech(data: dict) -> str:
    clusters = data.get("clusters") or []
    tl = data.get("total_low")
    th = data.get("total_high")
    conf = data.get("confidence") or "med"
    bits: list[str] = []
    for c in clusters[:4]:
        name = c.get("name") or "pile"
        lo, hi = c.get("low"), c.get("high")
        if lo is not None and hi is not None:
            bits.append(f"{name} {lo}-{hi}")
    line = f"Count {tl} to {th}, {conf} confidence."
    if bits:
        line = f"{len(clusters)} piles: " + ", ".join(bits) + f". Total {tl} to {th}. {conf} confidence."
    tip = (data.get("tip") or "").strip()
    if tip:
        line += f" {tip}"
    return _one_line(line, 280)


def _write_count_result(record: dict, data: dict, speech: str) -> None:
    payload = {
        "id": record.get("id"),
        "time": record.get("time"),
        "hint": record.get("text"),
        "image": record.get("image"),
        "result": data,
        "speech": speech,
        "updated": _now(),
    }
    try:
        COUNT_LAST.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    except OSError:
        pass
    lines = [
        "# COUNT — cluster tally",
        f"Updated: {_now()}",
        "",
        f"**Snap:** `{record.get('image')}`",
        f"**Hint:** {record.get('text')}",
        f"**Speech:** {speech}",
        "",
        "```json",
        json.dumps(data, indent=2),
        "```",
        "",
        "Brian: say yes or correct one pile. Second SNAP tightens range.",
        "",
    ]
    try:
        (DRIVE / "eyes/COUNT_PENDING.md").write_text("\n".join(lines), encoding="utf-8")
    except OSError:
        pass
    _dev_log("count_saved", {"id": record.get("id"), "total": f"{data.get('total_low')}-{data.get('total_high')}"})


def _gemini_count(image_path: Path, hint: str) -> tuple[dict | None, str]:
    key = _gemini_key()
    if not key:
        return None, "No vision key — CAPTN will count from your snap."
    prompt = (
        "Count physical objects in CLUMPS on a table or surface.\n"
        "Method: identify separate piles first; estimate each pile low-high; sum ranges.\n"
        "Never one exact number without a range. Overlaps = wider range + lower confidence.\n"
        f"Brian counts: {hint}\n"
        "Reply ONLY valid JSON, no markdown:\n"
        '{"clusters":[{"name":"pile A","low":0,"high":0,"note":"brief"}],'
        '"total_low":0,"total_high":0,"confidence":"low|med|high",'
        '"tip":"one short tip"}'
    )
    try:
        img_b64 = base64.b64encode(image_path.read_bytes()).decode("ascii")
        url = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"gemini-2.0-flash:generateContent?key={key}"
        )
        data = _http_post_json(
            url,
            {"Content-Type": "application/json"},
            {
                "contents": [
                    {
                        "parts": [
                            {"text": prompt},
                            {"inline_data": {"mime_type": "image/jpeg", "data": img_b64}},
                        ]
                    }
                ],
                "generationConfig": {"maxOutputTokens": 400, "temperature": 0.2},
            },
            timeout=25,
        )
        parts = data["candidates"][0]["content"]["parts"]
        text = " ".join(p.get("text", "") for p in parts)
        parsed = _parse_json_blob(text)
        if not parsed:
            _dev_log("count_parse_err", text[:120])
            return None, "Count failed parse — CAPTN reading snap by hand."
        speech = _format_count_speech(parsed)
        return parsed, speech
    except (urllib.error.URLError, KeyError, IndexError, json.JSONDecodeError, OSError) as exc:
        _dev_log("count_err", str(exc)[:120])
        return None, "Count timed out — CAPTN reading snap by hand."


def _run_count_job(record: dict, image_name: str, hint: str) -> None:
    path = EYES_OUT / image_name
    parsed, speech = _gemini_count(path, hint)
    if parsed:
        _write_count_result(record, parsed, speech)
        _post_say(speech)
        _dev_log("count_done", {"id": record["id"], "say": speech[:80]})
    else:
        record["text"] = f"(count) {hint}"
        _write_pending(record)
        _write_eyes_pending(record)
        _dev_log("count_queue", {"id": record["id"], "reason": speech[:80]})


def _needs_think(text: str) -> bool:
    t = text.lower()
    if len(text) > 70:
        return True
    triggers = (
        "how", "why", "plan", "queue", "sync", "build", "fix", "decide",
        "should", "what if", "figure", "think", "strategy", "priority",
        "puppy", "uncle", "export", "reboot", "organize", "clear the",
    )
    if any(w in t for w in triggers):
        return True
    return "?" in text and len(text) > 20


def _plan_seconds(text: str) -> int:
    if len(text) > 100:
        return 20
    if len(text) > 50:
        return 15
    return 10


def _plan_followup(user_text: str, image_name: str | None) -> str:
    """After the wait line — speak a real CAPTN answer (no slow APIs)."""
    t = (user_text or "").strip()
    low = t.lower()
    if "boxster" in low or "986" in low:
        return (
            "Got it Brian — two thousand two Boxster nine eighty-six gets its own file. "
            "I'll open fleet slash BOXSTER nine eighty-six when you're parked."
        )
    if "cigarette" in low or "beer" in low or "errand" in low or "store" in low:
        return "Errand copied — cigarettes and beer. Use HOLD to talk if DRIVE MIC fights you."
    if "sync" in low or "snap" in low or "fetch" in low or "1033" in low:
        url = _public_url()
        return f"Link is fresh — open {url} in a new Chrome tab. Fetch errors were a dead tunnel."
    if "puppy" in low and "queue" in low:
        return "Puppy queue stays on hold until your GUI is fixed. CAPTN sees inbox — no forced clear."
    if "uncle" in low and ("linux" in low or "fix" in low):
        return "Uncle Linux — WRANGLER slave is on it. You stay on RADIO; nothing for legs to fix."
    if any(w in low for w in ("respond", "didn't respond", "15 second", "waiting", "hear from")):
        return "Brian — CAPTN hears you now. New link is live on Drive — paste it fresh, no old tab."
    if "microphone" in low or "driver mic" in low or "red button" in low:
        return "Tap DRIVE MIC once for open mic. If it drops, use HOLD — press, talk, release."
    return _local_reply(user_text, bool(image_name and (EYES_OUT / image_name).is_file()))


def _local_reply(user_text: str, has_image: bool) -> str:
    t = (user_text or "").strip()
    low = t.lower()
    if any(w in low for w in ("respond", "hear me", "hear", "confirm", "test", "rover", "daddy", "captn")):
        return "Yes — Daddy hears you ROVER. I'm here. Go ahead."
    if t == "(snap)" or (has_image and len(t) < 12):
        return "Picture received — CAPTN reading. Watch the green REPLY box."
    if t.lower().startswith("(aim)"):
        return "Got your aim hint. Say SNAP when ready — I'll tell you left, right, up, or down."
    if any(w in low for w in ("picture", "sync", "timestamp", "attach", "eyes", "snap")):
        return "Got the picture — Daddy eyes on Drive. Tell me what you want checked in one sentence."
    if any(w in low for w in ("rover", "cellular", "moto", "unique", "identifier")):
        return "Moto cellular is ROVER. Samsung WiFi stays TESTER."
    if "?" in t:
        if any(w in low for w in ("car", "truck", "vehicle", "engine", "tire")):
            return "What do you need on the car?"
        return "Say it again in one short sentence."
    if len(t) > 15:
        return "Got it — I'm with you. Next?"
    return "Yes — I'm here. Keep talking."


def _auto_reply(user_text: str, image_name: str | None) -> str:
    has_image = bool(image_name and (EYES_OUT / image_name).is_file())
    # FAST: skip Gemini/Groq on drive (429/403 + 15s timeout was causing silence)
    return _local_reply(user_text, has_image)


def _post_say(text: str) -> None:
    global _say_mtime
    SAY_FILE.write_text(text + "\n", encoding="utf-8")
    _say_mtime = SAY_FILE.stat().st_mtime
    _broadcast({"type": "say", "text": text})
    _dev_log("auto_say", text[:100])


def _watch_say_file() -> None:
    global _say_mtime
    while True:
        try:
            if SAY_FILE.is_file():
                mt = SAY_FILE.stat().st_mtime
                if mt > _say_mtime:
                    _say_mtime = mt
                    text = SAY_FILE.read_text(encoding="utf-8").strip()
                    if text:
                        _broadcast({"type": "say", "text": text})
                        _dev_log("say_file", text)
        except OSError:
            pass
        time.sleep(1.0)


threading.Thread(target=_watch_say_file, daemon=True).start()


def _public_url() -> str:
    url_file = DRIVE / "fleet/MESH_RADIO_URL.txt"
    if url_file.is_file():
        for line in url_file.read_text(encoding="utf-8").splitlines():
            s = line.strip()
            if s.startswith("https://"):
                return s.rstrip("/").removesuffix("/rover")
    return "http://127.0.0.1:8765"


def _rover_url() -> str:
    return _public_url().rstrip("/") + "/rover"


def _qr_page() -> str:
    import urllib.parse

    url = _rover_url()
    enc = urllib.parse.quote(url, safe="")
    qr = f"https://quickchart.io/qr?size=420&text={enc}"
    return f"""<!DOCTYPE html>
<html><head>
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>RADIO QR</title>
<style>
body{{font-family:system-ui;text-align:center;background:#000;color:#fff;padding:1rem}}
img{{width:min(420px,90vw);border:10px solid #fff;border-radius:16px}}
a{{color:#6cf;font-size:1.2rem;word-break:break-all;display:block;margin:1rem}}
h1{{font-size:1.6rem}}
p{{color:#aaa}}
</style></head><body>
<h1>Scan with Moto (ROVER)</h1>
<img src="{qr}" alt="QR code">
<a href="{url}">{url}</a>
<p>CB2 must stay awake · Home Screen → RADIO</p>
</body></html>"""

PHONE_PAGE = """<!DOCTYPE html>
<html><head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="apple-mobile-web-app-capable" content="yes">
<title>MESH RADIO</title>
<style>
  * { box-sizing: border-box; }
  body { font-family: system-ui, sans-serif; margin: 0; padding: 1rem;
         background: #0a0a0a; color: #eee; max-width: 720px; margin-inline: auto; }
  h1 { font-size: 1.75rem; margin: 0 0 0.25rem; }
  .sub { color: #888; font-size: 1rem; margin-bottom: 1rem; }
  video { width: 100%; max-height: 42vh; background: #000; border-radius: 10px; }
  .row { display: flex; flex-wrap: wrap; gap: 0.5rem; margin: 0.75rem 0; }
  button { font-size: 1.35rem; padding: 0.85rem 1.2rem; border: none; border-radius: 10px;
           cursor: pointer; font-weight: 600; }
  #talk { display: none; }
  #drive { background: #27ae60; color: #fff; flex: 1; min-width: 120px; }
  #drive.off { background: #555; color: #ccc; }
  #snap { background: #3498db; color: #fff; }
  #count { background: #e67e22; color: #fff; }
  #send { background: #2ecc71; color: #000; font-size: 1.05rem; padding: 0.55rem 1rem; width: 100%; }
  #speak { background: #9b59b6; color: #fff; }
  @keyframes pulse { 50% { opacity: 0.7; } }
  #heard, #reply { font-size: 1.25rem; line-height: 1.45; padding: 0.75rem;
                   border-radius: 8px; margin: 0.5rem 0; min-height: 2.5rem; }
  #heard { background: #1a1a2e; color: #aad; }
  #reply { background: #1a2e1a; color: #afa; font-weight: 600; }
  #wait { background: #2e2a1a; color: #dd8; font-size: 1.1rem; padding: 0.5rem 0.75rem;
          border-radius: 8px; margin: 0.5rem 0; display: none; }
  #wait.on { display: block; }
  #status { font-size: 0.95rem; color: #666; }
  input[type=text] { width: 100%; font-size: 1.2rem; padding: 0.6rem; border-radius: 8px;
                     border: 1px solid #333; background: #111; color: #eee; }
  .dev h3 { font-size: 1rem; color: #888; margin: 1.25rem 0 0.35rem; }
  #devlog { background: #1a1a1a; color: #8cf; padding: 0.75rem; border-radius: 8px;
            font-size: 0.82rem; line-height: 1.35; max-height: 220px; overflow-y: auto;
            white-space: pre-wrap; word-break: break-word; border: 1px solid #333; }
</style></head><body>
<h1>MESH RADIO</h1>
<p class="sub">Drive mode — MIC ON = just talk (auto-sends). Type only if parked.</p>
<p id="status">Connecting…</p>
<video id="v" autoplay playsinline muted></video>
<div class="row">
  <button id="drive">MIC ON</button>
  <button id="snap">SNAP</button>
  <button id="count">COUNT</button>
  <button id="speak">HEAR AGAIN</button>
</div>
<input id="typed" type="text" placeholder="Type here — Enter sends">
<button id="send" style="margin-top:0.35rem;background:#2ecc71;color:#000">SEND TEXT</button>
<div id="heard"></div>
<div id="wait">Waiting for CAPTN…</div>
<div id="reply"></div>
<div class="dev"><h3>Developer log</h3><pre id="devlog">(waiting…)</pre></div>
<canvas id="c" hidden></canvas>
<script>
const heard = document.getElementById('heard');
const reply = document.getElementById('reply');
const wait = document.getElementById('wait');
const status = document.getElementById('status');
const devlog = document.getElementById('devlog');
let stream=null, lastReply='', lastSpoken='', lastSayTs=0, recognition=null;
let listening=false, driveMode=true, sending=false;

function devLog(tag, obj){
  const ts=new Date().toLocaleTimeString();
  const body=(typeof obj==='string')?obj:JSON.stringify(obj,null,2);
  const line='['+ts+'] '+tag+': '+body;
  devlog.textContent=(devlog.textContent==='(waiting…)'?'':devlog.textContent+'\\n')+line;
  devlog.scrollTop=devlog.scrollHeight;
}

async function refreshDevLog(){
  try{
    const r=await fetch('/api/devlog'); const j=await r.json();
    if(j.server&&j.server.length){
      devLog('server', j.server.slice(-8).join('\\n'));
    }
  }catch(e){ devLog('devlog_err', String(e)); }
}

function showReply(text, speak=true){
  if(!text) return;
  wait.classList.remove('on');
  reply.textContent='CAPTN: '+text;
  if(text===lastReply && (!speak || text===lastSpoken)) return;
  lastReply=text;
  devLog('reply', text);
  if(speak && text!==lastSpoken){
    lastSpoken=text;
    sayAloud(text);
  }
}

function pollSay(){
  fetch('/api/say').then(r=>r.json()).then(j=>{
    if(!j.text) return;
    const ts=Date.parse(j.updated||'')||0;
    if(ts>lastSayTs){
      lastSayTs=ts;
      showReply(j.text, false);
    }else if(!lastReply){
      showReply(j.text, false);
    }
  }).catch((e)=>{ devLog('poll_err', String(e)); });
}

function sayAloud(t){
  if(!t||!window.speechSynthesis) return;
  speechSynthesis.cancel();
  const u=new SpeechSynthesisUtterance(t);
  u.rate=0.95; speechSynthesis.speak(u);
}

async function startCam(){
  const tries=[
    {video:{facingMode:{ideal:'environment'}}},
    {video:{facingMode:'user'}},
    {video:true},
  ];
  for(let i=0;i<tries.length;i++){
    try{
      stream=await navigator.mediaDevices.getUserMedia({...tries[i],audio:false});
      document.getElementById('v').srcObject=stream;
      status.textContent='Camera on · drive mode';
      devLog('camera', 'on try '+i);
      return;
    }catch(e){ devLog('camera_try', String(e)); }
  }
  status.textContent='No camera — text/voice still work';
}

function frameB64(){
  const v=document.getElementById('v'), c=document.getElementById('c');
  if(!v.videoWidth) return null;
  c.width=v.videoWidth; c.height=v.videoHeight;
  c.getContext('2d').drawImage(v,0,0);
  return c.toDataURL('image/jpeg',0.82);
}

async function sendMsg(text, withFrame=false){
  text=(text||'').trim();
  if(!text||sending){ return; }
  sending=true;
  heard.textContent='You: '+text;
  status.textContent='Sending…';
  const body={text};
  if(withFrame){
    const f=frameB64();
    if(!f){
      status.textContent='No camera frame — allow camera or wait a sec';
      devLog('frame', 'missing');
      sending=false;
      return;
    }
    body.image=f;
  }
  try{
    const r=await fetch('/api/said',{method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify(body)});
    const j=await r.json();
    devLog('POST /api/said', j);
    status.textContent=j.ok?'Sent':'Error: '+(j.error||'?');
    if(j.planning){
      wait.classList.add('on');
      wait.textContent='Waiting for CAPTN…';
      reply.textContent='';
      setTimeout(pollSay, 500);
    }else if(j.say){ showReply(j.say, true); }
    else if(j.ok){ wait.classList.add('on'); reply.textContent=''; setTimeout(pollSay, 500); }
  }finally{ sending=false; }
}

function isMicNoise(t){
  const s=t.trim().toLowerCase().replace(/[.,!?'"]/g,'').replace(/\\s+/g,' ');
  if(!s||s.length<3) return true;
  if(/^(one|two|three|four|five|six|seven|eight|nine|ten|\\d+)( (one|two|three|four|five|six|seven|eight|nine|ten|\\d+))*$/.test(s)) return true;
  if(/^(hold steady|hold still|wait|ready|okay|ok|um|uh)$/.test(s)) return true;
  return false;
}

async function countWithSteady(){
  if(sending) return;
  const hint=document.getElementById('typed').value.trim();
  const text=hint?'(count) '+hint:'(count)';
  const wasDrive=driveMode;
  if(wasDrive&&listening){ try{recognition.stop();}catch(e){} listening=false; }
  for(const n of [3,2,1]){
    status.textContent='Aim shelf — hold still '+n+'…';
    wait.classList.add('on');
    wait.textContent='Aim shelf — hold still '+n+'…';
    await new Promise(r=>setTimeout(r,1000));
  }
  status.textContent='Snap now';
  wait.textContent='Snapping…';
  await sendMsg(text, true);
  if(wasDrive) startDriveMic();
}

document.getElementById('send').onclick=()=>sendMsg(document.getElementById('typed').value);
document.getElementById('typed').addEventListener('keydown',(e)=>{
  if(e.key==='Enter'){ e.preventDefault(); sendMsg(document.getElementById('typed').value); }
});
document.getElementById('snap').onclick=()=>sendMsg('(snap)', true);
document.getElementById('count').onclick=()=>countWithSteady();
document.getElementById('speak').onclick=()=>sayAloud(lastReply);

const SR=window.SpeechRecognition||window.webkitSpeechRecognition;
function setMicUi(on){
  const b=document.getElementById('drive');
  if(on){
    b.classList.remove('off');
    b.textContent='MIC ON';
    status.textContent='Listening — just talk';
  }else{
    b.classList.add('off');
    b.textContent='MIC OFF';
    status.textContent='Mic off — tap MIC ON or type below';
  }
}
function startDriveMic(){
  if(!SR||!driveMode) return;
  if(listening) return;
  listening=true;
  recognition.continuous=true;
  setMicUi(true);
  try{ recognition.start(); }catch(e){ devLog('mic', String(e)); }
}
function stopDriveMic(){
  listening=false;
  try{ recognition.stop(); }catch(e){}
  setMicUi(false);
}
if(SR){
  recognition=new SR();
  recognition.continuous=true;
  recognition.interimResults=true;
  recognition.lang='en-US';
  recognition.onresult=(e)=>{
    let t='';
    for(let i=e.resultIndex;i<e.results.length;i++) t+=e.results[i][0].transcript;
    document.getElementById('typed').value=t;
    heard.textContent=t?'You: '+t:'';
    if(driveMode && e.results[e.results.length-1].isFinal && t.trim()){
      if(isMicNoise(t)){ devLog('mic_skip', t); document.getElementById('typed').value=''; return; }
      sendMsg(t.trim(), false);
      document.getElementById('typed').value='';
    }
  };
  recognition.onend=()=>{
    listening=false;
    if(driveMode) setTimeout(startDriveMic, 400);
  };
  document.getElementById('drive').onclick=()=>{
    driveMode=!driveMode;
    if(driveMode) startDriveMic();
    else stopDriveMic();
  };
  driveMode=true;
  startDriveMic();
}else{
  document.getElementById('drive').textContent='MIC N/A';
  driveMode=false;
}

const es=new EventSource('/api/events');
es.onmessage=(ev)=>{
  try{
    const j=JSON.parse(ev.data);
    if(j.type==='say'&&j.text){
      devLog('SSE say', j);
      showReply(j.text, true);
    }
    if(j.type==='ping') devLog('SSE', 'ping');
  }catch(e){ devLog('SSE err', String(e)); }
};
es.onopen=()=>{ status.textContent=(status.textContent||'')+' · live'; devLog('SSE', 'connected'); };
es.onerror=()=>{ devLog('SSE', 'error'); };

startCam();
devLog('boot', location.href);
pollSay();
setInterval(pollSay, 2000);
setInterval(refreshDevLog, 4000);
refreshDevLog();
</script></body></html>"""

DESK_PAGE = """<!DOCTYPE html>
<html><head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>MESH DESK</title>
<style>
  body { font-family: system-ui; max-width: 640px; margin: 1rem; background: #111; color: #eee; }
  h1 { font-size: 1.5rem; }
  pre { background: #222; padding: 1rem; border-radius: 8px; white-space: pre-wrap; font-size: 1.1rem; }
  input, button { font-size: 1.2rem; padding: 0.5rem; margin: 0.25rem 0; width: 100%; }
  button { background: #2ecc71; color: #000; border: none; border-radius: 8px; font-weight: 700; }
</style></head><body>
<h1>MESH DESK — CAPTN reply</h1>
<pre id="pending">Loading…</pre>
<input id="line" placeholder="One short sentence for phone…">
<button onclick="reply()">SEND TO PHONE</button>
<div class="dev" style="margin-top:1rem"><h3 style="color:#888;font-size:1rem">Developer log</h3>
<pre id="devlog" style="background:#222;color:#8cf;padding:0.75rem;border-radius:8px;font-size:0.85rem;max-height:180px;overflow:auto;white-space:pre-wrap">(waiting…)</pre></div>
<script>
function devLog(tag, obj){
  const el=document.getElementById('devlog');
  const ts=new Date().toLocaleTimeString();
  const body=(typeof obj==='string')?obj:JSON.stringify(obj,null,2);
  el.textContent=(el.textContent==='(waiting…)'?'':el.textContent+'\\n')+'['+ts+'] '+tag+': '+body;
  el.scrollTop=el.scrollHeight;
}
async function refresh(){
  const r=await fetch('/api/pending'); const j=await r.json();
  document.getElementById('pending').textContent=j.pending||'(none)';
}
async function reply(){
  const text=document.getElementById('line').value.trim();
  if(!text) return;
  const r=await fetch('/api/reply',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({text})});
  const j=await r.json();
  devLog('POST /api/reply', j);
  document.getElementById('line').value='';
  refresh();
}
refresh(); setInterval(refresh, 3000);
fetch('/api/devlog').then(r=>r.json()).then(j=>devLog('server boot', j.server&&j.server.slice(-5))).catch(()=>{});
</script></body></html>"""

OFFICE_PAGE = """<!DOCTYPE html>
<html><head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>RADIO OFFICE — CB2</title>
<style>
  * { box-sizing: border-box; }
  body { font-family: system-ui, sans-serif; margin: 0; padding: 1rem;
         background: #0d1117; color: #e6edf3; max-width: 960px; margin-inline: auto; }
  h1 { font-size: 1.6rem; margin: 0 0 0.2rem; }
  .sub { color: #8b949e; margin-bottom: 0.75rem; }
  .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem; }
  @media(max-width:720px){ .grid { grid-template-columns: 1fr; } }
  video { width: 100%; max-height: 36vh; background: #000; border-radius: 8px; }
  button { font-size: 1.1rem; padding: 0.65rem 1rem; border: none; border-radius: 8px;
           cursor: pointer; font-weight: 600; margin: 0.25rem 0.25rem 0.25rem 0; }
  #snap { background: #388bfd; color: #fff; }
  #count { background: #d29922; color: #000; }
  #send { background: #3fb950; color: #000; }
  #speak { background: #a371f7; color: #fff; }
  #mic { background: #e67e22; color: #000; }
  #mic.off { background: #484f58; color: #e6edf3; }
  #flip { background: #6e7681; color: #fff; }
  input, textarea { width: 100%; font-size: 1.05rem; padding: 0.55rem; border-radius: 8px;
                    border: 1px solid #30363d; background: #161b22; color: #e6edf3; }
  .panel { background: #161b22; border: 1px solid #30363d; border-radius: 8px;
           padding: 0.65rem; font-size: 0.92rem; line-height: 1.4; }
  .panel h3 { margin: 0 0 0.4rem; font-size: 0.95rem; color: #8b949e; }
  #pending, #fleet { white-space: pre-wrap; max-height: 140px; overflow-y: auto; }
  #reply { background: #122117; color: #7ee787; font-weight: 600; min-height: 2.5rem; }
  #heard { background: #12162a; color: #a5b4fc; min-height: 2rem; }
  #wait { background: #2d2a14; color: #e3b341; display: none; padding: 0.5rem; border-radius: 8px; }
  #wait.on { display: block; }
  #status { color: #8b949e; font-size: 0.9rem; }
  #devlog { background: #0d1117; color: #79c0ff; padding: 0.65rem; border-radius: 8px;
            font-size: 0.78rem; max-height: 200px; overflow-y: auto; white-space: pre-wrap; }
</style></head><body>
<h1>RADIO OFFICE</h1>
<p class="sub">CB2 eyes — flat chromebook · say SNAP or tap · CAPTN speaks left/right back</p>
<p id="status">Starting camera…</p>
<video id="v" autoplay playsinline muted></video>
<div>
  <button id="snap">SNAP</button>
  <button id="count">COUNT</button>
  <button id="mic" class="off">MIC OFF</button>
  <button id="flip">FLIP CAM</button>
  <button id="send">SEND</button>
  <button id="speak">HEAR AGAIN</button>
</div>
<input id="typed" type="text" placeholder="Type test message — Enter to send">
<div id="heard" class="panel"></div>
<div id="wait">Waiting for CAPTN…</div>
<div id="reply" class="panel"></div>
<div class="grid">
  <div class="panel"><h3>Pending (phone inbox)</h3><div id="pending">…</div></div>
  <div class="panel"><h3>Fleet status</h3><div id="fleet">…</div></div>
</div>
<div class="panel" style="margin-top:0.75rem">
  <h3>Reply to phone</h3>
  <input id="captn" placeholder="One line → phone hears this">
  <button id="toPhone" style="background:#238636;color:#fff;margin-top:0.35rem">SEND TO PHONE</button>
</div>
<div class="panel" style="margin-top:0.75rem"><h3>Developer log</h3><pre id="devlog">(waiting…)</pre></div>
<canvas id="c" hidden></canvas>
<script>
let stream=null, lastReply='', lastSayTs=0, sending=false, micOn=false, camList=[], camIdx=0;
let recognition=null;
const heard=document.getElementById('heard');
const reply=document.getElementById('reply');
const wait=document.getElementById('wait');
const status=document.getElementById('status');
const devlog=document.getElementById('devlog');

function devLog(tag, obj){
  const ts=new Date().toLocaleTimeString();
  const body=(typeof obj==='string')?obj:JSON.stringify(obj,null,2);
  devlog.textContent=(devlog.textContent==='(waiting…)'?'':devlog.textContent+'\\n')+'['+ts+'] '+tag+': '+body;
  devlog.scrollTop=devlog.scrollHeight;
}

function sayAloud(t){
  if(!t||!window.speechSynthesis) return;
  speechSynthesis.cancel();
  const u=new SpeechSynthesisUtterance(t);
  u.rate=0.92; speechSynthesis.speak(u);
}

async function loadCameras(){
  try{
    const devs=await navigator.mediaDevices.enumerateDevices();
    camList=devs.filter(d=>d.kind==='videoinput');
    devLog('cams', camList.map((d,i)=>(i+1)+':'+(d.label||'camera '+i)).join(', ')||'none');
  }catch(e){ devLog('cams_err', String(e)); }
}

async function openCam(constraints){
  if(stream){ stream.getTracks().forEach(t=>t.stop()); stream=null; }
  stream=await navigator.mediaDevices.getUserMedia({...constraints,audio:false});
  document.getElementById('v').srcObject=stream;
}

async function startCam(idx=null){
  const tries=[
    {video:{facingMode:{ideal:'user'}}},
    {video:{facingMode:'user'}},
    {video:true},
    {video:{facingMode:{ideal:'environment'}}},
  ];
  try{
    if(idx!==null&&camList.length){
      const id=camList[idx%camList.length].deviceId;
      await openCam({video:{deviceId:{exact:id}}});
      status.textContent='Camera: '+(camList[idx%camList.length].label||('cam '+idx));
      devLog('camera','device '+idx);
      return;
    }
  }catch(e){ devLog('camera_dev', String(e)); }
  for(let i=0;i<tries.length;i++){
    try{
      await openCam(tries[i]);
      status.textContent='Office camera on — flat CB · front/USB';
      devLog('camera','on try '+i);
      await loadCameras();
      return;
    }catch(e){ devLog('camera_try', String(e)); }
  }
  status.textContent='No camera — plug USB cam or allow permission';
}

async function flipCam(){
  await loadCameras();
  if(!camList.length){ status.textContent='No camera list — allow permission first'; return; }
  camIdx=(camIdx+1)%camList.length;
  await startCam(camIdx);
}

function frameB64(){
  const v=document.getElementById('v'), c=document.getElementById('c');
  if(!v.videoWidth) return null;
  c.width=v.videoWidth; c.height=v.videoHeight;
  c.getContext('2d').drawImage(v,0,0);
  return c.toDataURL('image/jpeg',0.85);
}

async function sendMsg(text, withFrame=false){
  text=(text||'').trim();
  if(!text||sending) return;
  sending=true;
  heard.textContent='Office: '+text;
  const body={text};
  if(withFrame){
    const f=frameB64();
    if(!f){ status.textContent='No frame — wait for camera'; sending=false; return; }
    body.image=f;
  }
  try{
    const r=await fetch('/api/said',{method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify(body)});
    const j=await r.json();
    devLog('said', j);
    if(j.planning){ wait.classList.add('on'); reply.textContent=''; pollSay(); }
    else if(j.say){ wait.classList.remove('on'); reply.textContent='CAPTN: '+j.say; lastReply=j.say; }
    refreshPanels();
  }finally{ sending=false; }
}

function pollSay(){
  fetch('/api/say').then(r=>r.json()).then(j=>{
    if(!j.text) return;
    const ts=Date.parse(j.updated||'')||0;
    if(ts>lastSayTs||!lastReply){
      lastSayTs=ts;
      wait.classList.remove('on');
      reply.textContent='CAPTN: '+j.text;
      lastReply=j.text;
      sayAloud(j.text);
    }
  }).catch(()=>{});
}

function handleVoice(t){
  const s=t.trim().toLowerCase().replace(/[.,!?'"]/g,'').replace(/\\s+/g,' ');
  if(!s) return;
  heard.textContent='You: '+t;
  if(/\\bsnap\\b/.test(s)){ sendMsg('(snap)', true); return; }
  if(/\\bcount\\b/.test(s)){ countWithSteady(); return; }
  if(/\\b(left|right|up|down|closer|back|tilt|rotate)\\b/.test(s)){
    sendMsg('(aim) '+t.trim(), false);
    return;
  }
  sendMsg(t.trim(), false);
}

function setMicUi(on){
  const b=document.getElementById('mic');
  if(on){ b.classList.remove('off'); b.textContent='MIC ON'; status.textContent='Listening — say SNAP · left · right'; }
  else{ b.classList.add('off'); b.textContent='MIC OFF'; }
}
function startMic(){
  const SR=window.SpeechRecognition||window.webkitSpeechRecognition;
  if(!SR){ document.getElementById('mic').textContent='MIC N/A'; return; }
  if(!recognition){
    recognition=new SR();
    recognition.continuous=true;
    recognition.interimResults=true;
    recognition.lang='en-US';
    recognition.onresult=(e)=>{
      let t='';
      for(let i=e.resultIndex;i<e.results.length;i++) t+=e.results[i][0].transcript;
      document.getElementById('typed').value=t;
      if(e.results[e.results.length-1].isFinal&&t.trim()) handleVoice(t);
    };
    recognition.onend=()=>{ if(micOn) setTimeout(()=>{ try{recognition.start();}catch(x){} }, 400); };
  }
  micOn=true; setMicUi(true);
  try{ recognition.start(); }catch(e){ devLog('mic', String(e)); }
}
function stopMic(){
  micOn=false; setMicUi(false);
  try{ recognition.stop(); }catch(e){}
}

async function refreshPanels(){
  try{
    const [p,s]=await Promise.all([fetch('/api/pending'), fetch('/status')]);
    const pj=await p.json(), sj=await s.json();
    document.getElementById('pending').textContent=(pj.pending||'(none)').slice(0,1200);
    document.getElementById('fleet').textContent=
      'service: '+sj.service+'\\nlatest_snap: '+(sj.latest_snap||'none')+'\\nphone_inbox: '+sj.phone_inbox;
  }catch(e){ devLog('panels', String(e)); }
}

async function countWithSteady(){
  if(sending) return;
  const h=document.getElementById('typed').value.trim();
  const text=h?'(count) '+h:'(count)';
  for(const n of [3,2,1]){
    status.textContent='Aim shelf — hold still '+n+'…';
    wait.classList.add('on');
    wait.textContent='Aim shelf — hold still '+n+'…';
    await new Promise(r=>setTimeout(r,1000));
  }
  wait.textContent='Snapping…';
  await sendMsg(text, true);
}

document.getElementById('snap').onclick=()=>sendMsg('(snap)', true);
document.getElementById('count').onclick=()=>countWithSteady();
document.getElementById('mic').onclick=()=>{ if(micOn) stopMic(); else startMic(); };
document.getElementById('flip').onclick=()=>flipCam();
document.getElementById('send').onclick=()=>sendMsg(document.getElementById('typed').value);
document.getElementById('typed').addEventListener('keydown',(e)=>{
  if(e.key==='Enter'){ e.preventDefault(); sendMsg(document.getElementById('typed').value); }
});
document.getElementById('speak').onclick=()=>{
  if(lastReply&&window.speechSynthesis){
    speechSynthesis.cancel();
    const u=new SpeechSynthesisUtterance(lastReply); speechSynthesis.speak(u);
  }
};
document.getElementById('toPhone').onclick=async()=>{
  const text=document.getElementById('captn').value.trim();
  if(!text) return;
  const r=await fetch('/api/reply',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({text})});
  const j=await r.json();
  devLog('reply', j);
  document.getElementById('captn').value='';
  pollSay();
};

startCam();
startMic();
pollSay();
refreshPanels();
setInterval(pollSay, 2000);
setInterval(refreshPanels, 5000);
fetch('/api/devlog').then(r=>r.json()).then(j=>{
  if(j.server) devLog('boot', j.server.slice(-6).join('\\n'));
}).catch(()=>{});
</script></body></html>"""

ROVER_PAGE = (
    PHONE_PAGE.replace("<title>MESH RADIO</title>", "<title>ROVER</title>")
    .replace("<h1>MESH RADIO</h1>", "<h1>ROVER</h1>")
    .replace(
        "<p class=\"sub\">Drive mode — MIC ON = just talk (auto-sends). Type only if parked.</p>",
        "<p class=\"sub\">Moto LTE · MIC ON = talk · SNAP = eyes · HEAR AGAIN for CAPTN</p>"
        "<p class=\"sub\" style=\"color:#c96;font-size:0.9rem\">No Gemini Live on phone — this page only.</p>",
    )
    .replace('<div class="dev">', '<div class="dev" style="display:none">')
)


@app.route("/")
def home():
    return PHONE_PAGE


@app.route("/rover")
def rover():
    return ROVER_PAGE


@app.route("/desk")
def desk():
    return DESK_PAGE


@app.route("/office")
def office():
    return OFFICE_PAGE


@app.route("/qr")
def qr():
    return _qr_page()


@app.route("/status")
def status():
    snaps = sorted(EYES_OUT.glob("eyes_*.jpg"), key=lambda p: p.stat().st_mtime, reverse=True)
    say = SAY_FILE.read_text(encoding="utf-8").strip() if SAY_FILE.is_file() else ""
    return jsonify(
        {
            "ok": True,
            "service": "mesh_radio",
            "port": 8765,
            "eyes": str(EYES_OUT),
            "phone_inbox": str(PHONE_INBOX),
            "latest_snap": snaps[0].name if snaps else None,
            "say": say,
            "mesh": "http://100.115.92.26:8765",
        }
    )


@app.route("/snap", methods=["POST"])
def snap_only():
    data = request.get_json(force=True, silent=True) or {}
    name = _save_snap((data.get("image") or "").strip())
    if not name:
        return jsonify({"ok": False, "error": "bad image"}), 400
    return jsonify({"ok": True, "name": name})


@app.route("/api/said", methods=["POST"])
def api_said():
    data = request.get_json(force=True, silent=True) or {}
    text = (data.get("text") or "").strip()
    if not text:
        return jsonify({"ok": False, "error": "empty"}), 400
    image_name = _save_snap((data.get("image") or "").strip())
    text = (data.get("text") or "").strip()
    if not text:
        return jsonify({"ok": False, "error": "empty"}), 400

    count_job = _is_count_request(text) or _wants_count(text)
    if count_job and not image_name:
        image_name = _latest_snap()
        if image_name:
            _dev_log("count_attach", {"snap": image_name, "text": text[:60]})

    record = {
        "id": _ts(),
        "time": _now(),
        "text": text,
        "image": image_name,
    }
    path = PHONE_INBOX / f"said_{record['id']}.json"
    path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    _write_pending(record)

    if count_job:
        if not image_name:
            reply = "COUNT needs a frame — point at the shelf and tap COUNT again."
            _post_say(reply)
            resp = {"ok": True, "id": record["id"], "image": None, "ack": "Need frame.", "say": reply}
            _dev_log("said", {"id": record["id"], "count": "no_frame"})
            return jsonify(resp)
        hint = _count_hint(text) if _is_count_request(text) else text
        threading.Thread(target=_run_count_job, args=(record, image_name, hint), daemon=True).start()
        resp = {
            "ok": True,
            "id": record["id"],
            "image": image_name,
            "ack": "Counting clusters…",
            "planning": 15,
        }
        _dev_log("said", {"id": record["id"], "count_start": hint[:60]})
        return jsonify(resp)

    # Snaps queue for CAPTN vision — no canned auto-reply overwriting real directions
    if image_name and (text == "(snap)" or text.startswith("(aim)") or len(text) < 20):
        resp = {
            "ok": True,
            "id": record["id"],
            "image": image_name,
            "ack": "Snap queued — CAPTN reading.",
            "planning": 8,
        }
        _dev_log("said", {"id": record["id"], "eyes_queue": text[:40]})
        return jsonify(resp)

    if _needs_think(text):
        secs = _plan_seconds(text)
        _dev_log("plan_queue", {"secs": secs, "text": text[:80], "id": record["id"]})
        # Real CAPTN answers via /api/reply — no canned auto-reply after a timer.
        resp = {
            "ok": True,
            "id": record["id"],
            "image": image_name,
            "ack": "Queued for CAPTN.",
            "planning": secs,
        }
        _dev_log("said", {"id": record["id"], "plan_queue": secs})
        return jsonify(resp)

    reply = _auto_reply(text, image_name)
    _post_say(reply)
    resp = {"ok": True, "id": record["id"], "image": image_name, "ack": "Sent.", "say": reply}
    _dev_log("said", {"id": record["id"], "text": text[:80], "say": reply[:80]})
    return jsonify(resp)


@app.route("/api/say")
def api_say():
    text = SAY_FILE.read_text(encoding="utf-8").strip() if SAY_FILE.is_file() else ""
    updated = ""
    if SAY_FILE.is_file():
        updated = datetime.fromtimestamp(SAY_FILE.stat().st_mtime, timezone.utc).astimezone().isoformat()
    return jsonify({"ok": True, "text": text, "updated": updated})


@app.route("/api/pending")
def api_pending():
    text = PENDING_MD.read_text(encoding="utf-8") if PENDING_MD.is_file() else "(none)"
    return jsonify({"ok": True, "pending": text})


@app.route("/api/reply", methods=["POST"])
def api_reply():
    data = request.get_json(force=True, silent=True) or {}
    text = (data.get("text") or "").strip()
    if not text:
        return jsonify({"ok": False, "error": "empty"}), 400
    SAY_FILE.write_text(text + "\n", encoding="utf-8")
    _broadcast({"type": "say", "text": text})
    _dev_log("reply", text)
    return jsonify({"ok": True, "text": text})


@app.route("/api/devlog")
def api_devlog():
    with _lock:
        mem = list(_dev_lines[-40:])
    file_tail: list[str] = []
    try:
        if DEV_LOG_FILE.is_file():
            lines = DEV_LOG_FILE.read_text(encoding="utf-8").splitlines()
            file_tail = lines[-40:]
    except OSError:
        pass
    return jsonify({"ok": True, "server": mem or file_tail, "file": str(DEV_LOG_FILE)})


@app.route("/api/events")
def api_events():
    def stream():
        while True:
            try:
                ev = _event_q.get(timeout=25)
                yield f"data: {json.dumps(ev)}\n\n"
            except queue.Empty:
                yield f"data: {json.dumps({'type': 'ping'})}\n\n"

    return Response(stream(), mimetype="text/event-stream", headers={"Cache-Control": "no-cache"})


if __name__ == "__main__":
    _dev_log("boot", "mesh_radio :8765")
    app.run(host="0.0.0.0", port=8765, threaded=True, debug=False)
