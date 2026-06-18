#!/usr/bin/env python3
"""Video Slicer — cloud-to-cloud: Drive video → server transcribe (Groq) → Drive play.

Phone upload path is temporary spike only. Production = cloud ↔ AI ↔ cloud (23min OK).
"""
import json
import math
import mimetypes
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
from urllib.parse import quote

from flask import Flask, jsonify, request, Response, render_template_string, send_from_directory, send_file

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 512 * 1024 * 1024  # 512MB per upload

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_ROOT = BASE_DIR / "uploads" / "device"
STATIC_DIR = BASE_DIR / "static"
LOCAL_INDEX_FILE = BASE_DIR / "uploads" / "device_index.json"
SERVER_INDEX_FILE = Path.home() / "video_index.json"
DRIVE_VIDEO_ROOT = Path("/mnt/shared/GoogleDrive/MyDrive/Videos")
DRIVE_INDEX_FILE = DRIVE_VIDEO_ROOT / "video_index.json"
# Skip likely medical camera-roll filenames (Brian note 2026-06-12)
CONTENT_SKIP_TERMS = (
    "medical", "xray", "x-ray", "mri", "surgery", "wound", "hospital",
    "diagnosis", "prescription", "dermatology", "ultrasound", "biopsy",
)
DEV_LOG = Path.home() / ".stan" / "slicer_dev.jsonl"


def _dev_log(event: str, **fields) -> None:
    """Invisible dev feedback — Big Daddy reads ~/.stan/slicer_dev.jsonl"""
    try:
        DEV_LOG.parent.mkdir(parents=True, exist_ok=True)
        row = {
            "at": datetime.now(timezone.utc).astimezone().isoformat(),
            "event": event,
            "ip": (request.remote_addr if request else ""),
            "path": (request.path if request else ""),
            **fields,
        }
        with DEV_LOG.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, default=str) + "\n")
    except Exception:
        pass


def _load_drive_map() -> dict[str, str]:
    file_map: dict[str, str] = {}
    for i in range(1, 10):
        page_file = Path.home() / f"page{i}.json"
        if not page_file.is_file():
            continue
        try:
            for item in json.loads(page_file.read_text(encoding="utf-8")):
                title = item.get("title")
                file_id = item.get("id")
                if title and file_id:
                    file_map[os.path.basename(title).lower().strip()] = file_id
        except Exception:
            pass
    return file_map


DRIVE_MAP = _load_drive_map()


def _drive_id_for_video(video_name: str) -> str:
    clean = os.path.basename(video_name).lower().strip()
    if clean in DRIVE_MAP:
        return DRIVE_MAP[clean]
    for title, file_id in DRIVE_MAP.items():
        if clean in title or title in clean:
            return file_id
    return ""

UPLOAD_ROOT.mkdir(parents=True, exist_ok=True)
STATIC_DIR.mkdir(parents=True, exist_ok=True)

VIDEO_DIRS = [
    str(UPLOAD_ROOT),
    str(DRIVE_VIDEO_ROOT),
    str(Path.home() / "Facebook videos"),
    "/mnt/shared/MyFiles/Downloads",
    ".",
]

def _cloud_enabled() -> bool:
    return DRIVE_VIDEO_ROOT.is_dir() and (
        SERVER_INDEX_FILE.is_file() or DRIVE_INDEX_FILE.is_file()
    )


def _cloud_index_file() -> Path:
    if SERVER_INDEX_FILE.is_file():
        return SERVER_INDEX_FILE
    return DRIVE_INDEX_FILE


def _cloud_index() -> dict:
    if not _cloud_enabled():
        return {}
    return _load_json(_cloud_index_file())


def _is_excluded_content(name: str) -> bool:
    low = os.path.basename(name).lower()
    return any(term in low for term in CONTENT_SKIP_TERMS)


def _cloud_video_playable(name: str) -> bool:
    if _is_excluded_content(name):
        return False
    return (DRIVE_VIDEO_ROOT / os.path.basename(name)).is_file()

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
SLICER_TWA_PACKAGE = os.environ.get("SLICER_TWA_PACKAGE", "")
SLICER_TWA_SHA256 = os.environ.get("SLICER_TWA_SHA256", "")
UPLOADS_PER_IP_DAY = int(os.environ.get("SLICER_UPLOADS_PER_IP_DAY", "10") or "10")
_RATE_FILE = BASE_DIR / "uploads" / "upload_rate.json"

# Phone upload + Groq transcription limits (local test build)
MAX_SINGLE_UPLOAD_MB = 50       # one-pass through tunnel
MAX_SPLIT_UPLOAD_MB = 150       # upload then split on server
MAX_SINGLE_SECONDS = 360        # ~6 min — recommend split above
CHUNK_SECONDS = 300             # 5 min parts when splitting
GROQ_AUDIO_MB_LIMIT = 24        # under Groq 25MB cap (32kbps mono ≈ 100+ min audio)
UPLOAD_TIMEOUT_SINGLE_S = 120
UPLOAD_TIMEOUT_SPLIT_S = 600


def _load_groq_key() -> None:
    global GROQ_API_KEY
    if GROQ_API_KEY:
        return
    env_file = Path.home() / ".stan" / "groq.env"
    if not env_file.is_file():
        return
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line.startswith("GROQ_API_KEY="):
            GROQ_API_KEY = line.split("=", 1)[1].strip().strip('"').strip("'")
            os.environ["GROQ_API_KEY"] = GROQ_API_KEY
            break


_load_groq_key()


def _upload_rate_ok(ip: str) -> tuple[bool, str]:
    """Daily upload cap per IP — no Groq blank check."""
    if UPLOADS_PER_IP_DAY <= 0:
        return True, ""
    day = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    data = _load_json(_RATE_FILE)
    bucket = data.setdefault(day, {})
    count = int(bucket.get(ip, 0))
    if count >= UPLOADS_PER_IP_DAY:
        return False, f"Daily upload limit ({UPLOADS_PER_IP_DAY}) — try tomorrow."
    return True, ""


def _upload_rate_record(ip: str, n: int = 1) -> None:
    if UPLOADS_PER_IP_DAY <= 0 or n <= 0:
        return
    day = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    data = _load_json(_RATE_FILE)
    bucket = data.setdefault(day, {})
    bucket[ip] = int(bucket.get(ip, 0)) + n
    _save_json(_RATE_FILE, data)


def _load_json(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _local_index() -> dict:
    return _load_json(LOCAL_INDEX_FILE)


def _save_local_index(index: dict) -> None:
    _save_json(LOCAL_INDEX_FILE, index)


def _video_duration_sec(video_path: str) -> float:
    if not shutil.which("ffprobe"):
        return 0.0
    try:
        out = subprocess.run(
            [
                "ffprobe", "-v", "error", "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1", video_path,
            ],
            capture_output=True, text=True, check=True,
        )
        return float(out.stdout.strip() or 0)
    except Exception:
        return 0.0


def _media_probe(video_path: str) -> dict:
    """Quick ffprobe for play diagnostics (audio track present?)."""
    if not shutil.which("ffprobe") or not os.path.isfile(video_path):
        return {}
    try:
        out = subprocess.run(
            [
                "ffprobe", "-v", "error", "-show_entries",
                "format=duration:stream=codec_type,codec_name,channels",
                "-of", "json", video_path,
            ],
            capture_output=True, text=True, timeout=8, check=True,
        )
        data = json.loads(out.stdout)
        streams = data.get("streams") or []
        audio = next((s for s in streams if s.get("codec_type") == "audio"), None)
        video = next((s for s in streams if s.get("codec_type") == "video"), None)
        return {
            "dur": round(float((data.get("format") or {}).get("duration") or 0), 2),
            "audio_codec": (audio or {}).get("codec_name") or "none",
            "audio_ch": (audio or {}).get("channels") or 0,
            "video_codec": (video or {}).get("codec_name") or "none",
        }
    except Exception as e:
        return {"probe_err": str(e)[:80]}


def _split_video_parts(video_path: str, chunk_sec: int = CHUNK_SECONDS) -> list[str]:
    """Split long video into chunk_sec segments for separate transcription."""
    if not shutil.which("ffmpeg"):
        return [video_path]
    duration = _video_duration_sec(video_path)
    if duration <= chunk_sec:
        return [video_path]

    base = Path(video_path)
    tmp_dir = STATIC_DIR / "split"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    parts: list[str] = []
    n_parts = max(1, math.ceil(duration / chunk_sec))

    for i in range(n_parts):
        start = i * chunk_sec
        out = tmp_dir / f"{base.stem}_part{i + 1:02d}_{uuid.uuid4().hex[:6]}.mp4"
        cmd = [
            "ffmpeg", "-y", "-ss", str(start), "-i", video_path,
            "-t", str(chunk_sec), "-c", "copy", "-movflags", "+faststart", str(out),
        ]
        try:
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if out.is_file() and out.stat().st_size > 0:
                parts.append(str(out))
        except Exception:
            break

    return parts or [video_path]


def _ensure_faststart(video_path: Path) -> bool:
    """Move moov atom to front so phones can play without tail range requests."""
    if not shutil.which("ffmpeg") or not video_path.is_file():
        return False
    tmp = video_path.with_suffix(".fast.mp4")
    cmd = [
        "ffmpeg", "-y", "-i", str(video_path), "-c", "copy",
        "-movflags", "+faststart", str(tmp),
    ]
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        tmp.replace(video_path)
        return True
    except Exception:
        try:
            tmp.unlink(missing_ok=True)
        except OSError:
            pass
        return False


def extract_audio(video_path: str, audio_path: str) -> bool:
    if not shutil.which("ffmpeg"):
        return False
    cmd = [
        "ffmpeg", "-y", "-i", video_path, "-vn", "-ac", "1", "-ar", "16000",
        "-acodec", "libmp3lame", "-ab", "32k", audio_path,
    ]
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except subprocess.CalledProcessError:
        return False


def transcribe_audio(audio_path: str) -> dict | None:
    if not GROQ_API_KEY:
        return None
    try:
        from groq import Groq
        client = Groq(api_key=GROQ_API_KEY)
        with open(audio_path, "rb") as f:
            response = client.audio.transcriptions.create(
                file=(os.path.basename(audio_path), f.read()),
                model="whisper-large-v3",
                response_format="verbose_json",
            )
        segments = []
        raw_segments = getattr(response, "segments", None) or []
        for seg in raw_segments:
            segments.append({
                "start": getattr(seg, "start", 0) if not isinstance(seg, dict) else seg.get("start", 0),
                "end": getattr(seg, "end", 0) if not isinstance(seg, dict) else seg.get("end", 0),
                "text": (getattr(seg, "text", "") if not isinstance(seg, dict) else seg.get("text", "")).strip(),
            })
        full_text = getattr(response, "text", "") or ""
        return {"full_text": full_text.strip(), "segments": segments}
    except Exception:
        return None


_load_groq_key()

_transcribe_q: queue.Queue[str] = queue.Queue()
_transcribe_started = False


def _ensure_transcribe_worker() -> None:
    global _transcribe_started
    if _transcribe_started:
        return
    _transcribe_started = True

    def worker() -> None:
        while True:
            key = _transcribe_q.get()
            try:
                _transcribe_video_key(key)
            except Exception as exc:
                index = _local_index()
                if key in index:
                    index[key]["status"] = "error"
                    index[key]["error"] = str(exc)[:200]
                    _save_local_index(index)
            finally:
                _transcribe_q.task_done()

    threading.Thread(target=worker, daemon=True).start()


def stage_upload_single(src_path: str, original_name: str, parent_name: str = "") -> dict:
    """Save one file fast; queue transcription in background."""
    safe = re.sub(r"[^a-zA-Z0-9._-]+", "_", original_name)[:120] or "video.mp4"
    stored = f"{int(time.time())}_{uuid.uuid4().hex[:8]}_{safe}"
    dest = UPLOAD_ROOT / stored
    shutil.copy2(src_path, dest)
    _ensure_faststart(dest)

    key = f"device/{stored}"
    index = _local_index()
    index[key] = {
        "mtime": os.path.getmtime(dest),
        "original_name": original_name,
        "parent_name": parent_name or original_name,
        "stored_name": stored,
        "duration_sec": round(_video_duration_sec(str(dest)), 1),
        "full_text": "",
        "segments": [],
        "transcribed": False,
        "status": "processing",
        "source": "device",
    }
    _save_local_index(index)
    _ensure_transcribe_worker()
    _transcribe_q.put(key)
    _dev_log("upload_staged", name=original_name, key=key)
    return {
        "video": key,
        "name": original_name,
        "segments": 0,
        "transcribed": False,
        "status": "processing",
    }


def stage_upload(src_path: str, original_name: str, split: bool = False) -> list[dict]:
    """Save file(s); split long uploads into parts when requested."""
    size_mb = os.path.getsize(src_path) / (1024 * 1024)
    duration = _video_duration_sec(src_path)
    needs_split = split or size_mb > MAX_SINGLE_UPLOAD_MB or duration > MAX_SINGLE_SECONDS

    if needs_split and size_mb > MAX_SPLIT_UPLOAD_MB:
        raise ValueError(
            f"File too large ({size_mb:.0f}MB). Max with split is {MAX_SPLIT_UPLOAD_MB}MB."
        )

    if not needs_split:
        return [stage_upload_single(src_path, original_name)]

    part_paths = _split_video_parts(src_path, CHUNK_SECONDS)
    n_parts = len(part_paths)
    stem = Path(original_name).stem
    suffix = Path(original_name).suffix or ".mp4"
    added: list[dict] = []

    for i, part_path in enumerate(part_paths, 1):
        part_name = f"{stem} (part {i}/{n_parts}){suffix}"
        added.append(stage_upload_single(part_path, part_name, parent_name=original_name))
        if part_path != src_path:
            try:
                os.remove(part_path)
            except OSError:
                pass

    _dev_log("upload_split", name=original_name, parts=n_parts, mb=round(size_mb, 1), sec=round(duration))
    return added


def _transcribe_video_key(key: str) -> None:
    index = _local_index()
    data = index.get(key)
    if not data:
        return
    stored = data.get("stored_name")
    dest = UPLOAD_ROOT / stored
    if not dest.is_file():
        data["status"] = "error"
        data["error"] = "file missing after upload"
        _save_local_index(index)
        return

    temp_audio = str(STATIC_DIR / f"tmp_{uuid.uuid4().hex}.mp3")
    transcribed = False
    segments = []
    full_text = ""
    err = ""

    if extract_audio(str(dest), temp_audio):
        size_mb = os.path.getsize(temp_audio) / (1024 * 1024)
        if size_mb > GROQ_AUDIO_MB_LIMIT:
            err = (
                f"audio too long for API ({size_mb:.0f}MB) — "
                f"re-upload with split into {CHUNK_SECONDS // 60}-min parts"
            )
        else:
            result = transcribe_audio(temp_audio)
            if result:
                segments = result.get("segments", [])
                full_text = result.get("full_text", "")
                transcribed = bool(segments or full_text)
            else:
                err = "transcription failed — check GROQ key or rate limit"
    else:
        err = "could not extract audio (ffmpeg)"

    if os.path.exists(temp_audio):
        try:
            os.remove(temp_audio)
        except OSError:
            pass

    if not transcribed:
        segments = [{
            "start": 0,
            "end": 0,
            "text": f"[{err or 'transcription pending'}] {data.get('original_name', key)}",
        }]
        full_text = segments[0]["text"]

    data["full_text"] = full_text
    data["segments"] = segments
    data["transcribed"] = transcribed
    data["status"] = "ready" if transcribed else "error"
    if err and not transcribed:
        data["error"] = err
    index[key] = data
    _save_local_index(index)
    _dev_log("transcribe_done", key=key, ok=transcribed, err=err[:80] if err else "")


def ingest_video_file(src_path: str, original_name: str) -> dict:
    """Sync path — kept for CLI/tests; web uses stage_upload."""
    items = stage_upload(src_path, original_name)
    item = items[0]
    _transcribe_video_key(item["video"])
    index = _local_index()
    row = index.get(item["video"], {})
    return {
        **item,
        "segments": len(row.get("segments", [])),
        "transcribed": row.get("transcribed", False),
        "status": row.get("status", "ready"),
    }


def get_phonetic_key(word: str) -> str:
    if not word:
        return ""
    word = "".join(c for c in word.lower() if c.isalpha())
    if not word:
        return ""
    for a, b in (("ph", "f"), ("sh", "s"), ("ch", "c"), ("v", "f"), ("y", "i"), ("k", "c")):
        word = word.replace(a, b)
    if len(word) > 2 and word.endswith("h"):
        word = word[:-1]
    first, rest = word[0], word[1:]
    rest_no_vowels = "".join(c for c in rest if c not in "aeiou")
    out, prev = [], ""
    for char in first + rest_no_vowels:
        if char != prev:
            out.append(char)
            prev = char
    return "".join(out)


def _search_one_index(index: dict, query: str, source: str) -> list:
    exact_matches, phonetic_matches = [], []
    query_words = query.split()
    query_keys = [get_phonetic_key(w) for w in query_words if w]
    if not query_keys:
        return []

    for video, data in index.items():
        segments = data.get("segments", [])
        for i, seg in enumerate(segments):
            seg_text = seg.get("text", "").lower()
            is_exact = query in seg_text
            is_phonetic = False
            if not is_exact:
                seg_keys = [get_phonetic_key(w) for w in seg_text.split() if w]
                is_phonetic = all(qk in seg_keys for qk in query_keys)
            if not (is_exact or is_phonetic):
                continue
            prev_text = segments[i - 1].get("text", "").strip() if i > 0 else ""
            next_text = segments[i + 1].get("text", "").strip() if i < len(segments) - 1 else ""
            context = " ".join(x for x in [
                f"... {prev_text}" if prev_text else "",
                seg.get("text", "").strip(),
                f"{next_text} ..." if next_text else "",
            ] if x)
            item = {
                "video": video,
                "start": seg.get("start", 0),
                "text": seg.get("text", ""),
                "better_context": context,
                "is_phonetic": is_phonetic and not is_exact,
                "source": source,
                "display_name": data.get("original_name") or os.path.basename(video),
            }
            (exact_matches if is_exact else phonetic_matches).append(item)
    return exact_matches + phonetic_matches


def search_index(query: str, include_cloud: bool | None = None, include_device: bool = True) -> list:
    query = re.sub(r"[^\w\s]", "", query.strip().lower()).strip()
    if not query:
        return []
    if include_cloud is None:
        include_cloud = _cloud_enabled()
    results: list = []
    if include_device:
        results.extend(_search_one_index(_local_index(), query, "device"))
    if include_cloud:
        cloud = _search_one_index(_cloud_index(), query, "cloud")
        for item in cloud:
            if not _cloud_video_playable(item["video"]):
                continue
            item["drive_id"] = _drive_id_for_video(item["video"])
            item["display_name"] = os.path.basename(item["video"])
        results.extend(cloud)
    return results


def resolve_video_path(video_name: str) -> str | None:
    if video_name.startswith("device/"):
        path = UPLOAD_ROOT / video_name.split("/", 1)[1]
        return str(path) if path.is_file() else None
    basename = os.path.basename(video_name)
    cloud_path = DRIVE_VIDEO_ROOT / basename
    if cloud_path.is_file() and not _is_excluded_content(basename):
        return str(cloud_path)
    for d in VIDEO_DIRS:
        test = os.path.join(d, video_name)
        if os.path.isfile(test):
            return test
        test_base = os.path.join(d, basename)
        if os.path.isfile(test_base):
            return test_base
    return None


def stream_partial_file(path: str, byte_range: str | None):
    file_size = os.path.getsize(path)
    start, end = 0, file_size - 1
    if byte_range:
        match = re.match(r"bytes=(\d+)-(\d*)", byte_range)
        if match:
            start = int(match.group(1))
            if match.group(2):
                end = int(match.group(2))
    end = min(end, file_size - 1)
    length = end - start + 1
    with open(path, "rb") as f:
        f.seek(start)
        data = f.read(length)
    mime_type, _ = mimetypes.guess_type(path)
    mime_type = mime_type or "video/mp4"
    rv = Response(data, 206, mimetype=mime_type, direct_passthrough=True)
    rv.headers.add("Content-Range", f"bytes {start}-{end}/{file_size}")
    rv.headers.add("Accept-Ranges", "bytes")
    rv.headers.add("Content-Length", str(length))
    return rv


@app.route("/logo.svg")
def logo():
    svg = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 120" fill="none">
  <rect x="4" y="4" width="112" height="112" stroke="#000" stroke-width="8" fill="#fff"/>
  <path d="M30 78 L50 42 L62 42 L42 78 Z" fill="#000"/>
  <path d="M58 78 L78 42 L90 42 L70 78 Z" fill="#000"/>
  <rect x="28" y="82" width="64" height="6" fill="#000"/>
</svg>"""
    return Response(svg, mimetype="image/svg+xml")


@app.route("/")
def index():
    _dev_log("page_view", ua=request.headers.get("User-Agent", "")[:120])
    resp = Response(render_template_string(HTML_TEMPLATE))
    resp.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
    resp.headers["Pragma"] = "no-cache"
    return resp


@app.after_request
def _dev_after(resp):
    if request.path.startswith("/api/") and request.path != "/api/dev/event":
        _dev_log(
            "api",
            method=request.method,
            status=resp.status_code,
            q=request.args.get("q", "")[:40],
        )
    return resp


@app.route("/api/dev/event", methods=["POST"])
def api_dev_event():
    """Invisible client telemetry — no UI."""
    payload = request.get_json(silent=True)
    if not payload:
        raw = request.get_data(as_text=True) or ""
        if raw.strip():
            try:
                payload = json.loads(raw)
            except Exception:
                payload = {"raw": raw[:200]}
        else:
            payload = {}
    event = str(payload.pop("ev", "client"))[:40]
    _dev_log(event, **{k: str(v)[:200] for k, v in payload.items()})
    return "", 204


def _limits_payload() -> dict:
    return {
        "max_single_mb": MAX_SINGLE_UPLOAD_MB,
        "max_split_mb": MAX_SPLIT_UPLOAD_MB,
        "max_single_minutes": MAX_SINGLE_SECONDS // 60,
        "chunk_minutes": CHUNK_SECONDS // 60,
        "groq_audio_mb": GROQ_AUDIO_MB_LIMIT,
        "note": (
            f"One-pass: ≤{MAX_SINGLE_SECONDS // 60} min / {MAX_SINGLE_UPLOAD_MB}MB. "
            f"Longer: split into ~{CHUNK_SECONDS // 60}-min parts (up to {MAX_SPLIT_UPLOAD_MB}MB)."
        ),
    }


@app.route("/api/status")
def api_status():
    idx = _local_index()
    cloud_playable = sum(1 for k in _cloud_index() if _cloud_video_playable(k))
    return jsonify({
        "device_videos": len(idx),
        "cloud_videos": cloud_playable,
        "transcribe_ready": bool(GROQ_API_KEY),
        "mode": "cloud+local" if _cloud_enabled() else "local",
        "limits": _limits_payload(),
    })


@app.route("/api/limits")
def api_limits():
    return jsonify(_limits_payload())


@app.route("/api/library")
def api_library():
    """Mounted Drive library — streams from penguin, not phone→Drive API."""
    if not _cloud_enabled():
        return jsonify({"count": 0, "total": 0, "videos": [], "disabled": True}), 403
    videos = []
    for name, data in _cloud_index().items():
        if not _cloud_video_playable(name):
            continue
        videos.append({
            "video": name,
            "name": name,
            "segments": len(data.get("segments", [])),
            "transcribed": bool(data.get("full_text")),
            "status": "ready",
            "source": "cloud",
        })
    videos.sort(key=lambda v: v["name"].lower())
    return jsonify({"count": len(videos), "total": len(videos), "videos": videos, "disabled": False})


@app.route("/api/catalog")
def api_catalog():
    catalog = []
    for video, data in _local_index().items():
        catalog.append({
            "video": video,
            "name": data.get("original_name") or os.path.basename(video),
            "segments": len(data.get("segments", [])),
            "transcribed": data.get("transcribed", False),
            "status": data.get("status", "ready" if data.get("transcribed") else "processing"),
            "error": data.get("error", ""),
            "source": "device",
        })
    if _cloud_enabled():
        for video, data in _cloud_index().items():
            if not _cloud_video_playable(video):
                continue
            catalog.append({
                "video": video,
                "name": video,
                "segments": len(data.get("segments", [])),
                "transcribed": bool(data.get("full_text")),
                "status": "ready",
                "error": "",
                "source": "cloud",
            })
    catalog.sort(key=lambda r: (0 if r.get("source") == "device" else 1, (r.get("name") or "").lower()))
    return jsonify(catalog)


@app.route("/api/scan/status")
def api_scan_status():
    rows = _local_index().values()
    processing = sum(1 for r in rows if r.get("status") == "processing")
    ready = sum(1 for r in rows if r.get("status") == "ready")
    errors = sum(1 for r in rows if r.get("status") == "error")
    return jsonify({
        "processing": processing,
        "ready": ready,
        "errors": errors,
        "total": processing + ready + errors,
        "transcribe_ready": bool(GROQ_API_KEY),
    })


@app.route("/api/scan", methods=["POST"])
def api_scan():
    files = request.files.getlist("videos")
    if not files:
        one = request.files.get("video")
        if one:
            files = [one]
    if not files:
        return jsonify({"error": "No videos received"}), 400

    ip = request.remote_addr or "unknown"
    ok, msg = _upload_rate_ok(ip)
    if not ok:
        return jsonify({"error": msg}), 429

    added = []
    errors = []
    split = request.form.get("split", "").lower() in ("1", "true", "yes")
    tmp_dir = STATIC_DIR / "incoming"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    for f in files:
        if not f.filename:
            continue
        tmp_path = tmp_dir / f"{uuid.uuid4().hex}_{f.filename}"
        f.save(tmp_path)
        try:
            items = stage_upload(str(tmp_path), f.filename, split=split)
            added.extend(items)
        except ValueError as exc:
            errors.append(f"{f.filename}: {exc}")
        finally:
            try:
                tmp_path.unlink(missing_ok=True)
            except Exception:
                pass

    if not added:
        msg = errors[0] if errors else "No videos saved"
        return jsonify({"error": msg, "errors": errors}), 400

    _upload_rate_record(ip, len(added))

    return jsonify({
        "status": "accepted",
        "added": added,
        "catalog": added,
        "split": split,
        "message": (
            f"Saved {len(added)} part(s). Transcribing in background — search when status shows ready."
            if split and len(added) > 1
            else f"Saved {len(added)} file(s). Transcribing in background — search when status shows ready."
        ),
        "transcribe_ready": bool(GROQ_API_KEY),
        "errors": errors,
    })


SEARCH_PAGE_SIZE = 40


def _find_segment_at(index: dict, video: str, start: float) -> tuple[list, int] | tuple[None, int]:
    data = index.get(video)
    if not data:
        return None, -1
    segments = data.get("segments", [])
    if not segments:
        return None, -1
    best_i = min(
        range(len(segments)),
        key=lambda i: abs(float(segments[i].get("start", 0)) - start),
    )
    if abs(float(segments[best_i].get("start", 0)) - start) > 2.0:
        return None, -1
    return segments, best_i


def _two_sentence_context(video: str, start: float, fallback: str = "") -> str:
    """Prev + next sentence around the match (quote sits between them)."""
    for index_fn in (_local_index, _cloud_index):
        segments, i = _find_segment_at(index_fn(), video, start)
        if segments is None or i < 0:
            continue
        prev_t = segments[i - 1].get("text", "").strip() if i > 0 else ""
        next_t = segments[i + 1].get("text", "").strip() if i < len(segments) - 1 else ""
        if prev_t and next_t:
            return f"{prev_t} {next_t}"
        if prev_t:
            quote = segments[i].get("text", "").strip()
            return f"{prev_t} {quote}" if quote and quote != prev_t else prev_t
        if next_t:
            quote = segments[i].get("text", "").strip()
            return f"{quote} {next_t}" if quote and quote != next_t else next_t
    raw = re.sub(r"^\.\.\.\s*", "", (fallback or "").strip())
    raw = re.sub(r"\s*\.\.\.$", "", raw).strip()
    if not raw:
        return ""
    parts = [p.strip() for p in re.split(r"(?<=[.!?])\s+", raw) if p.strip()]
    if len(parts) >= 2:
        return f"{parts[0]} {parts[1]}"
    return raw


def _share_watch_line(video: str, ts: str, drive_id: str = "") -> str:
    """Plain text only — social apps auto-linkify https://; no URLs in paste."""
    name = os.path.basename(video)
    base = name.rsplit(".", 1)[0] if "." in name else name
    if drive_id:
        return f"▶ Watch on Google Drive · {base} @ {ts}"
    return f"▶ Watch · {base} @ {ts}"


def _share_payload(
    video: str,
    start: float,
    quote_text: str,
    context: str = "",
    drive_id: str = "",
) -> dict:
    m, s = divmod(int(start), 60)
    ts = f"{m:02d}:{s:02d}"
    name = os.path.basename(video)
    clean_quote = (quote_text or "").strip().strip('"')
    if not clean_quote:
        segments, i = _find_segment_at(_local_index(), video, start)
        if segments is None:
            segments, i = _find_segment_at(_cloud_index(), video, start)
        if segments is not None and i >= 0:
            clean_quote = segments[i].get("text", "").strip()
    context_block = _two_sentence_context(video, start, context)
    watch_line = _share_watch_line(video, ts, drive_id or _drive_id_for_video(video))
    lines = [f'"{clean_quote}"']
    if context_block:
        lines.append("")
        lines.append(context_block)
    lines.extend(["", f"— {name} @ {ts}", watch_line, "Seize the Clip · Floater"])
    text = "\n".join(lines)
    return {
        "text": text,
        "quote": clean_quote,
        "context": context_block,
        "video": name,
        "timestamp": ts,
        "watch_line": watch_line,
    }


@app.route("/api/search")
def api_search():
    q = request.args.get("q", "")
    try:
        limit = min(max(int(request.args.get("limit", SEARCH_PAGE_SIZE)), 1), 100)
    except ValueError:
        limit = SEARCH_PAGE_SIZE
    try:
        offset = max(int(request.args.get("offset", 0)), 0)
    except ValueError:
        offset = 0
    all_results = search_index(q)
    return jsonify({
        "query": q,
        "total": len(all_results),
        "offset": offset,
        "limit": limit,
        "results": all_results[offset:offset + limit],
    })


@app.route("/api/share-text")
def api_share_text():
    video = request.args.get("video", "")
    start = float(request.args.get("start", 0) or 0)
    quote_text = request.args.get("quote", "").strip()
    context = request.args.get("context", "").strip()
    drive_id = request.args.get("drive_id", "").strip()
    return jsonify(_share_payload(video, start, quote_text, context, drive_id))


@app.route("/api/clip")
def api_clip():
    video = request.args.get("video")
    try:
        start = float(request.args.get("start", 0) or 0)
    except ValueError:
        start = 0.0
    actual_path = resolve_video_path(video)
    if not actual_path:
        return jsonify({"error": "Video not found"}), 404

    output_filename = f"clip_{int(time.time())}.mp4"
    output_path = STATIC_DIR / output_filename
    cmd = [
        "ffmpeg", "-y", "-ss", str(start), "-i", actual_path,
        "-t", "10", "-c:v", "libx264", "-preset", "veryfast", "-c:a", "aac",
        "-movflags", "+faststart", str(output_path),
    ]
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return jsonify({"status": "success", "clip_url": f"/static/{output_filename}"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/static/<path:filename>")
def static_files(filename):
    return send_from_directory(STATIC_DIR, filename)


@app.route("/video/<path:filename>")
def play_video(filename):
    path = resolve_video_path(filename)
    if not path:
        _dev_log("play_missing", video=filename[:120])
        return "File not found", 404
    mime_type, _ = mimetypes.guess_type(path)
    mime_type = mime_type or "video/mp4"
    probe = _media_probe(path)
    _dev_log(
        "play_serve",
        video=filename[:120],
        bytes=os.path.getsize(path),
        dur=probe.get("dur", "?"),
        audio=probe.get("audio_codec", "?"),
        ach=probe.get("audio_ch", "?"),
    )
    resp = send_file(path, mimetype=mime_type, conditional=True)
    resp.headers["Accept-Ranges"] = "bytes"
    resp.headers["Cache-Control"] = "private, max-age=86400"
    return resp


@app.route("/.well-known/assetlinks.json")
def assetlinks():
    """Android TWA verification — set SLICER_TWA_PACKAGE + SLICER_TWA_SHA256 on production host."""
    if not SLICER_TWA_PACKAGE or not SLICER_TWA_SHA256:
        return jsonify([])
    fps = [s.strip() for s in SLICER_TWA_SHA256.split(",") if s.strip()]
    return jsonify([
        {
            "relation": ["delegate_permission/common.handle_all_urls"],
            "target": {
                "namespace": "android_app",
                "package_name": SLICER_TWA_PACKAGE,
                "sha256_cert_fingerprints": fps,
            },
        }
    ])


@app.route("/manifest.json")
def manifest():
    return jsonify({
        "short_name": "Slicer",
        "name": "Video Slicer · Seize the Clip",
        "description": "Search spoken word in your videos. Share quotes and 10s clips.",
        "icons": [{"src": "/logo.svg", "sizes": "120x120", "type": "image/svg+xml", "purpose": "any"}],
        "start_url": "/",
        "scope": "/",
        "background_color": "#ffffff",
        "theme_color": "#000000",
        "display": "standalone",
        "orientation": "portrait",
        "categories": ["video", "utilities"],
    })


HTML_TEMPLATE = r"""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
  <title>Video Slicer</title>
  <meta name="app-version" content="search-social-14">
  <meta name="theme-color" content="#000000">
  <link rel="manifest" href="/manifest.json">
  <link rel="icon" href="/logo.svg">
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: Georgia, "Times New Roman", serif;
      background: #fff;
      color: #000;
      min-height: 100vh;
      -webkit-tap-highlight-color: transparent;
    }
    .frame {
      min-height: 100vh;
      margin: 10px;
      border: 4px solid #000;
      display: flex;
      flex-direction: column;
      max-width: 480px;
      margin-left: auto;
      margin-right: auto;
      background: #fff;
    }
    .header {
      border-bottom: 3px solid #000;
      padding: 16px;
      text-align: center;
    }
    .logo { width: 72px; height: 72px; margin: 0 auto 8px; display: block; }
    h1 { font-size: 1.35rem; letter-spacing: 0.12em; text-transform: uppercase; }
    .sub { font-size: 0.7rem; letter-spacing: 0.2em; text-transform: uppercase; margin-top: 4px; }
    .panel { padding: 16px; flex: 1; overflow-y: auto; }
    .gate p { font-size: 1rem; line-height: 1.5; margin-bottom: 16px; }
    .btn {
      display: block; width: 100%; padding: 14px 16px; margin-bottom: 10px;
      border: 3px solid #000; background: #fff; color: #000;
      font-size: 1rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.06em;
      cursor: pointer;
    }
    .btn-primary { background: #000; color: #fff; }
    .btn:disabled { opacity: 0.5; }
    .btn:active { transform: scale(0.98); }
    .hidden { display: none !important; }
    .status { font-size: 0.8rem; border: 2px solid #000; padding: 10px; margin-bottom: 12px; }
    .catalog { list-style: none; }
    .catalog li {
      border: 2px solid #000; padding: 12px; margin-bottom: 8px;
      font-size: 0.9rem;
    }
    .search-row { display: flex; gap: 8px; margin-bottom: 12px; }
    input[type=text] {
      flex: 1; border: 3px solid #000; padding: 12px; font-size: 1rem; background: #fff;
    }
    .card {
      border: 2px solid #000; padding: 12px; margin-bottom: 10px; cursor: pointer;
    }
    .card .meta { font-size: 0.75rem; margin-top: 8px; display: flex; gap: 8px; flex-wrap: wrap; }
    .btn-row { display: flex; gap: 8px; flex-wrap: wrap; margin-top: 8px; }
    .btn-row .btn { width: auto; flex: 1; min-width: 120px; margin-bottom: 0; padding: 10px 8px; font-size: 0.75rem; }
    .btn-share { background: #000; color: #fff; }
    .tag { border: 1px solid #000; padding: 2px 6px; font-size: 0.65rem; text-transform: uppercase; }
    .player-wrap { border-bottom: 3px solid #000; }
    video { width: 100%; background: #000; }
    .toast {
      position: fixed; bottom: 16px; left: 16px; right: 16px; max-width: 448px; margin: 0 auto;
      background: #000; color: #fff; padding: 12px; border: 2px solid #000; text-align: center;
      font-size: 0.85rem; z-index: 99;
    }
  </style>
</head>
<body>
  <div class="frame">
    <div class="header">
      <img src="/logo.svg" alt="Video Slicer" class="logo">
      <h1>Video Slicer</h1>
      <div class="sub">Floater · Seize the Clip</div>
    </div>

    <!-- Permission gate — optional local upload; cloud library loads automatically -->
    <div id="gate-screen" class="panel gate">
      <p><strong>Cloud library loading…</strong> Search &amp; play from Drive. Optional: pick local videos to transcribe.</p>
      <p id="limits-hint" style="font-size:0.85rem;">One pass: ~6 min / 50MB. Longer videos: we ask to split into ~5-min parts.</p>
      <input type="file" id="file-input" accept="video/*" multiple class="hidden">
      <button class="btn btn-primary" id="pick-btn" onclick="document.getElementById('file-input').click()">Pick local videos</button>
      <div id="scan-status" class="status hidden"></div>
    </div>

    <!-- Main app -->
    <div id="app-screen" class="hidden" style="display:flex;flex-direction:column;flex:1;">
      <div id="player-wrap" class="player-wrap hidden">
        <div style="padding:8px 12px;border-bottom:2px solid #000;font-size:0.8rem;display:flex;justify-content:space-between;align-items:center;gap:8px;">
          <span id="player-title" style="flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">video</span>
          <button class="btn btn-share" style="width:auto;padding:4px 10px;margin:0;" id="player-share-btn" onclick="shareCurrent()">Share</button>
          <button class="btn" style="width:auto;padding:4px 10px;margin:0;" onclick="closePlayer()">Hide</button>
        </div>
        <div id="player-loading" class="status hidden" style="margin:8px;">Loading video…</div>
        <video id="main-player" controls playsinline webkit-playsinline preload="auto" type="video/mp4"></video>
      </div>
      <div class="panel" style="flex:1;overflow-y:auto;">
        <div class="sub" style="margin-bottom:8px;">Search spoken word</div>
        <div class="search-row">
          <input type="text" id="search-input" placeholder="Try Moore, ancestry, Facebook…" autofocus>
          <button class="btn btn-primary" style="width:auto;min-width:96px;" id="search-btn" onclick="performSearch()">Search</button>
        </div>
        <div id="summary-text" class="sub" style="margin-bottom:8px;"></div>
        <div id="results-area"></div>
        <button class="btn hidden" id="load-more-btn" onclick="loadMoreResults()">Load more</button>
        <button class="btn" id="toggle-catalog-btn" style="margin-top:12px;" onclick="toggleCatalog()">Browse catalog</button>
        <div id="catalog-block" class="hidden">
          <div class="sub" style="margin:12px 0 8px;">Catalog</div>
          <div id="library-hint" class="status" style="margin-bottom:8px;">Cloud + local — streams with prefetch.</div>
          <ul id="catalog-list" class="catalog"></ul>
        </div>
        <button class="btn" style="margin-top:12px;" onclick="document.getElementById('file-input').click()">+ Add local videos</button>
      </div>
    </div>
  </div>
  <div id="toast" class="toast hidden"></div>

  <script>
    function _d(ev, extra) {
      try {
        const payload = Object.assign({ ev: ev, t: Date.now() }, extra || {});
        const body = JSON.stringify(payload);
        const blob = new Blob([body], { type: 'application/json' });
        if (!navigator.sendBeacon('/api/dev/event', blob)) {
          fetch('/api/dev/event', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body,
            keepalive: true,
          }).catch(() => {});
        }
      } catch (e) {}
    }

    function _playState(player, item, tag) {
      _d(tag, {
        video: item.video,
        dur: player.duration || 0,
        muted: player.muted ? '1' : '0',
        vol: player.volume,
        paused: player.paused ? '1' : '0',
        ct: player.currentTime || 0,
        rs: player.readyState,
      });
    }

    const _prefetchPool = new Map();
    const PREFETCH_MAX = 6;

    function videoUrl(video) {
      const parts = String(video).split('/').map(p => encodeURIComponent(p));
      return `/video/${parts.join('/')}`;
    }

    function prefetchVideo(video, level) {
      if (!video || _prefetchPool.has(video)) return;
      while (_prefetchPool.size >= PREFETCH_MAX) {
        const oldest = _prefetchPool.keys().next().value;
        const node = _prefetchPool.get(oldest);
        if (node && node.parentNode) node.parentNode.removeChild(node);
        _prefetchPool.delete(oldest);
      }
      const url = videoUrl(video);
      const v = document.createElement('video');
      v.preload = level || 'metadata';
      v.muted = true;
      v.playsInline = true;
      v.setAttribute('playsinline', '');
      v.style.cssText = 'position:absolute;width:0;height:0;opacity:0;pointer-events:none';
      v.src = url;
      document.body.appendChild(v);
      _prefetchPool.set(video, v);
      _d('prefetch_start', { video, level: v.preload });
      v.addEventListener('loadeddata', () => _d('prefetch_ready', { video, level: v.preload }), { once: true });
    }

    function prefetchMany(items, level, limit) {
      const seen = new Set();
      for (const item of items) {
        const v = item.video;
        if (!v || seen.has(v)) continue;
        seen.add(v);
        prefetchVideo(v, level);
        if (seen.size >= limit) break;
      }
    }
    _d('boot');
    if ('serviceWorker' in navigator) {
      navigator.serviceWorker.getRegistrations().then(rs => rs.forEach(r => r.unregister()));
    }

    let allResults = [];
    let searchTotal = 0;
    let searchOffset = 0;
    let searchQuery = '';
    let currentPlayItem = null;
    let catalogRows = [];
    const SEARCH_PAGE = 40;
    let LIMITS = {
      max_single_mb: 50,
      max_split_mb: 150,
      max_single_minutes: 6,
      chunk_minutes: 5,
    };
    const fileInput = document.getElementById('file-input');

    fetch('/api/status').then(r => r.json()).then(st => {
      if (st.limits) {
        LIMITS = Object.assign(LIMITS, st.limits);
        const hint = document.getElementById('limits-hint');
        if (hint) {
          hint.textContent =
            `One pass: ~${LIMITS.max_single_minutes} min / ${LIMITS.max_single_mb}MB. ` +
            `Longer: split into ~${LIMITS.chunk_minutes}-min parts (up to ${LIMITS.max_split_mb}MB).`;
        }
      }
      const libHint = document.getElementById('library-hint');
      if (libHint && st.cloud_videos) {
        libHint.textContent =
          `Cloud (${st.cloud_videos}) + local (${st.device_videos || 0}) — streams with prefetch.`;
      }
    }).catch(() => {});

    function estimateDurationSec(file) {
      // Rough phone-video guess when metadata probe is slow (~5MB/min).
      return (file.size / (5 * 1024 * 1024)) * 60;
    }

    function probeDuration(file, timeoutMs = 2500) {
      return Promise.race([
        new Promise((resolve) => {
          const url = URL.createObjectURL(file);
          const v = document.createElement('video');
          v.preload = 'metadata';
          const done = (sec) => {
            URL.revokeObjectURL(url);
            resolve(sec);
          };
          v.onloadedmetadata = () => done(v.duration || 0);
          v.onerror = () => done(0);
          v.src = url;
        }),
        new Promise((resolve) => setTimeout(() => resolve(-1), timeoutMs)),
      ]);
    }

    function needsSplit(file, durationSec) {
      const maxBytes = LIMITS.max_single_mb * 1024 * 1024;
      const maxSec = (LIMITS.max_single_minutes || 6) * 60;
      if (file.size > maxBytes) return true;
      if (durationSec > 0 && durationSec > maxSec) return true;
      // Probe timed out on a chunky file — assume long (moov-at-end phones hang here).
      if (durationSec < 0 && file.size > 25 * 1024 * 1024) return true;
      return false;
    }

    function displayDurationSec(file, durationSec) {
      if (durationSec > 0) return durationSec;
      if (durationSec < 0 || file.size > 25 * 1024 * 1024) return estimateDurationSec(file);
      return 0;
    }

    async function askSplit(file, durationSec, sizeMb) {
      const durMin = durationSec > 0 ? (durationSec / 60).toFixed(1) : '?';
      const est = durationSec <= 0 ? ' (estimated)' : '';
      return confirm(
        `This video is ~${durMin} min${est} (${sizeMb}MB).\n\n` +
        `One-pass max: ~${LIMITS.max_single_minutes} min / ${LIMITS.max_single_mb}MB.\n\n` +
        `Split into ~${LIMITS.chunk_minutes}-minute parts for transcription?`
      );
    }

    fileInput.addEventListener('change', () => uploadPickedFiles(fileInput.files));

    document.getElementById('search-input').addEventListener('keypress', (e) => {
      if (e.key === 'Enter') performSearch();
    });

    function showToast(msg) {
      const t = document.getElementById('toast');
      t.textContent = msg;
      t.classList.remove('hidden');
      setTimeout(() => t.classList.add('hidden'), 3200);
    }

    async function uploadPickedFiles(fileList) {
      if (!fileList || !fileList.length) return;
      const status = document.getElementById('scan-status');
      status.classList.remove('hidden');
      document.getElementById('pick-btn').disabled = true;

      const total = fileList.length;
      let ok = 0;
      let fail = 0;

      for (let i = 0; i < total; i++) {
        const f = fileList[i];
        const sizeMb = (f.size / (1024 * 1024)).toFixed(1);
        const overSingle = f.size > LIMITS.max_single_mb * 1024 * 1024;

        status.textContent = overSingle
          ? `Large file (${sizeMb}MB) — checking if we should split…`
          : `Checking ${f.name} (${sizeMb}MB)…`;
        _d('upload_check', { name: f.name, mb: sizeMb });

        let rawDuration = 0;
        if (overSingle) {
          rawDuration = -1; // skip slow probe — size alone triggers split prompt
        } else {
          rawDuration = await probeDuration(f, 2500);
        }
        const displaySec = displayDurationSec(f, rawDuration);
        const durMin = displaySec > 0 ? (displaySec / 60).toFixed(1) : '?';

        if (f.size > LIMITS.max_split_mb * 1024 * 1024) {
          fail++;
          status.textContent = `Skipped ${f.name} (${sizeMb}MB) — over ${LIMITS.max_split_mb}MB max.`;
          showToast(`Too large even for split (${sizeMb}MB).`);
          await new Promise(r => setTimeout(r, 2000));
          continue;
        }

        let doSplit = false;
        if (needsSplit(f, rawDuration)) {
          _d('split_prompt', { name: f.name, mb: sizeMb, dur: String(durMin) });
          doSplit = await askSplit(f, displaySec, sizeMb);
          if (!doSplit) {
            fail++;
            status.textContent = `Skipped ${f.name} (~${durMin} min) — pick a shorter clip or allow split.`;
            await new Promise(r => setTimeout(r, 2000));
            continue;
          }
        }

        status.textContent = doSplit
          ? `Uploading ${i + 1} of ${total}: ${f.name} (~${durMin} min) — will split into parts…`
          : `Uploading ${i + 1} of ${total}: ${f.name} (${sizeMb}MB)…`;
        const form = new FormData();
        form.append('video', f);
        if (doSplit) form.append('split', '1');

        let done = false;
        const uploadTimeout = doSplit ? 600000 : 120000;
        for (let attempt = 1; attempt <= 3 && !done; attempt++) {
          try {
            const ctrl = new AbortController();
            const timer = setTimeout(() => ctrl.abort(), uploadTimeout);
            const res = await fetch('/api/scan', { method: 'POST', body: form, signal: ctrl.signal });
            clearTimeout(timer);
            const data = await res.json();
            if (!res.ok) throw new Error(data.error || 'Upload failed');
            ok++;
            done = true;
            _d('upload_ok', { name: f.name, mb: sizeMb, split: doSplit ? '1' : '0', parts: (data.added || []).length });
            if (doSplit && (data.added || []).length > 1) {
              showToast(`Split into ${data.added.length} parts — transcribing each.`);
            }
          } catch (err) {
            if (attempt === 3) {
              fail++;
              _d('upload_fail', { name: f.name, err: String(err.message || err).slice(0, 120) });
              status.textContent = `Failed: ${f.name} — ${err.message || 'timeout'}. Try split or shorter clip.`;
              await new Promise(r => setTimeout(r, 1500));
            } else {
              status.textContent = `Retry ${attempt}/3 for ${f.name}…`;
              await new Promise(r => setTimeout(r, 1500));
            }
          }
        }
      }

      document.getElementById('gate-screen').classList.add('hidden');
      document.getElementById('app-screen').classList.remove('hidden');
      document.getElementById('catalog-block').classList.remove('hidden');
      if (ok === 0) {
        status.textContent = 'No videos saved — try shorter or allow split.';
        showToast('Upload failed — try shorter clip or allow split.');
        return;
      }
      status.textContent = `Saved ${ok} of ${total}. Transcribing…`;
      await refreshCatalogWithPoll();
      if (fail) showToast(`${fail} skipped/failed — try one at a time.`);
      document.getElementById('pick-btn').disabled = false;
      fileInput.value = '';
    }

    async function refreshCatalogWithPoll() {
      let tries = 0;
      while (tries < 20) {
        const [catRes, stRes] = await Promise.all([
          fetch('/api/catalog'),
          fetch('/api/scan/status'),
        ]);
        const rows = await catRes.json();
        const st = await stRes.json();
        renderCatalog(rows);
        const status = document.getElementById('scan-status');
        if (status && !status.classList.contains('hidden')) {
          if (st.processing === 0) {
            status.textContent = `Done: ${st.ready} local ready. Search below.`;
            break;
          }
          status.textContent = `Transcribing: ${st.ready} ready, ${st.processing} still working…`;
        }
        tries++;
        await new Promise(r => setTimeout(r, 3000));
      }
    }

    function bindCatalogClicks(list) {
      list.querySelectorAll('li[data-video]').forEach(li => {
        li.onclick = () => playSegment({
          video: li.dataset.video,
          start: 0,
          display_name: li.querySelector('strong')?.textContent || li.dataset.video,
        });
      });
    }

    function renderCatalog(items) {
      const block = document.getElementById('catalog-block');
      const list = document.getElementById('catalog-list');
      if (!items.length) {
        fetch('/api/catalog').then(r => r.json()).then(rows => {
          if (!rows.length) return;
          catalogRows = rows;
          block.classList.remove('hidden');
          list.innerHTML = rows.map(r => catalogItemHtml(r)).join('');
          bindCatalogClicks(list);
        });
        return;
      }
      catalogRows = items;
      block.classList.remove('hidden');
      list.innerHTML = items.map(r => catalogItemHtml(r)).join('');
      bindCatalogClicks(list);
      prefetchMany(items.filter(r => (r.status || '') === 'ready' || r.transcribed), 'metadata', 6);
    }

    function catalogItemHtml(r) {
      const st = r.status || (r.transcribed ? 'ready' : 'processing');
      const tag = st === 'ready' ? 'ready' : (st === 'error' ? ('error: ' + (r.error || 'failed')) : 'working…');
      const src = r.source === 'cloud' ? ' · cloud' : '';
      const vid = escapeHtml(r.video || '');
      const name = escapeHtml(r.name || r.video);
      return `<li data-video="${vid}" style="cursor:pointer;"><strong>${name}</strong><br><span class="tag">${escapeHtml(tag)}</span>${src} · ${r.segments || 0} segments</li>`;
    }

    function escapeHtml(s) {
      return String(s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
    }

    async function performSearch(reset) {
      const query = document.getElementById('search-input').value.trim();
      if (!query) return;
      if (reset !== false) {
        searchOffset = 0;
        allResults = [];
      }
      searchQuery = query;
      const btn = document.getElementById('search-btn');
      btn.disabled = true;
      btn.textContent = '…';
      try {
        const res = await fetch(
          `/api/search?q=${encodeURIComponent(query)}&offset=${searchOffset}&limit=${SEARCH_PAGE}`
        );
        const data = await res.json();
        const batch = data.results || data;
        searchTotal = data.total != null ? data.total : batch.length;
        if (searchOffset === 0) {
          allResults = batch;
        } else {
          allResults = allResults.concat(batch);
        }
        _d('search', { q: query, n: searchTotal, shown: allResults.length });
        renderResults();
      } catch (err) {
        showToast('Search error: ' + err.message);
      } finally {
        btn.disabled = false;
        btn.textContent = 'Search';
      }
    }

    function loadMoreResults() {
      if (allResults.length >= searchTotal) return;
      searchOffset = allResults.length;
      performSearch(false);
    }

    function toggleCatalog() {
      const block = document.getElementById('catalog-block');
      const btn = document.getElementById('toggle-catalog-btn');
      const open = block.classList.toggle('hidden') === false;
      btn.textContent = open ? 'Hide catalog' : `Browse catalog (${catalogRows.length})`;
    }

    function renderResults() {
      const container = document.getElementById('results-area');
      const summary = document.getElementById('summary-text');
      const loadMore = document.getElementById('load-more-btn');
      container.innerHTML = '';
      if (!allResults.length) {
        summary.textContent = searchQuery ? 'No matches — try another word.' : '';
        if (searchQuery) {
          container.innerHTML = '<p>No matches — try a word you heard in the video.</p>';
        }
        loadMore.classList.add('hidden');
        return;
      }
      summary.textContent = searchTotal > allResults.length
        ? `${searchTotal} matches — showing ${allResults.length}`
        : `${searchTotal} match${searchTotal === 1 ? '' : 'es'}`;
      loadMore.classList.toggle('hidden', allResults.length >= searchTotal);
      allResults.forEach((item, index) => {
        const m = Math.floor(item.start / 60);
        const s = Math.floor(item.start % 60);
        const ts = `${String(m).padStart(2,'0')}:${String(s).padStart(2,'0')}`;
        const quote = item.text || item.better_context || '';
        const card = document.createElement('div');
        card.className = 'card';
        card.innerHTML = `
          <div><strong>#${index+1}</strong> ${item.is_phonetic ? '<span class="tag">phonetic</span>' : ''} ${item.source === 'cloud' ? '<span class="tag">cloud</span>' : ''}</div>
          <p style="margin-top:8px;">"${escapeHtml(quote)}"</p>
          <div class="meta">
            <span class="tag">${escapeHtml(item.display_name || item.video)}</span>
            <span class="tag">@ ${ts}</span>
          </div>
          <div class="btn-row">
            <button class="btn btn-share" onclick="event.stopPropagation(); shareToSocial(${index})">Share</button>
            <button class="btn" onclick="event.stopPropagation(); copyForSocial(${index})">Copy text</button>
            <button class="btn" onclick="event.stopPropagation(); grabClip(${index})">10s clip</button>
          </div>`;
        card.onclick = () => playSegment(item);
        container.appendChild(card);
      });
      prefetchMany(allResults, 'auto', 3);
    }

    async function fetchShareText(item) {
      const res = await fetch(
        `/api/share-text?video=${encodeURIComponent(item.video)}&start=${item.start}` +
        `&quote=${encodeURIComponent(item.text || '')}` +
        `&context=${encodeURIComponent(item.better_context || '')}` +
        (item.drive_id ? `&drive_id=${encodeURIComponent(item.drive_id)}` : '')
      );
      return res.json();
    }

    async function shareToSocial(index) {
      const item = allResults[index];
      if (!item) return;
      const data = await fetchShareText(item);
      try {
        if (navigator.share) {
          await navigator.share({ title: 'Seize the Clip', text: data.text });
          showToast('Shared — pick your app.');
        } else {
          await navigator.clipboard.writeText(data.text);
          showToast('Copied — paste into social media.');
        }
      } catch (e) {
        if (e.name !== 'AbortError') {
          try {
            await navigator.clipboard.writeText(data.text);
            showToast('Copied — paste into social media.');
          } catch (e2) {
            prompt('Copy for social:', data.text);
          }
        }
      }
    }

    async function shareCurrent() {
      if (!currentPlayItem) {
        showToast('Play a clip first.');
        return;
      }
      const data = await fetchShareText(currentPlayItem);
      try {
        if (navigator.share) {
          await navigator.share({ title: 'Seize the Clip', text: data.text });
          showToast('Shared — pick your app.');
        } else {
          await navigator.clipboard.writeText(data.text);
          showToast('Copied — paste into social media.');
        }
      } catch (e) {
        if (e.name !== 'AbortError') {
          try {
            await navigator.clipboard.writeText(data.text);
            showToast('Copied — paste into social media.');
          } catch (e2) {
            prompt('Copy for social:', data.text);
          }
        }
      }
    }

    async function copyForSocial(index) {
      const item = allResults[index];
      const data = await fetchShareText(item);
      try {
        await navigator.clipboard.writeText(data.text);
        showToast('Copied — paste into social media.');
      } catch (e) {
        prompt('Copy for social:', data.text);
      }
    }

    async function grabClip(index) {
      const item = allResults[index];
      if (!item) return;
      showToast('Cutting 10s clip…');
      try {
        const res = await fetch(
          `/api/clip?video=${encodeURIComponent(item.video)}&start=${item.start}`
        );
        const data = await res.json();
        if (data.status !== 'success') throw new Error(data.error || 'clip failed');
        const shareData = await fetchShareText(item);
        if (navigator.share && navigator.canShare) {
          const blob = await (await fetch(data.clip_url)).blob();
          const file = new File([blob], 'seize_the_clip.mp4', { type: 'video/mp4' });
          const payload = { files: [file], title: 'Seize the Clip', text: shareData.text };
          if (navigator.canShare(payload)) {
            await navigator.share(payload);
            showToast('Clip shared.');
            return;
          }
        }
        await navigator.clipboard.writeText(shareData.text);
        showToast('Share text copied. Clip opened.');
        window.open(data.clip_url, '_blank');
      } catch (err) {
        if (err.name !== 'AbortError') showToast('Clip error: ' + err.message);
      }
    }

    async function playSegment(item) {
      currentPlayItem = item;
      const wrap = document.getElementById('player-wrap');
      const player = document.getElementById('main-player');
      const loading = document.getElementById('player-loading');
      const start = Math.max(0, Number(item.start) || 0);
      document.getElementById('player-title').textContent = item.display_name || item.video;
      const url = videoUrl(item.video);
      _d('play_start', { video: item.video, start, mode: 'stream' });

      wrap.classList.remove('hidden');
      loading.classList.remove('hidden');
      loading.textContent = 'Starting…';
      wrap.scrollIntoView({ behavior: 'smooth', block: 'start' });

      const beginPlay = () => {
        loading.classList.add('hidden');
        player.muted = false;
        if (player.volume === 0) player.volume = 1;
        _playState(player, item, 'play_loaded');
        player.play().then(() => {
          _playState(player, item, 'play_playing');
        }).catch((e) => {
          _d('play_fail', { video: item.video, err: String(e).slice(0, 80) });
          showToast('Tap the ▶ play button.');
        });
      };

      // Same file already loaded — seek only (fast segment hops).
      if (player._currentVideo === item.video && player.src && player.readyState >= 1) {
        loading.textContent = 'Seeking…';
        try { player.currentTime = start; } catch (e) {}
        beginPlay();
        return;
      }

      player.pause();
      if (player._blobUrl) {
        URL.revokeObjectURL(player._blobUrl);
        player._blobUrl = null;
      }
      player._currentVideo = item.video;
      player.removeAttribute('src');
      player.load();

      player.onloadedmetadata = null;
      player.oncanplay = null;
      player.onerror = null;

      let started = false;
      const onReady = () => {
        if (started) return;
        started = true;
        if (start > 0) {
          try { player.currentTime = start; } catch (e) {}
        }
        beginPlay();
      };

      player.onloadedmetadata = () => {
        if (start > 0 && player.readyState < 2) return;
        onReady();
      };
      player.oncanplay = () => onReady();
      player.onerror = () => {
        _d('play_error', { video: item.video, url, mode: 'stream' });
        loading.classList.add('hidden');
        showToast('Video decode error — try again.');
      };
      player.addEventListener('playing', () => _playState(player, item, 'play_event_playing'), { once: true });
      player.addEventListener('stalled', () => _playState(player, item, 'play_stalled'));
      player.addEventListener('volumechange', () => _playState(player, item, 'play_volume'));

      player.src = url;
      player.load();
      _d('play_stream', { video: item.video, start });
    }

    function closePlayer() {
      const player = document.getElementById('main-player');
      player.pause();
      if (player._blobUrl) {
        URL.revokeObjectURL(player._blobUrl);
        player._blobUrl = null;
      }
      player.removeAttribute('src');
      player._currentVideo = null;
      currentPlayItem = null;
      document.getElementById('player-loading').classList.add('hidden');
      document.getElementById('player-wrap').classList.add('hidden');
    }

    function openAppWithCatalog(rows) {
      catalogRows = rows;
      document.getElementById('gate-screen').classList.add('hidden');
      document.getElementById('app-screen').classList.remove('hidden');
      document.getElementById('toggle-catalog-btn').textContent = `Browse catalog (${rows.length})`;
      if (rows.length <= 12) {
        document.getElementById('catalog-block').classList.remove('hidden');
        renderCatalog(rows);
      } else {
        document.getElementById('catalog-block').classList.add('hidden');
      }
      if (rows.some(r => (r.status || '') === 'processing')) refreshCatalogWithPoll();
    }

    function handleDeepLink() {
      const params = new URLSearchParams(location.search);
      const playName = params.get('play') || params.get('v');
      if (!playName) return;
      const start = Math.max(0, parseFloat(params.get('t') || '0') || 0);
      const item = {
        video: decodeURIComponent(playName),
        start,
        display_name: decodeURIComponent(playName).split('/').pop(),
      };
      setTimeout(() => playSegment(item), 400);
    }

    // Auto-open when cloud or local catalog exists
    fetch('/api/catalog').then(r => r.json()).then(rows => {
      if (rows.length) {
        openAppWithCatalog(rows);
        handleDeepLink();
      } else {
        document.getElementById('gate-screen').querySelector('p').innerHTML =
          '<strong>No catalog yet.</strong> Pick a local video — we transcribe, then you search &amp; play.';
      }
    }).catch(() => {
      document.getElementById('gate-screen').querySelector('p').innerHTML =
        '<strong>Catalog load failed.</strong> Pick a local video or hard refresh.';
    });
  </script>
</body>
</html>
"""

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False, threaded=True)
