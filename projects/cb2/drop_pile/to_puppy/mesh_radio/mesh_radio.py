#!/usr/bin/env python3
"""MESH RADIO — phone extension over Tailscale. Camera + mic + SSE replies. Drive bus."""
from __future__ import annotations

import base64
import json
import os
import queue
import threading
import time
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

for d in (EYES_OUT, PHONE_INBOX, PHONE_DIR):
    d.mkdir(parents=True, exist_ok=True)

app = Flask(__name__)
_event_q: queue.Queue[dict] = queue.Queue()
_say_mtime: float = 0.0
_lock = threading.Lock()


def _now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat()


def _ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _broadcast(event: dict) -> None:
    event = {**event, "time": _now()}
    _event_q.put(event)
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
    lines = [
        "# Phone — waiting for CAPTN",
        f"Updated: {_now()}",
        "",
        f"**Time:** {record.get('time')}",
        f"**You said:** {record.get('text', '')}",
        f"**Frame:** {record.get('image') or 'none'}",
        "",
        "CAPTN: write one short line to `phone/say.txt` or POST /api/reply",
        "",
    ]
    PENDING_MD.write_text("\n".join(lines), encoding="utf-8")


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
        except OSError:
            pass
        time.sleep(1.0)


threading.Thread(target=_watch_say_file, daemon=True).start()

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
  #talk { background: #e74c3c; color: #fff; flex: 1; min-width: 140px; }
  #talk.on { background: #c0392b; animation: pulse 1s infinite; }
  #send { background: #2ecc71; color: #000; }
  #snap { background: #3498db; color: #fff; }
  #speak { background: #9b59b6; color: #fff; }
  @keyframes pulse { 50% { opacity: 0.7; } }
  #heard, #reply { font-size: 1.25rem; line-height: 1.45; padding: 0.75rem;
                   border-radius: 8px; margin: 0.5rem 0; min-height: 2.5rem; }
  #heard { background: #1a1a2e; color: #aad; }
  #reply { background: #1a2e1a; color: #afa; font-weight: 600; }
  #status { font-size: 0.95rem; color: #666; }
  input[type=text] { width: 100%; font-size: 1.2rem; padding: 0.6rem; border-radius: 8px;
                     border: 1px solid #333; background: #111; color: #eee; }
</style></head><body>
<h1>MESH RADIO</h1>
<p class="sub">Tailscale phone extension · camera + voice · CAPTN replies</p>
<p id="status">Connecting…</p>
<video id="v" autoplay playsinline muted></video>
<div class="row">
  <button id="talk">HOLD TALK</button>
  <button id="send">SEND</button>
  <button id="snap">SNAP</button>
  <button id="speak">REPEAT</button>
</div>
<input id="typed" type="text" placeholder="Or type here…">
<div id="heard"></div>
<div id="reply"></div>
<canvas id="c" hidden></canvas>
<script>
const heard = document.getElementById('heard');
const reply = document.getElementById('reply');
const status = document.getElementById('status');
let stream=null, lastReply='', recognition=null, listening=false;

function sayAloud(t){
  if(!t||!window.speechSynthesis) return;
  speechSynthesis.cancel();
  const u=new SpeechSynthesisUtterance(t);
  u.rate=0.95; speechSynthesis.speak(u);
}

async function startCam(){
  try{
    stream=await navigator.mediaDevices.getUserMedia({
      video:{facingMode:{ideal:'environment'}}, audio:false});
    document.getElementById('v').srcObject=stream;
    status.textContent='Camera on · mesh live';
  }catch(e){
    status.textContent='No camera — text/voice still work';
  }
}

function frameB64(){
  const v=document.getElementById('v'), c=document.getElementById('c');
  if(!v.videoWidth) return null;
  c.width=v.videoWidth; c.height=v.videoHeight;
  c.getContext('2d').drawImage(v,0,0);
  return c.toDataURL('image/jpeg',0.82);
}

async function sendMsg(text, withFrame=true){
  text=(text||'').trim();
  if(!text){ status.textContent='Nothing to send'; return; }
  heard.textContent='You: '+text;
  status.textContent='Sending…';
  const body={text};
  if(withFrame){ const f=frameB64(); if(f) body.image=f; }
  const r=await fetch('/api/said',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify(body)});
  const j=await r.json();
  status.textContent=j.ok?'Sent · waiting for CAPTN':'Error: '+(j.error||'?');
  if(j.ack) reply.textContent=j.ack;
}

document.getElementById('send').onclick=()=>sendMsg(document.getElementById('typed').value);
document.getElementById('snap').onclick=()=>sendMsg('(snap)', true);
document.getElementById('speak').onclick=()=>sayAloud(lastReply);

const SR=window.SpeechRecognition||window.webkitSpeechRecognition;
if(SR){
  recognition=new SR();
  recognition.continuous=false;
  recognition.interimResults=true;
  recognition.lang='en-US';
  recognition.onresult=(e)=>{
    let t='';
    for(let i=e.resultIndex;i<e.results.length;i++) t+=e.results[i][0].transcript;
    document.getElementById('typed').value=t;
    if(e.results[e.results.length-1].isFinal) sendMsg(t);
  };
  recognition.onend=()=>{
    listening=false;
    document.getElementById('talk').classList.remove('on');
    document.getElementById('talk').textContent='HOLD TALK';
  };
  const talkBtn=document.getElementById('talk');
  talkBtn.onmousedown=talkBtn.ontouchstart=(ev)=>{
    ev.preventDefault();
    if(listening) return;
    listening=true;
    talkBtn.classList.add('on');
    talkBtn.textContent='LISTENING…';
    recognition.start();
  };
}else{
  document.getElementById('talk').textContent='MIC N/A';
}

const es=new EventSource('/api/events');
es.onmessage=(ev)=>{
  try{
    const j=JSON.parse(ev.data);
    if(j.type==='say'&&j.text){
      lastReply=j.text;
      reply.textContent='CAPTN: '+j.text;
      sayAloud(j.text);
    }
    if(j.type==='ack'&&j.text) reply.textContent=j.text;
  }catch(e){}
};
es.onopen=()=>{ status.textContent=(status.textContent||'')+' · SSE ok'; };

startCam();
fetch('/api/say').then(r=>r.json()).then(j=>{
  if(j.text){ lastReply=j.text; reply.textContent='CAPTN: '+j.text; }
});
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
<script>
async function refresh(){
  const r=await fetch('/api/pending'); const j=await r.json();
  document.getElementById('pending').textContent=j.pending||'(none)';
}
async function reply(){
  const text=document.getElementById('line').value.trim();
  if(!text) return;
  await fetch('/api/reply',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({text})});
  document.getElementById('line').value='';
  refresh();
}
refresh(); setInterval(refresh, 3000);
</script></body></html>"""


@app.route("/")
def home():
    return PHONE_PAGE


@app.route("/desk")
def desk():
    return DESK_PAGE


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
    record = {
        "id": _ts(),
        "time": _now(),
        "text": text,
        "image": image_name,
    }
    path = PHONE_INBOX / f"said_{record['id']}.json"
    path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    _write_pending(record)
    ack = f"Heard. CAPTN answering…"
    _broadcast({"type": "ack", "text": ack})
    return jsonify({"ok": True, "id": record["id"], "image": image_name, "ack": ack})


@app.route("/api/say")
def api_say():
    text = SAY_FILE.read_text(encoding="utf-8").strip() if SAY_FILE.is_file() else ""
    return jsonify({"ok": True, "text": text})


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
    return jsonify({"ok": True, "text": text})


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
    app.run(host="0.0.0.0", port=8765, threaded=True, debug=False)
