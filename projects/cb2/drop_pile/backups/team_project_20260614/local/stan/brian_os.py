#!/usr/bin/env python3
"""
Brian OS — central queue + plain-English status for multi-machine workflow.
Brian talks normal; Lester queues; Cursors execute by capability.
"""

from __future__ import annotations

import json
import os
import platform
import re
import threading
import time
import urllib.request
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

STAN_DIR = Path.home() / ".stan"
DRIVE_ROOT = Path("/mnt/shared/GoogleDrive/MyDrive")
FLEET_BUS = DRIVE_ROOT / "fleet" / "bus"
STATUS_FILE = FLEET_BUS / "BRIAN_STATUS.txt"
QUEUE_FILE = FLEET_BUS / "brian_queue.json"
PHONE_FILE = DRIVE_ROOT / "fleet" / "BRIAN_PHONE.txt"
BASEBALL_WS = Path.home() / "Applications/cursor/baseball_cards"

HOSTNAME = platform.node().lower()

CAPABILITIES: dict[str, dict[str, bool]] = {
    "penguin": {
        "can_build": True,
        "can_import_collx": True,
        "can_serve_phone_wifi": False,
        "can_read_drive": True,
        "role": "captain",
    },
    "puppy": {
        "can_build": True,
        "can_import_collx": True,
        "can_serve_phone_wifi": True,
        "can_read_drive": True,
        "role": "phone_server",
    },
}

DEFAULT_CAPS = {
    "can_build": True,
    "can_import_collx": True,
    "can_serve_phone_wifi": False,
    "can_read_drive": True,
    "role": "worker",
}

INTENT_ROUTING: dict[str, str] = {
    "import_collx": "penguin",
    "refresh_status": "any",
    "serve_phone": "puppy",
    "build": "penguin",
    "execute_brief": "penguin",
    "fix_thumbnails": "penguin",
    "scan_drive": "penguin",
}

_watcher_started = False
_lock = threading.Lock()


def _now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat()


def _caps() -> dict[str, Any]:
    c = dict(DEFAULT_CAPS)
    c.update(CAPABILITIES.get(HOSTNAME, {}))
    c["hostname"] = HOSTNAME
    return c


def _read_json(path: Path, default: Any) -> Any:
    if not path.is_file():
        return default
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return default


def _write_json(path: Path, data: Any) -> bool:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        return True
    except OSError:
        return False


def _write_text(path: Path, text: str) -> bool:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return True
    except OSError:
        return False


def load_queue() -> dict[str, Any]:
    data = _read_json(QUEUE_FILE, {"jobs": [], "updated_at": None})
    if not isinstance(data.get("jobs"), list):
        data["jobs"] = []
    return data


def save_queue(data: dict[str, Any]) -> None:
    data["updated_at"] = _now()
    _write_json(QUEUE_FILE, data)


def queue_job(
    intent: str,
    said: str = "",
    assign_to: str = "auto",
    params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Lester or Brian intent → queue. Returns job record."""
    intent = (intent or "general").strip().lower().replace(" ", "_")
    if assign_to == "auto":
        assign_to = INTENT_ROUTING.get(intent, "penguin")
    job = {
        "id": str(uuid.uuid4())[:10],
        "intent": intent,
        "said": (said or "").strip()[:500],
        "assign_to": assign_to,
        "params": params or {},
        "status": "pending",
        "created_at": _now(),
        "completed_at": None,
        "result": None,
        "error": None,
        "hostname_done": None,
    }
    with _lock:
        q = load_queue()
        q["jobs"].insert(0, job)
        q["jobs"] = q["jobs"][:50]
        save_queue(q)
    refresh_brian_status(waiting_note=f"Queued: {intent}")
    return job


def _can_run_job(job: dict[str, Any]) -> bool:
    caps = _caps()
    assign = job.get("assign_to", "any")
    intent = job.get("intent", "")
    if assign == "any":
        return True
    if assign == "penguin" and HOSTNAME != "penguin":
        return False
    if assign == "puppy" and HOSTNAME not in ("puppy", "puppy64"):
        return False
    if intent == "serve_phone" and not caps.get("can_serve_phone_wifi"):
        return False
    if intent in ("import_collx", "fix_thumbnails", "scan_drive") and not caps.get("can_import_collx"):
        return False
    if intent in ("build", "execute_brief") and not caps.get("can_build"):
        return False
    return True


def _execute_job(job: dict[str, Any]) -> dict[str, Any]:
    intent = job.get("intent", "")
    caps = _caps()

    if intent == "serve_phone" and not caps.get("can_serve_phone_wifi"):
        return {
            "status": "failed",
            "error": "Phone Wi-Fi serving must run on puppy64, not Chromebook Linux.",
            "next": "On puppy: bash ~/GoogleDrive/MyDrive/lester/START_BASEBALL_ON_PUPPY.sh",
        }

    if intent == "import_collx" or intent == "scan_drive":
        try:
            sys_path = str(STAN_DIR)
            if sys_path not in __import__("sys").path:
                __import__("sys").path.insert(0, sys_path)
            ws = str(BASEBALL_WS)
            if ws not in __import__("sys").path:
                __import__("sys").path.insert(0, ws)
            from collx_data import auto_import_from_drive, reimport_last_source, status as collx_status

            r = auto_import_from_drive()
            if r.get("status") != "success":
                r = reimport_last_source()
            cx = collx_status()
            return {
                "status": r.get("status", "error"),
                "imported": r.get("imported"),
                "collection_count": r.get("collection_count"),
                "catalog_count": cx.get("catalog_count"),
                "priced_count": cx.get("priced_count"),
                "message": r.get("message"),
            }
        except Exception as exc:
            return {"status": "failed", "error": str(exc)}

    if intent == "fix_thumbnails":
        try:
            __import__("sys").path.insert(0, str(BASEBALL_WS))
            from collx_data import reimport_last_source

            r = reimport_last_source()
            return {"status": r.get("status"), "imported": r.get("imported"), "note": "thumbnails refreshed"}
        except Exception as exc:
            return {"status": "failed", "error": str(exc)}

    if intent == "refresh_status":
        refresh_brian_status()
        return {"status": "success", "note": "status file updated"}

    if intent == "serve_phone":
        script = DRIVE_ROOT / "lester" / "START_BASEBALL_ON_PUPPY.sh"
        if script.is_file() and HOSTNAME in ("puppy", "puppy64"):
            return {
                "status": "pending",
                "note": "Run START_BASEBALL_ON_PUPPY.sh on puppy and post puppy_outbox.txt",
                "script": str(script),
            }
        return {"status": "failed", "error": "Not on puppy64"}

    return {"status": "skipped", "note": f"No handler for intent {intent} on {HOSTNAME}"}


def process_pending_jobs(max_jobs: int = 1) -> list[dict[str, Any]]:
    """Captain/worker: run pending jobs this machine can handle."""
    results: list[dict[str, Any]] = []
    with _lock:
        q = load_queue()
        for job in q["jobs"]:
            if job.get("status") != "pending":
                continue
            if not _can_run_job(job):
                continue
            job["status"] = "running"
            job["started_at"] = _now()
            save_queue(q)
            outcome = _execute_job(job)
            job["status"] = "done" if outcome.get("status") == "success" else (
                "failed" if outcome.get("status") == "failed" else "done"
            )
            job["completed_at"] = _now()
            job["result"] = outcome
            job["hostname_done"] = HOSTNAME
            if outcome.get("error"):
                job["error"] = outcome["error"]
            save_queue(q)
            results.append(job)
            if len(results) >= max_jobs:
                break
    if results:
        refresh_brian_status()
    return results


def read_brian_status() -> str:
    if STATUS_FILE.is_file():
        try:
            return STATUS_FILE.read_text(encoding="utf-8", errors="replace").strip()
        except OSError:
            pass
    return refresh_brian_status()


def _fetch_baseball_snapshot() -> dict[str, Any]:
    snap: dict[str, Any] = {"app": "unknown", "cards": 0, "priced": 0, "total_low": 0, "total_high": 0}
    try:
        with urllib.request.urlopen("http://127.0.0.1:8002/api/health", timeout=3) as r:
            h = json.loads(r.read())
        snap["app"] = "running"
        snap["cards"] = h.get("cards", 0)
        snap["collx_catalog"] = h.get("collx_catalog", 0)
        snap["ui"] = h.get("ui_version", "")
    except Exception:
        snap["app"] = "down"
    try:
        with urllib.request.urlopen("http://127.0.0.1:8002/api/cards", timeout=5) as r:
            c = json.loads(r.read())
        snap["cards"] = c.get("count", snap["cards"])
        snap["priced"] = c.get("priced_count", 0)
        snap["total_low"] = c.get("total_low", 0)
        snap["total_high"] = c.get("total_high", 0)
    except Exception:
        pass
    return snap


def refresh_brian_status(waiting_note: str = "") -> str:
    """Build BRIAN_STATUS.txt — plain English, no code."""
    caps = _caps()
    snap = _fetch_baseball_snapshot()
    phone = ""
    if PHONE_FILE.is_file():
        try:
            phone = PHONE_FILE.read_text(encoding="utf-8", errors="replace").strip()
            m = re.search(r"https?://[^\s]+", phone)
            phone = m.group(0) if m else phone.split("\n")[0][:80]
        except OSError:
            phone = ""

    q = load_queue()
    pending = [j for j in q.get("jobs", []) if j.get("status") == "pending"]
    last_done = next((j for j in q.get("jobs", []) if j.get("status") == "done"), None)

    lines = [
        "# Brian status — read this, not the code",
        f"Updated: {_now()}",
        f"This machine: {HOSTNAME} ({caps.get('role', 'worker')})",
        "",
    ]

    if snap["app"] == "running":
        lines.append("Baseball cards app: RUNNING on this machine.")
        if snap["cards"]:
            lines.append(
                f"Collection: {snap['cards']} cards, {snap.get('priced', 0)} with CollX prices."
            )
            if snap.get("total_low") or snap.get("total_high"):
                lines.append(
                    f"Total value (CollX): about ${snap['total_low']:.0f} – ${snap['total_high']:.0f}."
                )
        else:
            lines.append("Collection: empty — import CollX CSV (CollX tab or save email to collx_inbox).")
    else:
        lines.append("Baseball cards app: not running on this machine right now.")

    if phone:
        lines.append(f"Phone link: {phone}")
        lines.append("Keep Chromebook awake while testing on phone.")
    elif caps.get("can_serve_phone_wifi"):
        lines.append("Phone: run START_BASEBALL_ON_PUPPY.sh on this machine (home Wi-Fi).")
    else:
        lines.append("Phone: use link in BRIAN_PHONE.txt on Drive (Cloudflare tunnel from Chromebook).")

    lines.append("")
    if waiting_note:
        lines.append(f"Waiting on: {waiting_note}")
    elif pending:
        lines.append(f"Waiting on: {pending[0].get('intent')} — ({pending[0].get('said', '')[:60]})")
    elif last_done:
        lines.append(f"Last done: {last_done.get('intent')} on {last_done.get('hostname_done', '?')}.")
    else:
        lines.append("Waiting on: nothing — talk to Lester or open phone link.")

    lines.extend(
        [
            "",
            "You do NOT copy messages between Cursors.",
            "Queue file (machines only): brian_queue.json on Drive.",
        ]
    )

    text = "\n".join(lines) + "\n"
    _write_text(STATUS_FILE, text)
    return text


def brian_status_summary() -> str:
    """Short line for Lester to speak."""
    text = read_brian_status()
    keep = []
    for line in text.splitlines():
        if line.startswith("#") or not line.strip():
            continue
        if line.startswith("Updated:") or line.startswith("This machine:"):
            continue
        if line.startswith("Queue file"):
            continue
        keep.append(line.strip())
    return " ".join(keep[:4])[:400]


def show_footer(cursor_ctx_pct: float | None = None, cursor_tokens_k: int | None = None) -> str:
    """CB1-style one-line footer: project | cursor ctx | gemini ultra est."""
    brief_path = STAN_DIR / "handoff" / "brief.json"
    session_path = STAN_DIR / "handoff" / "session_note.md"
    gemini_path = STAN_DIR / "handoff" / "gemini_usage.json"
    proj = "cb2"
    if brief_path.is_file():
        try:
            b = json.loads(brief_path.read_text(encoding="utf-8"))
            proj = (b.get("project") or proj)[:48]
        except (json.JSONDecodeError, OSError):
            pass
    if session_path.is_file():
        try:
            for line in session_path.read_text(encoding="utf-8", errors="replace").splitlines():
                s = line.strip()
                if s.startswith("**Active program:**"):
                    proj = s.replace("**Active program:**", "", 1).strip()[:48]
                    break
        except OSError:
            pass
    if cursor_ctx_pct is not None:
        ctx = f"{int(cursor_ctx_pct)}%"
        if cursor_tokens_k:
            ctx = f"{ctx} ({cursor_tokens_k}k)"
    else:
        ctx = "?"
    gem = "gemini ultra ~?"
    if gemini_path.is_file():
        try:
            g = json.loads(gemini_path.read_text(encoding="utf-8"))
            used = float(g.get("used_units", 0) or 0)
            budget = float(g.get("daily_budget_units", 100) or 100) or 100
            pct = min(100, int(used * 100 / budget))
            plan = g.get("plan") or "ultra"
            gem = f"gemini {plan} ~{pct}% est"
        except (json.JSONDecodeError, OSError, TypeError, ValueError):
            pass
    return f"show  {proj}  |  cursor ctx {ctx}  |  {gem}"


def _watch_loop(interval: float = 20.0) -> None:
    while True:
        try:
            process_pending_jobs(max_jobs=1)
        except Exception:
            pass
        try:
            refresh_brian_status()
        except Exception:
            pass
        time.sleep(interval)


def start_queue_watcher(interval: float = 20.0) -> None:
    global _watcher_started
    if _watcher_started:
        return
    refresh_brian_status()
    t = threading.Thread(target=_watch_loop, args=(interval,), name="brian-os-watch", daemon=True)
    t.start()
    _watcher_started = True


if __name__ == "__main__":
    import sys

    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    if cmd == "status":
        print(read_brian_status())
    elif cmd == "refresh":
        print(refresh_brian_status())
    elif cmd == "summary":
        print(brian_status_summary())
    elif cmd == "show":
        pct = float(sys.argv[2]) if len(sys.argv) > 2 else None
        tk = int(sys.argv[3]) if len(sys.argv) > 3 else None
        print(show_footer(pct, tk))
    elif cmd == "queue":
        intent = sys.argv[2] if len(sys.argv) > 2 else "refresh_status"
        said = sys.argv[3] if len(sys.argv) > 3 else ""
        j = queue_job(intent, said=said)
        print(json.dumps(j, indent=2))
        process_pending_jobs()
        print(read_brian_status())
    elif cmd == "process":
        done = process_pending_jobs(max_jobs=3)
        print(json.dumps(done, indent=2))
        print(read_brian_status())
    elif cmd == "watch":
        print("Brian OS watcher running...", flush=True)
        refresh_brian_status()
        _watch_loop(interval=float(sys.argv[2]) if len(sys.argv) > 2 else 20.0)
    else:
        print(f"Unknown: {cmd}")
