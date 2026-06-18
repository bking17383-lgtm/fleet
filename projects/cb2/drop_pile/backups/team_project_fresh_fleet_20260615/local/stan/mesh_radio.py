#!/usr/bin/env python3
"""MESH RADIO — phone extension over Tailscale. Camera + mic + SSE replies. Drive bus."""
from __future__ import annotations

import base64
import json
import os
import queue
import random
import re
import threading
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from collections import deque

from flask import Flask, Response, jsonify, request

DRIVE = Path(os.environ.get("DRIVE", Path.home() / "GoogleDrive/MyDrive"))
if Path("/mnt/shared/GoogleDrive/MyDrive").is_dir():
    DRIVE = Path("/mnt/shared/GoogleDrive/MyDrive")

EYES_OUT = DRIVE / "eyes/inbox"
PHONE_INBOX = DRIVE / "phone/inbox"
PHONE_DIR = DRIVE / "phone"
FLEET_DEVICE_SAMSUNG = "phone-samsung-wifi"
FLEET_DEVICE_MOTO = "phone-moto-lte"
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
_radio_queue: deque[dict] = deque(maxlen=48)
_queue_lock = threading.Lock()
_captn_busy_until: float = 0.0
_reply_recent: deque[str] = deque(maxlen=10)


def _snippet(text: str, n: int = 36) -> str:
    s = re.sub(r"\s+", " ", (text or "").strip())
    if len(s) <= n:
        return s
    cut = s[: n + 1].rsplit(" ", 1)[0]
    return (cut or s[:n]) + "…"


def _pick(*options: str) -> str:
    opts = [o for o in options if o]
    if not opts:
        return ""
    with _lock:
        recent = set(_reply_recent)
    pool = [o for o in opts if o not in recent] or opts
    choice = random.choice(pool)
    with _lock:
        _reply_recent.append(choice)
    return choice


def _now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat()


def _ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _mark_captn_speaking(text: str) -> None:
    global _captn_busy_until
    words = max(1, len((text or "").split()))
    _captn_busy_until = time.time() + min(48, max(2.5, words * 0.42 + 1.2))


def _captn_busy() -> bool:
    return time.time() < _captn_busy_until


def _is_addressed_to_captn(text: str) -> bool:
    t = (text or "").strip()
    if not t:
        return False
    low = t.lower()
    if t in ("(snap)",) or low.startswith("(count)") or low.startswith("(aim)"):
        return True
    if any(w in low for w in ("captn", "captain", " hey cap", " cap ", "over cap", "roger cap")):
        return True
    if low.startswith(("hey ", "ok cap", "okay cap")):
        return True
    if "?" in t and len(t) > 10:
        return True
    if len(t.split()) >= 4:
        return True
    return False


def _enqueue_prefetch(record: dict) -> int:
    with _queue_lock:
        _radio_queue.append(record)
        return len(_radio_queue)


def _queue_snapshot() -> list[dict]:
    with _queue_lock:
        return [{"id": r.get("id"), "text": (r.get("text") or "")[:80], "addressed": _is_addressed_to_captn(r.get("text", ""))} for r in list(_radio_queue)]


def _cycle_prefetch_queue() -> None:
    if _captn_busy():
        return
    record = None
    with _queue_lock:
        for i, rec in enumerate(_radio_queue):
            if _is_addressed_to_captn(rec.get("text", "")):
                record = _radio_queue[i]
                del _radio_queue[i]
                break
    if not record:
        return
    reply = _plan_followup(record.get("text", ""), record.get("image"), record.get("radio_mode") or "do")
    _post_say(reply)


def _prefetch_loop() -> None:
    while True:
        try:
            _cycle_prefetch_queue()
        except Exception as exc:
            _dev_log("prefetch_err", str(exc))
        time.sleep(1.4)


def _fleet_stats() -> dict:
    path = DRIVE / "fleet/FLEET_AVAILABLE.txt"
    text = path.read_text(encoding="utf-8") if path.is_file() else ""
    compact = ""
    working = partial = down = total = 0
    for line in text.splitlines():
        if line.startswith("Compact:"):
            compact = line.split("Compact:", 1)[1].strip()
            m = re.search(r"(\d+)\s+up.*?(\d+)\s+partial.*?(\d+)\s+down", compact)
            if m:
                working, partial, down = int(m.group(1)), int(m.group(2)), int(m.group(3))
                total = working + partial + down
    if not compact:
        compact = "fleet board stale — say DESK on CB2"
    nodes = working + partial + down
    total = max(nodes, 6) if nodes else 6
    return {
        "compact": compact,
        "up": working,
        "partial": partial,
        "down": down,
        "total": total,
        "ratio": f"{working}/{total}",
        "can_delegate": working >= 3,
    }


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


def _append_brian_inbox(line: str) -> None:
    path = DRIVE / "fleet/bus/BRIAN_INBOX.txt"
    if not path.is_file():
        return
    try:
        text = path.read_text(encoding="utf-8")
        marker = "--- TYPE BELOW (one line) ---"
        if marker in text:
            head, tail = text.split(marker, 1)
            path.write_text(head + marker + "\n" + line.strip() + "\n" + tail.lstrip("\n"), encoding="utf-8")
        else:
            path.write_text(text.rstrip() + "\n" + line.strip() + "\n", encoding="utf-8")
    except OSError:
        pass


def _write_emergency(record: dict) -> None:
    record = {**record, "emergency": True}
    path = PHONE_INBOX / f"emergency_{record['id']}.json"
    path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    dev = record.get("device_id") or "phone"
    line = f"EMERGENCY [{dev}]: {record.get('text', '')}"
    _append_brian_inbox(line)
    mac = DRIVE / "fleet/bus/mac_inbox.txt"
    try:
        with mac.open("a", encoding="utf-8") as f:
            f.write(f"\n--- from: phone | emergency | {_now()} ---\n{line}\n")
    except OSError:
        pass
    _dev_log("EMERGENCY", record.get("text", "")[:120])


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


def _plan_followup(user_text: str, image_name: str | None, radio_mode: str = "do") -> str:
    """After the wait line — speak a real CAPTN answer (no slow APIs)."""
    t = (user_text or "").strip()
    low = t.lower()
    mode = (radio_mode or "do").lower()
    if mode == "spark":
        if any(w in low for w in ("personality", "inspired", "idea", "creative", "spark")):
            return (
                "SPARK mode — good. You're the creative; I amplify. "
                "Pick one thread: camel game, story mine, or phone radio — what's lighting up?"
            )
        if len(t) > 40:
            return _pick(
                "SPARK — what's the bold move?",
                "Creative lane open. Smallest next leap?",
                "Got it. Where does this go?",
            )
    if mode == "do" or mode == "brx":
        if any(w in low for w in ("personality", "get things done", "admin", "decide")):
            return (
                "DO mode — one next step. Tap DO or SPARK anytime; context stays. "
                "Right now: tell me the single task and I'll carry it — no fleet admin."
            )
    if any(w in low for w in ("sync", "synchronized", "going on", "background process", "hear good", "hear from")):
        st = _fleet_stats()
        r = st["ratio"]
        return _pick(
            f"Synced — mesh up, fleet {r}. Green box is me; you'll hear it spoken.",
            f"Channel good — CB2 CAPTN, fleet {r}. HOLD to talk, release to send.",
            f"We're live, fleet {r}. Reply shows in green; voice follows.",
        )
    if any(w in low for w in ("screen capture", "screen read", "screenshot")):
        return "Screen read — point at the screen and tap SNAP, or paste text below. I'll read what lands."
    if any(w in low for w in ("clear", "typed", "text box", "did not clear")):
        return "Fixed — text box clears after send now. Type again anytime."
    if any(w in low for w in ("camera", "cam on", "default")):
        return "Camera off by default now — tap CAM only when you need SNAP or COUNT."
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
    if any(w in low for w in ("respond", "didn't respond", "15 second", "waiting")):
        return _pick(
            "I'm here now — go ahead.",
            "Back on channel. Talk to me.",
            "Copy — what did you need?",
        )
    if "microphone" in low or "driver mic" in low or "red button" in low:
        return "Tap DRIVE MIC once for open mic. If it drops, use HOLD — press, talk, release."
    return _local_reply(user_text, bool(image_name and (EYES_OUT / image_name).is_file()), radio_mode)


def _local_reply(user_text: str, has_image: bool, radio_mode: str = "do") -> str:
    t = (user_text or "").strip()
    low = t.lower()
    if any(
        p in low
        for p in ("hear me", "can you hear", "you hear me", "radio check", "mic check", "didn't respond")
    ):
        return _pick(
            "Loud and clear — go ahead.",
            "Copy. I'm on — what's up?",
            "Roger — CAPTN here.",
            "Heard you. Keep talking.",
        )
    if low in ("test", "testing", "hello", "hey") or low.startswith(("hey cap", "ok cap", "hello cap")):
        return _pick(
            "Hey Brian — channel's open.",
            "Here. What do you need?",
            "Copy. Go ahead.",
            "On the line — shoot.",
        )
    if t == "(snap)" or (has_image and len(t) < 12):
        return _pick(
            "Picture in — reading it now.",
            "Snap received. Watch the green reply.",
            "Got the frame — one sec.",
        )
    if t.lower().startswith("(aim)"):
        return _pick(
            "Aim noted — tap SNAP when ready.",
            "Got the aim hint. SNAP when set.",
        )
    if any(w in low for w in ("picture", "timestamp", "attach", "eyes", "snap")):
        return _pick(
            "Picture on Drive — tell me what to check.",
            "Eyes on it. One sentence on what you want.",
        )
    if any(w in low for w in ("rover", "cellular", "moto", "unique", "identifier")):
        return _pick(
            "Moto LTE is ROVER. Samsung WiFi is TESTER.",
            "ROVER = Moto cellular. TESTER = Samsung WiFi.",
        )
    if "?" in t:
        if any(w in low for w in ("car", "truck", "vehicle", "engine", "tire")):
            return _pick("What's up with the car?", "Car — what do you need?", "Talk me through the vehicle issue.")
        return _pick(
            "Say that once more, short.",
            "One sentence — I'm with you.",
            "Run that by me again, tighter.",
        )
    if len(t) > 15:
        if (radio_mode or "do") == "spark":
            return _pick(
                "SPARK — what's the bold move?",
                "Creative lane — smallest next leap?",
                "Got it. Where does this go?",
            )
        return _pick(
            "Copy. What's the one next step?",
            "On it — what do you need?",
            "Roger. Keep going.",
            "Got it. Single task?",
        )
    return _pick("Copy.", "Go on.", "I'm here.", "Say more.", "Roger.")


def _auto_reply(user_text: str, image_name: str | None, radio_mode: str = "do") -> str:
    has_image = bool(image_name and (EYES_OUT / image_name).is_file())
    return _plan_followup(user_text, image_name, radio_mode)


def _schedule_say(record: dict, delay_sec: float = 2.0) -> None:
    """Every message gets a spoken reply — pending file is for Drive audit."""

    def _job() -> None:
        time.sleep(max(0.4, min(delay_sec, 4.0)))
        while _captn_busy():
            time.sleep(0.5)
        reply = _plan_followup(
            record.get("text", ""),
            record.get("image"),
            record.get("radio_mode") or "do",
        )
        _post_say(reply)

    threading.Thread(target=_job, daemon=True).start()


def _post_say(text: str) -> None:
    global _say_mtime
    SAY_FILE.write_text(text + "\n", encoding="utf-8")
    _say_mtime = SAY_FILE.stat().st_mtime
    _mark_captn_speaking(text)
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
threading.Thread(target=_prefetch_loop, daemon=True).start()


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
  html, body { height: 100%; margin: 0; }
  body.terminal { font-family: ui-monospace, "Cascadia Mono", "SF Mono", Menlo, Consolas, monospace;
         background: #0a0a0a; color: #ddd; display: flex; flex-direction: column;
         max-width: none; padding: 0; overflow: hidden; }
  .term-bar { flex: 0 0 auto; display: flex; justify-content: space-between; align-items: center;
              padding: 0.45rem 0.65rem; background: #121212; border-bottom: 1px solid #333;
              font-size: 0.88rem; }
  .term-bar strong { color: #e74; font-weight: 700; letter-spacing: 0.04em; }
  #status { color: #888; font-size: 0.82rem; text-align: right; max-width: 62%; }
  #transcript { flex: 1 1 auto; min-height: 0; overflow-y: auto; -webkit-overflow-scrolling: touch;
                margin: 0; padding: 0.75rem 0.65rem; font-size: 1.05rem; line-height: 1.55;
                background: #080808; white-space: pre-wrap; word-break: break-word; }
  .term-wait { flex: 0 0 auto; display: none; padding: 0.35rem 0.65rem; background: #2a2410;
                color: #dd8; font-size: 0.9rem; border-top: 1px solid #443; }
  .term-wait.on { display: block; }
  video { display: none; width: 0; height: 0; }
  video.on { display: block; width: 100%; max-height: 24vh; flex: 0 0 auto; object-fit: contain;
             background: #000; border-top: 1px solid #333; }
  .toolbar { flex: 0 0 auto; display: flex; flex-wrap: wrap; gap: 0.35rem; padding: 0.4rem 0.5rem;
             background: #101010; border-top: 1px solid #333; }
  .toolbar button { font-family: inherit; font-size: 0.95rem; padding: 0.55rem 0.65rem; border: none;
                    border-radius: 6px; cursor: pointer; font-weight: 600; flex: 1; min-width: 4.2rem; }
  #drive { background: #27ae60; color: #fff; flex: 2; min-width: 7rem; }
  #drive.off { background: #444; color: #ccc; }
  #cam { background: #555; color: #ccc; }
  #cam.on { background: #2980b9; color: #fff; }
  #snap { background: #3498db; color: #fff; }
  #count { background: #e67e22; color: #fff; }
  #speak { background: #555; color: #ccc; flex: 0; min-width: 2.5rem; }
  #modeDo,#modeSpark { background: #333; color: #ccc; }
  #modeDo.on { background: #1a6b3a; color: #fff; }
  #modeSpark.on { background: #a65d1a; color: #fff; }
  .typerow { flex: 0 0 auto; display: flex; gap: 0.4rem; align-items: stretch; padding: 0.45rem 0.5rem 0.65rem;
             background: #0a0a0a; border-top: 1px solid #333; }
  .typerow textarea { flex: 1; min-width: 0; min-height: 4.5rem; max-height: 30vh; resize: vertical;
                      font-family: inherit; font-size: 1.05rem; line-height: 1.45; padding: 0.55rem 0.6rem;
                      border-radius: 6px; border: 1px solid #333; background: #111; color: #eee; }
  #send { background: #2ecc71; color: #000; font-size: 1.25rem; padding: 0 0.85rem; border: none;
          border-radius: 6px; cursor: pointer; font-weight: 700; flex: 0 0 auto; font-family: inherit; }
  #heard, #reply { display: none !important; }
  .dev { display: none !important; }
</style></head><body class="terminal">
<header class="term-bar"><strong id="term-title">RADIO</strong><span id="status">Connecting…</span></header>
<main id="transcript" aria-live="polite"></main>
<div id="wait" class="term-wait">Waiting for CAPTN…</div>
<video id="v" autoplay playsinline muted></video>
<div class="toolbar row">
  <button id="drive">MIC ON</button>
  <button id="cam">CAM</button>
  <button id="snap">SNAP</button>
  <button id="count">CNT</button>
  <button id="speak" title="Hear again">↻</button>
</div>
<form id="typeform" class="typerow">
  <textarea id="typed" rows="3" enterkeyhint="send" autocomplete="off" placeholder="Type message… Shift+Enter new line"></textarea>
  <button id="send" type="submit" title="Send">↵</button>
</form>
<div id="heard"></div><div id="reply"></div>
<div class="dev"><h3>Developer log</h3><pre id="devlog">(waiting…)</pre></div>
<canvas id="c" hidden></canvas>
<script>
const heard = document.getElementById('heard');
const reply = document.getElementById('reply');
const wait = document.getElementById('wait');
const status = document.getElementById('status');
const transcript = document.getElementById('transcript');
const devlog = document.getElementById('devlog');
let stream=null, lastReply='', lastSpoken='', lastSayTs=0, recognition=null;
let listening=false, driveMode=false, sending=false;
const FLEET_DEVICE='phone-samsung-wifi';
const LOG_KEY='captn_radio_'+FLEET_DEVICE;

function loadTranscript(){
  try{
    const saved=localStorage.getItem(LOG_KEY);
    if(saved) transcript.textContent=saved;
  }catch(e){}
}
function saveTranscript(){
  try{
    let t=transcript.textContent||'';
    if(t.length>48000) t=t.slice(-48000);
    localStorage.setItem(LOG_KEY, t);
  }catch(e){}
}
function termLine(tag, text){
  const ts=new Date().toLocaleTimeString([], {hour:'2-digit',minute:'2-digit'});
  transcript.textContent=(transcript.textContent||'')+'['+ts+'] '+tag+': '+text+'\\n';
  transcript.scrollTop=transcript.scrollHeight;
  saveTranscript();
}

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
  if(text===lastReply && (!speak || text===lastSpoken)) return;
  lastReply=text;
  termLine('CAPTN', text);
  reply.textContent='CAPTN: '+text;
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
      showReply(j.text, true);
    }else if(!lastReply){
      showReply(j.text, true);
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
  const v=document.getElementById('v');
  const btn=document.getElementById('cam');
  if(stream){
    stream.getTracks().forEach(t=>t.stop());
    stream=null;
    v.srcObject=null;
    v.classList.remove('on');
    if(btn){ btn.classList.remove('on'); btn.textContent='CAM'; }
    status.textContent='Camera off';
    return;
  }
  const tries=[
    {video:{facingMode:{ideal:'environment'}}},
    {video:{facingMode:'user'}},
    {video:true},
  ];
  for(let i=0;i<tries.length;i++){
    try{
      stream=await navigator.mediaDevices.getUserMedia({...tries[i],audio:false});
      v.srcObject=stream;
      v.classList.add('on');
      if(btn){ btn.classList.add('on'); btn.textContent='CAM ON'; }
      status.textContent='Camera on — SNAP or COUNT';
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
  heard.textContent='';
  termLine('BRX', text);
  status.textContent='Sending…';
  const body={text, device_id: FLEET_DEVICE};
  if(withFrame){
    const f=frameB64();
    if(!f){
      status.textContent='Tap CAM first, then SNAP';
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
    document.getElementById('typed').value='';
    status.textContent=j.ok?(j.ack||'Sent'):('Error: '+(j.error||'?'));
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

document.getElementById('typeform').addEventListener('submit',(e)=>{
  e.preventDefault();
  sendMsg(document.getElementById('typed').value);
});
document.getElementById('typed').addEventListener('keydown',(e)=>{
  if(e.key==='Enter'&&!e.shiftKey){ e.preventDefault(); sendMsg(document.getElementById('typed').value); }
});
document.getElementById('snap').onclick=()=>sendMsg('(snap)', true);
document.getElementById('count').onclick=()=>countWithSteady();
document.getElementById('speak').onclick=()=>sayAloud(lastReply);

const SR=window.SpeechRecognition||window.webkitSpeechRecognition;
const HALF_DUPLEX=(FLEET_DEVICE||'').includes('moto');

function setPttUi(on){
  const b=document.getElementById('drive');
  if(on){ b.classList.remove('off'); b.textContent='… TALKING'; status.textContent='Speak now'; if(typeof setMode==='function') setMode('brx'); }
  else { b.classList.add('off'); b.textContent=HALF_DUPLEX?'HOLD TO TALK':'MIC OFF'; status.textContent=HALF_DUPLEX?'Release to send · one direction':'Mic off — tap MIC ON or type below'; }
}
let pttText='', pttActive=false;
function pttStart(){
  if((typeof captnOnAir!=='undefined'&&captnOnAir)||!SR||pttActive) return;
  pttActive=true; pttText=''; setPttUi(true);
  try{ recognition.start(); listening=true; }catch(e){ devLog('ptt', String(e)); }
}
function pttStop(){
  if(!pttActive) return;
  pttActive=false; listening=false;
  try{ recognition.stop(); }catch(e){}
  setPttUi(false);
  const t=(pttText||'').trim(); pttText='';
  if(!t||isMicNoise(t)) return;
  if(typeof captnOnAir!=='undefined'&&captnOnAir){
    if(typeof prefetchLocal!=='undefined'){ prefetchLocal.push(t); if(typeof setMode==='function') setMode('pre'); }
    return;
  }
  sendMsg(t,false);
}

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
  recognition.lang='en-US';
  if(HALF_DUPLEX){
    recognition.continuous=false;
    recognition.interimResults=false;
    recognition.onresult=(e)=>{
      let t='';
      for(let i=e.resultIndex;i<e.results.length;i++) t+=e.results[i][0].transcript;
      pttText=t;
    };
    recognition.onend=()=>{ listening=false; if(pttActive) setTimeout(pttStop, 120); };
    const btn=document.getElementById('drive');
    btn.onmousedown=btn.ontouchstart=(e)=>{ e.preventDefault(); pttStart(); };
    btn.onmouseup=btn.onmouseleave=btn.ontouchend=(e)=>{ e.preventDefault(); pttStop(); };
  }else{
    recognition.continuous=true;
    recognition.interimResults=true;
    recognition.onresult=(e)=>{
      let t='';
      for(let i=e.resultIndex;i<e.results.length;i++) t+=e.results[i][0].transcript;
      document.getElementById('typed').value=t;
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
  }
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

document.getElementById('cam').onclick=startCam;
loadTranscript();
if(!transcript.textContent) termLine('SYS', 'CAPTN radio — context kept below');
status.textContent='Radio ready — tap MIC ON or HOLD to talk';
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
    PHONE_PAGE.replace("const FLEET_DEVICE='phone-samsung-wifi'", "const FLEET_DEVICE='phone-moto-lte'")
    .replace("<title>MESH RADIO</title>", "<title>CAPTN — Radio</title>")
    .replace('<strong id="term-title">RADIO</strong>', '<strong id="term-title">CAPTN</strong>')
    .replace(
        '<button id="drive">MIC ON</button>',
        '<button id="modeDo" type="button">DO</button>'
        '<button id="modeSpark" type="button">SPARK</button>'
        '<button id="drive">HOLD TO TALK</button>',
    )
    .replace(
        "let listening=false, driveMode=false, sending=false;",
        "let listening=false, driveMode=false, sending=false, captnOnAir=false, prefetchLocal=[],"
        "radioMode=localStorage.getItem('captn_radio_mode')||'do';",
    )
    .replace(
        "const body={text, device_id: FLEET_DEVICE};",
        "const body={text, device_id: FLEET_DEVICE, half_duplex: HALF_DUPLEX, radio_mode: radioMode};",
    )
    .replace(
        "function sayAloud(t){\\n  if(!t||!window.speechSynthesis) return;\\n  speechSynthesis.cancel();\\n  const u=new SpeechSynthesisUtterance(t);\\n  u.rate=0.95; speechSynthesis.speak(u);\\n}",
        "function setMode(m){\\n  const s=document.getElementById('status'); if(!s) return;\\n  if(m==='cap') s.textContent='CAPTN speaking…';\\n  else if(m==='pre') s.textContent='Queued…';\\n  else s.textContent='Ready — HOLD to talk';\\n}\\n"
        "function sayAloud(t){\\n  if(!t||!window.speechSynthesis) return;\\n  captnOnAir=true; setMode('cap');\\n  if(listening){ try{recognition.stop();}catch(e){} listening=false; }\\n  speechSynthesis.cancel();\\n  const u=new SpeechSynthesisUtterance(t);\\n  u.rate=0.92;\\n  u.onend=()=>{ captnOnAir=false; setMode('brx'); flushPrefetchLocal(); };\\n  speechSynthesis.speak(u);\\n}\\n"
        "function flushPrefetchLocal(){\\n  while(prefetchLocal.length){\\n    const t=prefetchLocal.shift();\\n    if(t) sendMsg(t,false);\\n  }\\n}\\n"
        "function setRadioMode(m){\\n  radioMode=m; localStorage.setItem('captn_radio_mode', m);\\n  const d=document.getElementById('modeDo'), s=document.getElementById('modeSpark');\\n  if(d) d.classList.toggle('on', m==='do'); if(s) s.classList.toggle('on', m==='spark');\\n}\\n",
    )
    .replace(
        "    if(j.planning){\\n      wait.classList.add('on');\\n      wait.textContent='Waiting for CAPTN…';\\n      reply.textContent='';\\n      setTimeout(pollSay, 500);\\n    }else if(j.say){ showReply(j.say, true); }\\n    else if(j.ok){ wait.classList.add('on'); reply.textContent=''; setTimeout(pollSay, 500); }",
        "    if(j.planning){\\n      wait.classList.add('on');\\n      wait.textContent=j.ack||'CAPTN answering…';\\n      setTimeout(pollSay, 400);\\n    }else if(j.say){ showReply(j.say, true); }\\n    else if(j.queued){ wait.classList.add('on'); wait.textContent=j.ack||'Prefetch…'; setMode('pre'); setTimeout(pollSay, 800); }\\n    else if(j.ok){ wait.classList.add('on'); setTimeout(pollSay, 500); }",
    )
    .replace(
        "document.getElementById('cam').onclick=startCam;\\nloadTranscript();\\nif(!transcript.textContent) termLine('SYS', 'CAPTN radio — context kept below');\\nstatus.textContent='Radio ready — tap MIC ON or HOLD to talk';\\ndevLog('boot', location.href);\\npollSay();\\nsetInterval(pollSay, 2000);",
        "document.getElementById('cam').onclick=startCam;\\n"
        "document.getElementById('modeDo').onclick=()=>setRadioMode('do');\\n"
        "document.getElementById('modeSpark').onclick=()=>setRadioMode('spark');\\n"
        "setRadioMode(radioMode);\\n"
        "loadTranscript();\\n"
        "if(!transcript.textContent) termLine('SYS', 'CAPTN — HOLD to talk · context kept below');\\n"
        "status.textContent='Ready — HOLD to talk';\\n"
        "devLog('boot', location.href);\\npollSay();\\n"
        "setInterval(pollSay, 1500);",
    )
    .replace('<div class="dev">', '<div class="dev" style="display:none">')
    .replace("const wasDrive=driveMode;", "const wasDrive=false;")
    .replace("if(wasDrive) startDriveMic();", "")
)

CAPTN_HOME_PAGE = """<!DOCTYPE html>
<html><head>
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-title" content="CAPTN">
<title>CAPTN</title>
<style>
  body{font-family:system-ui;margin:0;padding:1.25rem;background:#0a0a0f;color:#eee;
       max-width:480px;margin-inline:auto;text-align:center}
  img.face{width:120px;height:120px;border-radius:50%;border:4px solid #c0392b;object-fit:cover}
  h1{margin:0.5rem 0 0.2rem;font-size:2rem}
  .tag{color:#888;margin-bottom:1.5rem}
  a.btn{display:block;padding:1.25rem 1rem;margin:0.75rem 0;border-radius:14px;
        font-size:1.35rem;font-weight:700;text-decoration:none;color:#fff}
  .normal{background:#1a5276}
  .emerg{background:#922b21;border:2px solid #e74c3c}
  .hint{color:#666;font-size:0.9rem;margin-top:1.5rem;line-height:1.4}
</style></head><body>
<img class="face" src="/api/captn_face" alt="CAPTN">
<h1>CAPTN</h1>
<p class="tag">Brian's phone lane · not Gemini · not SMS</p>
<a class="btn normal" href="/radio">📻 Normal Radio<br><span style="font-size:0.85rem;font-weight:400">talk · snap · everyday</span></a>
<a class="btn emerg" href="/emergency">🆘 Emergency<br><span style="font-size:0.85rem;font-weight:400">outage · sick · help now</span></a>
<p class="hint">Add to Home Screen → name <b>CAPTN</b><br>Keep CB2 awake · mesh :8765</p>
</body></html>"""

EMERGENCY_PAGE = """<!DOCTYPE html>
<html><head>
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="apple-mobile-web-app-capable" content="yes">
<title>CAPTN — Emergency</title>
<style>
  body{font-family:system-ui;margin:0;padding:1rem;background:#1a0808;color:#fee;max-width:480px;margin-inline:auto}
  h1{color:#e74c3c;margin:0 0 0.25rem;font-size:1.6rem}
  .sub{color:#c99;margin-bottom:1rem;font-size:0.95rem}
  button{width:100%;font-size:1.2rem;padding:1rem;margin:0.45rem 0;border:none;border-radius:12px;
          font-weight:700;cursor:pointer;background:#922b21;color:#fff;border:2px solid #e74c3c}
  #status{min-height:1.5rem;color:#faa;margin:0.75rem 0}
  #reply{background:#2a1010;padding:0.85rem;border-radius:10px;color:#afa;font-size:1.15rem;font-weight:600}
  a.back{display:block;text-align:center;margin-top:1rem;color:#8cf}
  video{width:100%;max-height:28vh;background:#000;border-radius:8px;margin:0.5rem 0}
</style></head><body>
<h1>🆘 CAPTN Emergency</h1>
<p class="sub">One tap logs to fleet + BRIAN_INBOX · not 911</p>
<video id="v" autoplay playsinline muted></video>
<button data-msg="OUTAGE — power or network down">🔌 OUTAGE</button>
<button data-msg="SICK / AFK — master down">🤒 SICK · AFK</button>
<button data-msg="HELP NOW — need CAPTN">🆘 HELP NOW</button>
<button data-msg="PUPPY DOWN — need mesh or host">🐕 PUPPY DOWN</button>
<button data-msg="CAN'T GET HOME — stranded">🏠 CAN'T GET HOME</button>
<button id="snap" style="background:#641e16">📷 SNAP + HELP</button>
<p id="status"></p>
<div id="reply"></div>
<a class="back" href="/rover">← Normal radio</a>
<canvas id="c" hidden></canvas>
<script>
const FLEET_DEVICE='phone-moto-lte';
const status=document.getElementById('status');
const reply=document.getElementById('reply');
let stream=null;
async function startCam(){
  try{
    stream=await navigator.mediaDevices.getUserMedia({video:{facingMode:{ideal:'environment'}},audio:false});
    document.getElementById('v').srcObject=stream;
  }catch(e){ status.textContent='Camera optional — tap a button'; }
}
function frameB64(){
  const v=document.getElementById('v'), c=document.getElementById('c');
  if(!v.videoWidth) return null;
  c.width=v.videoWidth; c.height=v.videoHeight;
  c.getContext('2d').drawImage(v,0,0);
  return c.toDataURL('image/jpeg',0.82);
}
async function sendEmerg(text, withFrame){
  status.textContent='Sending emergency…';
  const body={text, device_id:FLEET_DEVICE, emergency:true};
  if(withFrame){ const f=frameB64(); if(f) body.image=f; }
  const r=await fetch('/api/said',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify(body)});
  const j=await r.json();
  status.textContent='Logged.';
  reply.textContent=j.say||j.ack||'CAPTN has it.';
  if(window.speechSynthesis&&j.say){
    const u=new SpeechSynthesisUtterance(j.say); speechSynthesis.speak(u);
  }
}
document.querySelectorAll('button[data-msg]').forEach(b=>{
  b.onclick=()=>sendEmerg(b.dataset.msg, false);
});
document.getElementById('snap').onclick=()=>sendEmerg('HELP NOW — see snap', true);
startCam();
</script></body></html>"""


@app.route("/")
def home():
    return PHONE_PAGE


@app.route("/rover")
def rover_home():
    return CAPTN_HOME_PAGE


@app.route("/radio")
@app.route("/rover/radio")
def radio():
    return ROVER_PAGE


@app.route("/emergency")
@app.route("/rover/emergency")
def emergency():
    return EMERGENCY_PAGE


@app.route("/api/captn_face")
def captn_face():
    from flask import send_file

    face = DRIVE / "fleet/captn/CAPTN_FACE.jpg"
    if face.is_file():
        return send_file(face, mimetype="image/jpeg", max_age=3600)
    return ("", 404)


@app.route("/health")
def health():
    return jsonify({"ok": True, "service": "mesh_radio"})


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
        "device_id": (data.get("device_id") or "").strip() or None,
        "emergency": bool(data.get("emergency")),
        "radio_mode": (data.get("radio_mode") or "do").strip().lower()[:12],
    }
    path = PHONE_INBOX / f"said_{record['id']}.json"
    path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    _write_pending(record)

    if record["emergency"]:
        _write_emergency(record)
        reply = "Emergency logged. CAPTN sees it on Drive — hold tight."
        _post_say(reply)
        return jsonify(
            {
                "ok": True,
                "id": record["id"],
                "image": image_name,
                "ack": "Emergency logged.",
                "say": reply,
                "emergency": True,
            }
        )

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

    # Snaps queue for CAPTN vision — still speak back quickly
    if image_name and (text == "(snap)" or text.startswith("(aim)") or len(text) < 20):
        _schedule_say(record, 2.0)
        resp = {
            "ok": True,
            "id": record["id"],
            "image": image_name,
            "ack": "Snap received — CAPTN reading.",
            "planning": 3,
        }
        _dev_log("said", {"id": record["id"], "eyes_queue": text[:40]})
        return jsonify(resp)

    if _needs_think(text):
        secs = _plan_seconds(text)
        _schedule_say(record, min(secs, 3))
        _dev_log("plan_queue", {"secs": secs, "text": text[:80], "id": record["id"]})
        resp = {
            "ok": True,
            "id": record["id"],
            "image": image_name,
            "ack": _pick("On it.", "One sec.", "Reading you.", "Got it — answering."),
            "planning": min(secs, 4),
        }
        _dev_log("said", {"id": record["id"], "plan_queue": secs})
        return jsonify(resp)

    half = bool(data.get("half_duplex")) or (record.get("device_id") or "").startswith("phone-moto")
    if half:
        addressed = _is_addressed_to_captn(text)
        qlen = _enqueue_prefetch(record)
        if addressed and not _captn_busy():
            threading.Thread(target=_cycle_prefetch_queue, daemon=True).start()
        if not addressed:
            ack = _pick(
                "Channel open — say CAPTN when you want a reply.",
                "Copy. Listening — ping CAPTN for an answer.",
                "Heard. Open line — call me when you need words back.",
            )
        elif _captn_busy():
            ack = _pick(
                f"CAPTN talking — {qlen} queued.",
                f"Hold — I'm speaking ({qlen} in prefetch).",
                f"On air — your line is queued ({qlen}).",
            )
        else:
            ack = _pick(
                f"Cycling prefetch ({qlen}).",
                f"Got it — queue {qlen}.",
                f"In queue ({qlen}) — answering addressed first.",
            )
        resp = {
            "ok": True,
            "id": record["id"],
            "image": image_name,
            "queued": True,
            "prefetch": True,
            "addressed": addressed,
            "queue_len": qlen,
            "captn_busy": _captn_busy(),
            "ack": ack,
        }
        _dev_log("said", {"id": record["id"], "prefetch": qlen, "addressed": addressed})
        return jsonify(resp)

    reply = _auto_reply(text, image_name, record.get("radio_mode") or "do")
    _post_say(reply)
    resp = {"ok": True, "id": record["id"], "image": image_name, "ack": "Sent.", "say": reply}
    _dev_log("said", {"id": record["id"], "text": text[:80], "say": reply[:80]})
    return jsonify(resp)


@app.route("/api/fleet")
def api_fleet():
    st = _fleet_stats()
    st["ok"] = True
    st["updated"] = _now()
    return jsonify(st)


@app.route("/api/radio_state")
def api_radio_state():
    return jsonify(
        {
            "ok": True,
            "captn_busy": _captn_busy(),
            "captn_busy_until": _captn_busy_until,
            "queue_len": len(_radio_queue),
            "queue": _queue_snapshot(),
            "mode": "half_duplex_prefetch",
        }
    )


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
