#!/usr/bin/env python3
"""George reads Daddy's rail — site · git truth · slave · queue stats."""
from __future__ import annotations

import json
import re
from pathlib import Path

from bus_lane import STAN, bus_root, safe_is_file, safe_read_text

CACHE = STAN / "handoff/cb2_status_cache.json"
STATUS = Path.home() / "cb2_sandbox/STATUS.txt"
SITE = Path.home() / ".cache/hitme-site-state"
PROGRESS = STAN / "daddy_progress.json"
OPUS = Path.home() / "fleet/bus/cb2/from-opus.md"


def _read_json(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def _opus_job() -> str:
    if not OPUS.is_file():
        return ""
    text = OPUS.read_text(encoding="utf-8", errors="replace")
    m = re.search(r">>>\s*CURRENT JOB[^\n]*:\s*(.+?)\s*<<<", text, re.I)
    if m:
        return re.sub(r"\s+", " ", m.group(1)).strip()[:100]
    return ""


def progress_pct() -> tuple[int, str, str]:
    data = _read_json(PROGRESS)
    steps = data.get("steps") or []
    if not steps:
        return 0, data.get("job_title") or "sandbox work", ""
    total = sum(int(s.get("weight") or 1) for s in steps)
    done = sum(int(s.get("weight") or 1) for s in steps if s.get("done"))
    pct = int(round(100 * done / total)) if total else 0
    title = data.get("job_title") or "Daddy sandbox"
    current = ""
    for s in steps:
        if s.get("current") and not s.get("done"):
            current = str(s.get("label") or "")
            break
        if not s.get("done") and not current:
            current = str(s.get("label") or "")
    return pct, title, current


def _parse_status_txt() -> dict[str, str]:
    out: dict[str, str] = {}
    if not STATUS.is_file():
        return out
    for ln in STATUS.read_text(encoding="utf-8", errors="replace").splitlines():
        if "        " in ln:
            key, _, val = ln.partition("        ")
            out[key.strip()] = val.strip()
    return out


def snapshot() -> dict:
    bus = bus_root()
    cache = _read_json(CACHE)
    stxt = _parse_status_txt()
    site = SITE.read_text(encoding="utf-8").strip() if SITE.is_file() else "?"
    rail = safe_read_text(bus / "fleet/bus/RAIL.txt").strip().splitlines()
    rail_line = rail[0][:120] if rail else "fleet"
    pct, job_title, current_step = progress_pct()
    opus = _opus_job()
    geo_q = bus / "fleet/bus/george_to_daddy.txt"
    queue_text = safe_read_text(geo_q).strip() if safe_is_file(geo_q) else ""
    queue_job = ""
    if queue_text:
        for ln in queue_text.splitlines():
            if ln.lower().startswith("job:"):
                queue_job = ln.split(":", 1)[1].strip()[:120]
                break
            if ln.lower().startswith("heard:"):
                queue_job = queue_job or ln.split(":", 1)[1].strip()[:120]

    truth = cache.get("truth") or stxt.get("TRUTH", "?").split("·")[0].strip()
    eyes = cache.get("eyes") or cache.get("slave") or "?"
    ack = cache.get("ack_min", "?")
    gl = cache.get("gl", "?")
    local = cache.get("git_local", "?")

    return {
        "site": site,
        "rail_line": rail_line,
        "truth": truth,
        "git_local": local,
        "slave": eyes,
        "eyes": eyes,
        "ack_min": ack,
        "gl": gl,
        "job_title": job_title,
        "job_current_step": current_step,
        "job_pct": pct,
        "opus_job": opus,
        "queue_pending": bool(queue_text),
        "queue_job": queue_job,
        "queue_preview": queue_text[:180],
    }


def spoken_rail(*, compact: bool = True) -> str:
    s = snapshot()
    site = str(s.get("site") or "?").upper()
    parts = [
        f"site {site}",
        f"truth {s.get('truth', '?')}",
        f"eyes {s.get('eyes', s.get('slave', '?'))}",
    ]
    if s.get("ack_min") not in (None, "?", ""):
        parts.append(f"beacon ack {s.get('ack_min')}m")
    if compact:
        return "Rail: " + " · ".join(parts) + "."
    return (
        f"Rail — {s.get('rail_line', 'fleet')}. "
        + " · ".join(parts)
        + f" · git local {s.get('git_local', '?')}."
    )


def spoken_job_brief() -> str:
    s = snapshot()
    pct = s.get("job_pct", 0)
    title = s.get("job_title") or "sandbox work"
    step = s.get("job_current_step") or ""
    opus = s.get("opus_job") or ""
    bits = [f"Daddy job: {title} — {pct}% done."]
    if step:
        bits.append(f"Working now: {step}.")
    if opus:
        bits.append(f"Opus lane: {opus}.")
    return " ".join(bits)


def spoken_queue() -> str:
    s = snapshot()
    if not s.get("queue_pending"):
        return "George queue is clear — nothing waiting for Daddy."
    job = s.get("queue_job") or "your last ping"
    return f"George queue: one item for Daddy — {job[:100]}."
