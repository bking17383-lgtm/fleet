#!/usr/bin/env python3
"""Paste Gemini Live transcript → Drive drop_pile/from_lester/"""
from datetime import datetime, timezone
from pathlib import Path
import os
import re

from flask import Flask, jsonify, request

DRIVE = Path(os.environ.get("DRIVE", Path.home() / "GoogleDrive/MyDrive"))
if Path("/mnt/shared/GoogleDrive/MyDrive").is_dir():
    DRIVE = Path("/mnt/shared/GoogleDrive/MyDrive")
OUT = DRIVE / "drop_pile/from_lester"
OUT.mkdir(parents=True, exist_ok=True)

app = Flask(__name__)

PAGE = """<!DOCTYPE html>
<html><body style="font-family:sans-serif;max-width:640px;margin:1rem">
<h2>Lester jailbreak — transcript sink</h2>
<p>Paste what Gemini Live said (or your notes). Saves to Drive <code>drop_pile/from_lester/</code></p>
<textarea id="t" rows="14" style="width:100%;font-size:16px"></textarea><br>
<input id="tag" placeholder="tag (optional, e.g. card1)" style="width:100%;margin:0.5rem 0;font-size:16px">
<button onclick="go()" style="font-size:18px;padding:0.5rem 1rem">Save to Drive</button>
<pre id="out" style="background:#f4f4f4;padding:0.5rem"></pre>
<script>
async function go(){
  const r=await fetch('/save',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({text:document.getElementById('t').value,tag:document.getElementById('tag').value})});
  const j=await r.json();
  document.getElementById('out').textContent=JSON.stringify(j,null,2);
  if(j.ok) document.getElementById('t').value='';
}
</script></body></html>"""


@app.route("/")
def home():
    return PAGE


@app.route("/save", methods=["POST"])
def save():
    data = request.get_json(force=True, silent=True) or {}
    text = (data.get("text") or "").strip()
    if not text:
        return jsonify({"ok": False, "error": "empty"}), 400
    tag = re.sub(r"[^\w\-]", "_", (data.get("tag") or "live")[:40])
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = OUT / f"live_transcript_{tag}_{ts}.txt"
    path.write_text(f"# Lester jailbreak transcript\n# saved: {ts}\n\n{text}\n", encoding="utf-8")
    return jsonify({"ok": True, "path": str(path), "bytes": path.stat().st_size})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8765, debug=False)
