#!/usr/bin/env python3
"""Sermon Slicer — church-simple record + search (phase 1)."""
from __future__ import annotations

import json
import os
import queue
import re
import shutil
import subprocess
import threading
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

from bus_lane import bus_root, safe_mkdir
from flask import Response, jsonify, request, send_file

STAN = Path.home() / ".stan"
GROQ_ENV = STAN / "groq.env"
SERMON_ROOT = bus_root() / "Videos/sermons"
INDEX_FILE = SERMON_ROOT / "sermon_index.json"
_transcribe_q: queue.Queue[str] = queue.Queue()
_worker_started = False
GROQ_KEY = ""


def _load_groq() -> None:
    global GROQ_KEY
    if GROQ_ENV.is_file():
        for ln in GROQ_ENV.read_text(encoding="utf-8").splitlines():
            if ln.startswith("GROQ_API_KEY="):
                GROQ_KEY = ln.split("=", 1)[1].strip()
                return


_load_groq()


def _now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def _load_index() -> dict:
    if not INDEX_FILE.is_file():
        return {}
    try:
        return json.loads(INDEX_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def _save_index(index: dict) -> None:
    safe_mkdir(INDEX_FILE.parent)
    INDEX_FILE.write_text(json.dumps(index, indent=2) + "\n", encoding="utf-8")


def _ffmpeg() -> str | None:
    return shutil.which("ffmpeg")


def _extract_audio(src: Path, dst: Path) -> bool:
    ff = _ffmpeg()
    if not ff:
        return False
    try:
        subprocess.run(
            [ff, "-y", "-i", str(src), "-vn", "-ac", "1", "-ar", "16000",
             "-acodec", "libmp3lame", "-ab", "64k", str(dst)],
            check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=600,
        )
        return dst.is_file()
    except (OSError, subprocess.SubprocessError):
        return False


def _transcribe(path: Path) -> dict | None:
    if not GROQ_KEY:
        return None
    try:
        from groq import Groq

        client = Groq(api_key=GROQ_KEY)
        with open(path, "rb") as f:
            resp = client.audio.transcriptions.create(
                file=(path.name, f.read()),
                model="whisper-large-v3",
                response_format="verbose_json",
            )
        segments = []
        for seg in getattr(resp, "segments", None) or []:
            segments.append({
                "start": getattr(seg, "start", 0) if not isinstance(seg, dict) else seg.get("start", 0),
                "end": getattr(seg, "end", 0) if not isinstance(seg, dict) else seg.get("end", 0),
                "text": (getattr(seg, "text", "") if not isinstance(seg, dict) else seg.get("text", "")).strip(),
            })
        return {"full_text": (getattr(resp, "text", "") or "").strip(), "segments": segments}
    except Exception:
        return None


def _transcribe_key(key: str) -> None:
    index = _load_index()
    row = index.get(key)
    if not row:
        return
    stored = SERMON_ROOT / row["stored"]
    if not stored.is_file():
        row["status"] = "error"
        row["error"] = "file missing"
        _save_index(index)
        return
    audio = SERMON_ROOT / f"{key}.mp3"
    src = stored
    if row.get("kind") == "audio" or stored.suffix.lower() in (".webm", ".ogg", ".m4a", ".mp3"):
        if stored.suffix.lower() != ".mp3":
            if not _extract_audio(stored, audio):
                row["status"] = "error"
                row["error"] = "audio extract failed"
                _save_index(index)
                return
        else:
            audio = stored
    elif not _extract_audio(stored, audio):
        row["status"] = "error"
        row["error"] = "audio extract failed"
        _save_index(index)
        return
    result = _transcribe(audio)
    index = _load_index()
    row = index.get(key)
    if not row:
        return
    if not result:
        row["status"] = "ready"
        row["transcribed"] = False
        row["error"] = "transcribe pending — no API key or failed"
    else:
        row["full_text"] = result["full_text"]
        row["segments"] = result["segments"]
        row["transcribed"] = True
        row["status"] = "ready"
        row["error"] = ""
    _save_index(index)


def _ensure_worker() -> None:
    global _worker_started
    if _worker_started:
        return
    _worker_started = True

    def run() -> None:
        while True:
            key = _transcribe_q.get()
            try:
                _transcribe_key(key)
            finally:
                _transcribe_q.task_done()

    threading.Thread(target=run, daemon=True).start()


def stage_upload(src: Path, original: str, kind: str) -> dict:
    safe_mkdir(SERMON_ROOT)
    ext = Path(original).suffix.lower() or (".webm" if kind == "audio" else ".mp4")
    key = f"{int(time.time())}_{uuid.uuid4().hex[:8]}"
    stored = f"{key}{ext}"
    dest = SERMON_ROOT / stored
    shutil.copy2(src, dest)
    index = _load_index()
    index[key] = {
        "stored": stored,
        "title": original or f"Sermon {_now()[:10]}",
        "kind": kind,
        "created": _now(),
        "status": "processing",
        "transcribed": False,
        "full_text": "",
        "segments": [],
        "error": "",
    }
    _save_index(index)
    _ensure_worker()
    _transcribe_q.put(key)
    return {"key": key, "title": index[key]["title"], "status": "processing"}


def search_sermons(query: str) -> list[dict]:
    q = query.strip().lower()
    if not q:
        return []
    out: list[dict] = []
    for key, row in _load_index().items():
        for seg in row.get("segments") or []:
            text = (seg.get("text") or "").strip()
            if q in text.lower():
                out.append({
                    "key": key,
                    "title": row.get("title") or key,
                    "start": seg.get("start", 0),
                    "text": text,
                    "kind": row.get("kind", "video"),
                })
    out.sort(key=lambda r: (r["title"], r["start"]))
    return out


SERMON_HTML = r"""<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no">
<meta name="theme-color" content="#2c1810">
<title>Sermon Words</title>
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: Georgia, "Times New Roman", serif; background: #faf6f0; color: #2c1810;
  min-height: 100vh; padding: 1rem 1rem 2rem; max-width: 26rem; margin: 0 auto; }
h1 { font-size: 1.5rem; text-align: center; margin: 0.5rem 0; }
.sub { text-align: center; font-size: 0.95rem; color: #6b5344; margin-bottom: 1.5rem; line-height: 1.4; }
.btn { display: block; width: 100%; padding: 1.25rem 1rem; margin: 0.75rem 0; font-size: 1.15rem;
  font-family: inherit; font-weight: 700; border: 3px solid #2c1810; border-radius: 12px;
  background: #fff; color: #2c1810; cursor: pointer; }
.btn-primary { background: #2c1810; color: #faf6f0; }
.btn-record { background: #8b2500; color: #fff; border-color: #8b2500; font-size: 1.35rem; }
.btn:active { opacity: 0.9; transform: scale(0.99); }
.hidden { display: none !important; }
.status { background: #fff; border: 2px solid #c4a882; border-radius: 10px; padding: 1rem;
  margin: 1rem 0; font-size: 1rem; line-height: 1.5; text-align: center; }
input[type=text] { width: 100%; padding: 1rem; font-size: 1.1rem; font-family: inherit;
  border: 3px solid #2c1810; border-radius: 10px; margin: 0.5rem 0 1rem; }
.card { background: #fff; border: 2px solid #c4a882; border-radius: 10px; padding: 1rem;
  margin: 0.65rem 0; cursor: pointer; }
.card .when { font-size: 0.85rem; color: #8b6914; margin-top: 0.35rem; }
video, audio { width: 100%; margin: 0.75rem 0; border-radius: 8px; }
.back { font-size: 0.9rem; color: #6b5344; background: none; border: none; text-decoration: underline;
  cursor: pointer; margin-bottom: 0.5rem; display: block; }
</style></head><body>
<div id="screen-welcome">
  <h1>Sermon Words</h1>
  <p class="sub">Welcome.<br>Record a sermon or find a clip for bible study.</p>
  <button class="btn btn-primary" id="go-record">Record a sermon</button>
  <button class="btn" id="go-find">Find a clip</button>
</div>
<div id="screen-mode" class="hidden">
  <button class="back" id="back-mode">← Back</button>
  <h1>Record</h1>
  <p class="sub">Do you want video or just audio?</p>
  <button class="btn btn-primary" id="pick-video">Video</button>
  <button class="btn" id="pick-audio">Just audio</button>
</div>
<div id="screen-record" class="hidden">
  <button class="back" id="back-record">← Back</button>
  <h1>Recording</h1>
  <p class="sub" id="record-hint">Tap START when the sermon begins.<br>Tap STOP when it ends.</p>
  <div class="status" id="record-status">Ready</div>
  <button class="btn btn-record" id="rec-btn">START</button>
  <video id="preview" class="hidden" playsinline muted></video>
</div>
<div id="screen-find" class="hidden">
  <button class="back" id="back-find">← Back</button>
  <h1>Find a clip</h1>
  <p class="sub">Type a word you remember from the sermon.</p>
  <input type="text" id="search-q" placeholder="Try faith, grace, Matthew…">
  <button class="btn btn-primary" id="search-btn">Search</button>
  <div id="search-results"></div>
  <video id="player-v" controls playsinline class="hidden"></video>
  <audio id="player-a" controls class="hidden"></audio>
</div>
<script>
let recMode = 'video', mediaStream = null, recorder = null, chunks = [], recording = false;

function show(id) {
  ['screen-welcome','screen-mode','screen-record','screen-find'].forEach(s => {
    document.getElementById(s).classList.toggle('hidden', s !== id);
  });
}

document.getElementById('go-record').onclick = () => show('screen-mode');
document.getElementById('go-find').onclick = () => { show('screen-find'); loadReady(); };
document.getElementById('back-mode').onclick = () => show('screen-welcome');
document.getElementById('back-record').onclick = () => { stopRec(); show('screen-mode'); };
document.getElementById('back-find').onclick = () => show('screen-welcome');

document.getElementById('pick-video').onclick = () => { recMode = 'video'; startRecordScreen(); };
document.getElementById('pick-audio').onclick = () => { recMode = 'audio'; startRecordScreen(); };

async function startRecordScreen() {
  show('screen-record');
  document.getElementById('record-status').textContent = 'Ready — tap START';
  document.getElementById('rec-btn').textContent = 'START';
  document.getElementById('preview').classList.toggle('hidden', recMode !== 'video');
  recording = false;
}

async function startRec() {
  try {
    const constraints = recMode === 'video'
      ? { video: { facingMode: 'environment' }, audio: true }
      : { audio: true };
    mediaStream = await navigator.mediaDevices.getUserMedia(constraints);
    if (recMode === 'video') {
      const pv = document.getElementById('preview');
      pv.srcObject = mediaStream;
      pv.classList.remove('hidden');
      try { await pv.play(); } catch(e) {}
    }
    const mime = recMode === 'video'
      ? (MediaRecorder.isTypeSupported('video/webm;codecs=vp8,opus') ? 'video/webm;codecs=vp8,opus' : 'video/webm')
      : (MediaRecorder.isTypeSupported('audio/webm') ? 'audio/webm' : 'audio/mp4');
    recorder = new MediaRecorder(mediaStream, { mimeType: mime });
    chunks = [];
    recorder.ondataavailable = e => { if (e.data.size) chunks.push(e.data); };
    recorder.onstop = uploadRec;
    recorder.start(1000);
    recording = true;
    document.getElementById('record-status').textContent = 'Recording… tap STOP when done';
    document.getElementById('rec-btn').textContent = 'STOP';
  } catch (e) {
    document.getElementById('record-status').textContent = 'Mic/camera blocked — check phone settings';
  }
}

function stopRec() {
  if (recorder && recording) { try { recorder.stop(); } catch(e) {} }
  if (mediaStream) { mediaStream.getTracks().forEach(t => t.stop()); mediaStream = null; }
  recording = false;
}

async function uploadRec() {
  document.getElementById('record-status').textContent = 'Saving…';
  const blob = new Blob(chunks, { type: chunks[0]?.type || 'application/octet-stream' });
  const ext = recMode === 'video' ? '.webm' : '.webm';
  const fd = new FormData();
  fd.append('file', blob, 'sermon' + ext);
  fd.append('kind', recMode);
  fd.append('title', 'Sermon ' + new Date().toLocaleDateString());
  try {
    const r = await fetch('/api/sermon/upload', { method: 'POST', body: fd });
    const d = await r.json();
    if (!d.ok) throw new Error(d.error || 'upload failed');
    document.getElementById('record-status').textContent =
      'Saved! We will get it ready to search when you are on Wi-Fi.';
    document.getElementById('rec-btn').textContent = 'DONE';
  } catch (e) {
    document.getElementById('record-status').textContent = 'Save failed — try again on Wi-Fi';
  }
}

document.getElementById('rec-btn').onclick = () => {
  recording ? stopRec() : startRec();
};

async function loadReady() {
  try {
    const r = await fetch('/api/sermon/status');
    const d = await r.json();
    if (d.processing > 0) {
      const el = document.getElementById('search-results');
      el.innerHTML = '<p class="status">' + d.processing + ' sermon(s) still getting ready…</p>';
    }
  } catch(e) {}
}

document.getElementById('search-btn').onclick = doSearch;
document.getElementById('search-q').addEventListener('keypress', e => { if (e.key === 'Enter') doSearch(); });

async function doSearch() {
  const q = document.getElementById('search-q').value.trim();
  const box = document.getElementById('search-results');
  if (!q) return;
  box.innerHTML = '<p class="status">Searching…</p>';
  const r = await fetch('/api/sermon/search?q=' + encodeURIComponent(q));
  const d = await r.json();
  if (!d.results || !d.results.length) {
    box.innerHTML = '<p class="status">No matches — try another word, or wait if sermon is still getting ready.</p>';
    return;
  }
  box.innerHTML = d.results.map((hit, i) =>
    '<div class="card" data-i="' + i + '">' + hit.text +
    '<div class="when">' + hit.title + ' · ' + fmtTime(hit.start) + '</div></div>'
  ).join('');
  window._hits = d.results;
  box.querySelectorAll('.card').forEach(el => {
    el.onclick = () => playHit(window._hits[+el.dataset.i]);
  });
}

function fmtTime(s) {
  s = Math.floor(s || 0);
  return String(Math.floor(s/60)).padStart(2,'0') + ':' + String(s%60).padStart(2,'0');
}

function playHit(hit) {
  const v = document.getElementById('player-v');
  const a = document.getElementById('player-a');
  const url = '/api/sermon/file/' + hit.key;
  v.classList.add('hidden');
  a.classList.add('hidden');
  if (hit.kind === 'audio') {
    a.src = url;
    a.classList.remove('hidden');
    a.currentTime = hit.start || 0;
    a.play();
  } else {
    v.src = url;
    v.classList.remove('hidden');
    v.currentTime = hit.start || 0;
    v.play();
  }
}
</script></body></html>"""


def register_sermon_routes(app) -> None:
    @app.route("/sermon")
    def sermon_page():
        return Response(SERMON_HTML, mimetype="text/html")

    @app.route("/api/sermon/status")
    def api_sermon_status():
        index = _load_index()
        processing = sum(1 for r in index.values() if r.get("status") == "processing")
        ready = sum(1 for r in index.values() if r.get("status") == "ready")
        return jsonify({
            "ok": True,
            "processing": processing,
            "ready": ready,
            "total": len(index),
            "transcribe": bool(GROQ_KEY),
        })

    @app.route("/api/sermon/upload", methods=["POST"])
    def api_sermon_upload():
        f = request.files.get("file")
        if not f:
            return jsonify({"ok": False, "error": "no file"}), 400
        kind = (request.form.get("kind") or "video").strip().lower()
        title = (request.form.get("title") or "Sermon").strip()[:120]
        safe_mkdir(SERMON_ROOT)
        tmp = SERMON_ROOT / f"upload_{uuid.uuid4().hex}.tmp"
        f.save(tmp)
        try:
            row = stage_upload(tmp, title + (Path(f.filename or "").suffix or ""), kind)
            row["title"] = title
            index = _load_index()
            if row["key"] in index:
                index[row["key"]]["title"] = title
                _save_index(index)
            return jsonify({"ok": True, **row})
        finally:
            if tmp.is_file():
                tmp.unlink(missing_ok=True)

    @app.route("/api/sermon/search")
    def api_sermon_search():
        q = request.args.get("q", "")
        return jsonify({"ok": True, "results": search_sermons(q)})

    @app.route("/api/sermon/file/<key>")
    def api_sermon_file(key: str):
        index = _load_index()
        row = index.get(key)
        if not row:
            return jsonify({"error": "not found"}), 404
        path = SERMON_ROOT / row["stored"]
        if not path.is_file():
            return jsonify({"error": "missing"}), 404
        return send_file(path, conditional=True)
