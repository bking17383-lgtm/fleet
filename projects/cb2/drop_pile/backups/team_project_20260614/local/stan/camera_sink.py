#!/usr/bin/env python3
"""EYES — USB/Chrome camera → Drive. No LLM. Big SNAP button."""
from __future__ import annotations

import base64
import os
import re
from datetime import datetime, timezone
from pathlib import Path

from flask import Flask, jsonify, request

DRIVE = Path(os.environ.get("DRIVE", Path.home() / "GoogleDrive/MyDrive"))
if Path("/mnt/shared/GoogleDrive/MyDrive").is_dir():
    DRIVE = Path("/mnt/shared/GoogleDrive/MyDrive")
OUT = DRIVE / "eyes/inbox"
OUT.mkdir(parents=True, exist_ok=True)

app = Flask(__name__)

PAGE = """<!DOCTYPE html>
<html><head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>EYES — camera to Drive</title>
<style>
  body { font-family: system-ui, sans-serif; margin: 1rem; max-width: 720px;
         background: #111; color: #eee; }
  h1 { font-size: 2rem; margin: 0 0 0.5rem; }
  p { font-size: 1.1rem; line-height: 1.4; color: #bbb; }
  video { width: 100%; max-height: 55vh; background: #000; border-radius: 8px; }
  button { font-size: 1.6rem; padding: 0.75rem 1.5rem; margin: 0.5rem 0.5rem 0.5rem 0;
           border: none; border-radius: 8px; cursor: pointer; }
  #snap { background: #2ecc71; color: #000; font-weight: 700; }
  #auto { background: #3498db; color: #fff; }
  #auto.on { background: #e67e22; }
  #msg { font-size: 1.2rem; min-height: 2rem; margin-top: 0.75rem; }
  code { background: #222; padding: 0.1rem 0.3rem; border-radius: 4px; }
</style></head><body>
<h1>EYES</h1>
<p>Camera only. No Gemini. Saves to Drive <code>eyes/inbox/</code>. Say <b>SNAP</b> in Cursor.</p>
<video id="v" autoplay playsinline muted></video>
<canvas id="c" hidden></canvas><br>
<button id="snap" onclick="snap()">SNAP</button>
<button id="auto" onclick="toggleAuto()">Auto 30s</button>
<div id="msg"></div>
<script>
let stream=null, timer=null, auto=false;
const msg=(t,c='#8f8')=>{document.getElementById('msg').innerHTML=t;document.getElementById('msg').style.color=c;};
async function start(){
  try{
    stream=await navigator.mediaDevices.getUserMedia({video:{facingMode:'environment'},audio:false});
    document.getElementById('v').srcObject=stream;
    msg('Camera on. Plug USB cam if built-in missing.');
  }catch(e){msg('Camera blocked or missing: '+e,'#f88');}
}
async function snap(){
  const v=document.getElementById('v'), c=document.getElementById('c');
  if(!v.videoWidth){msg('No video yet','#f88');return;}
  c.width=v.videoWidth; c.height=v.videoHeight;
  c.getContext('2d').drawImage(v,0,0);
  const data=c.toDataURL('image/jpeg',0.85);
  msg('Saving…','#ff8');
  const r=await fetch('/snap',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({image:data})});
  const j=await r.json();
  if(j.ok) msg('Saved <code>'+j.name+'</code> — say SNAP in Cursor');
  else msg('Fail: '+(j.error||'?'),'#f88');
}
function toggleAuto(){
  auto=!auto;
  const b=document.getElementById('auto');
  b.textContent=auto?'Auto ON (30s)':'Auto 30s';
  b.classList.toggle('on',auto);
  clearInterval(timer);
  if(auto){snap(); timer=setInterval(snap,30000);}
}
start();
</script></body></html>"""


@app.route("/")
def home():
    return PAGE


@app.route("/status")
def status():
    snaps = sorted(OUT.glob("eyes_*.jpg"), key=lambda p: p.stat().st_mtime, reverse=True)
    latest = snaps[0].name if snaps else None
    return jsonify({"ok": True, "out": str(OUT), "count": len(snaps), "latest": latest})


@app.route("/snap", methods=["POST"])
def snap():
    data = request.get_json(force=True, silent=True) or {}
    raw = (data.get("image") or "").strip()
    if not raw.startswith("data:image"):
        return jsonify({"ok": False, "error": "no image"}), 400
    try:
        b64 = raw.split(",", 1)[1]
        img = base64.b64decode(b64)
    except (IndexError, ValueError):
        return jsonify({"ok": False, "error": "bad image"}), 400
    if len(img) < 500:
        return jsonify({"ok": False, "error": "too small"}), 400
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    name = f"eyes_{ts}.jpg"
    path = OUT / name
    path.write_bytes(img)
    return jsonify({"ok": True, "name": name, "path": str(path), "bytes": len(img)})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8765, debug=False)
