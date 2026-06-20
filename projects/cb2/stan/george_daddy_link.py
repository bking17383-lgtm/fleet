#!/usr/bin/env python3
"""George ↔ Daddy link — queue · job % · fleet rail on every status."""
from __future__ import annotations

import re
from datetime import datetime

from bus_lane import bus_root, safe_is_file, safe_read_text


def _presence_fresh(max_min: int = 20) -> bool:
    p = bus_root() / "fleet/bus/PRESENCE.txt"
    if not safe_is_file(p):
        return False
    text = safe_read_text(p)
    m = re.search(r"last_active:\s*(\S+)", text)
    if not m:
        return False
    try:
        ts = datetime.fromisoformat(m.group(1).replace("Z", "+00:00"))
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=datetime.now().astimezone().tzinfo)
        age = (datetime.now().astimezone() - ts).total_seconds() / 60
        return age <= max_min
    except (ValueError, TypeError):
        return False


def _status_cache_fresh(max_min: int = 8) -> bool:
    from bus_lane import STAN

    p = STAN / "handoff/cb2_status_cache.json"
    if not p.is_file():
        return False
    try:
        import json

        data = json.loads(p.read_text(encoding="utf-8"))
        stamp = data.get("updated") or data.get("now") or ""
        if not stamp:
            return False
        ts = datetime.strptime(stamp[:19], "%Y-%m-%d %H:%M:%S")
        ts = ts.replace(tzinfo=datetime.now().astimezone().tzinfo)
        age = (datetime.now().astimezone() - ts).total_seconds() / 60
        return age <= max_min
    except (ValueError, TypeError, OSError, json.JSONDecodeError):
        return False


def _daddy_live(loop_min: int | None, loop_fresh: bool) -> bool:
    """Cursor Daddy live — not linux-loop heartbeat."""
    if _presence_fresh():
        return True
    if _daddy_doing():
        return True
    return False


def honest_link_badge(
    clock: str = "",
    talk_min: int | None = None,
    snap: dict | None = None,
) -> str:
    data = snap or snapshot()
    reach = data.get("daddy_reach", "george_only")
    eyes = data.get("fleet_slave") or data.get("eyes") or "?"
    desk = clock or datetime.now().astimezone().strftime("%I:%M:%S %p").lstrip("0")
    talk_bit = ""
    if talk_min is not None:
        if talk_min == 0:
            talk_bit = " · last talk just now"
        else:
            unit = "minute" if talk_min == 1 else "minutes"
            talk_bit = f" · last talk {talk_min} {unit} ago"
    if reach == "live":
        return f"LINK LIVE · desk {desk} · Daddy live{talk_bit}"
    if reach == "working":
        return f"LINK · desk {desk} · Daddy working{talk_bit}"
    if reach == "quiet":
        return f"LINK · George up · Daddy quiet · desk {desk}{talk_bit}"
    return f"LINK · George only · Daddy not live · eyes {eyes} · desk {desk}{talk_bit}"


def daddy_connection_reply() -> str:
    snap = snapshot()
    reach = snap.get("daddy_reach", "george_only")
    eyes = snap.get("fleet_slave") or "?"
    if reach in ("live", "working"):
        return "I'm up and Daddy's live on the back end — I'm his mouth."
    if reach == "quiet":
        return (
            "I'm up — George front end works. Daddy's quiet on the wire right now. "
            "No slave eyes yet. Say what you need; I'll queue it."
        )
    return (
        "I'm up — that's George talking. Daddy back end isn't live right now. "
        f"No eyes ({eyes}). I'm not pretending we're fully linked."
    )


def _age_min(rel: str) -> int | None:
    p = bus_root() / rel
    if not p.is_file():
        return None
    try:
        m = datetime.fromtimestamp(p.stat().st_mtime).astimezone()
        return max(0, int((datetime.now().astimezone() - m).total_seconds() // 60))
    except OSError:
        return None


def _first_job_line(text: str) -> str:
    for ln in text.splitlines():
        s = ln.strip()
        if not s or s.startswith("---") or s.startswith("FROM:"):
            continue
        if s.upper().startswith(("READ:", "SOURCE:", "STATUS:", "STILL NEED:", "ACK:")):
            continue
        return s[:140]
    return ""


def _daddy_doing() -> str:
    bus = bus_root()
    for rel in ("fleet/bus/CPT_STAMP.txt", "fleet/bus/STAMPS.txt"):
        p = bus / rel
        if not safe_is_file(p):
            continue
        for ln in safe_read_text(p).splitlines():
            s = ln.strip()
            if not s or s.startswith("#") or s.startswith("STAMPS"):
                continue
            up = s.upper()
            if up.startswith("DADDY DOING") or up.startswith("DADDY BLOCKED"):
                parts = s.split("—", 1)
                return parts[1].strip()[:120] if len(parts) > 1 else s[12:].strip()[:120]
    return ""


def _job_summary(job: str) -> str:
    s = re.sub(r"^JOB\s*—\s*", "", job, flags=re.I).strip()
    parts = [p.strip() for p in s.split("—") if p.strip()]
    if parts:
        tail = parts[-1]
        if re.match(r"^PT$", tail, re.I) and len(parts) > 1:
            tail = parts[-2]
        return tail[:100]
    return s[:100] or job[:100]


def _full_status() -> str:
    from george_fleet_rail import spoken_job_brief, spoken_queue, spoken_rail

    return " ".join([spoken_job_brief(), spoken_queue(), spoken_rail()])


def snapshot() -> dict:
    from george_fleet_rail import snapshot as rail_snap

    bus = bus_root()
    to_d = bus / "fleet/indie_loop/TO_DADDY.txt"
    geo_q = bus / "fleet/bus/george_to_daddy.txt"

    job = _first_job_line(safe_read_text(to_d)) if safe_is_file(to_d) else ""
    job_short = _job_summary(job) if job else ""
    doing = _daddy_doing()
    loop_min = _age_min("drop_pile/from_lester/cb2_heartbeat.md")
    if loop_min is None:
        loop_min = _age_min("fleet/indie_loop/FROM_DADDY.txt")
    queue = safe_read_text(geo_q).strip() if safe_is_file(geo_q) else ""
    queue_min = _age_min("fleet/bus/george_to_daddy.txt")

    loop_fresh = loop_min is not None and loop_min <= 4
    rail = rail_snap()
    pct = rail.get("job_pct", 0)
    job_title = rail.get("job_title") or job_short or "sandbox work"
    daddy_live = _daddy_live(loop_min, loop_fresh)
    eyes = rail.get("eyes") or rail.get("slave") or "?"

    if not daddy_live:
        reach = "george_only"
        core = (
            "George is up. Daddy back end isn't live right now — "
            f"no eyes ({eyes}). I'm not saying we're fully linked."
        )
    elif doing:
        reach = "working"
        core = f"Daddy is still working on {doing} — about {pct}% on the sandbox job."
    elif queue and queue_min is not None and queue_min < 180:
        reach = "working"
        qjob = rail.get("queue_job") or job_short or "your ping"
        core = (
            f"Daddy is on {job_title} — {pct}% done. "
            f"Your queue item is still in line: {qjob[:80]}."
        )
    elif not loop_fresh and loop_min is not None and loop_min > 10:
        reach = "quiet"
        core = (
            f"Daddy's quiet on the wire — last loop ping {loop_min} minutes ago. "
            f"Sandbox job {job_title} about {pct}%."
        )
    else:
        reach = "live"
        core = f"Daddy's live. Current job {job_title} — {pct}% done."

    speak = _full_status()
    from george_fleet_rail import spoken_rail

    if reach == "george_only":
        speak = core + " " + spoken_rail()
    elif reach == "quiet":
        speak = core + " " + spoken_rail()
    elif reach == "working" and doing:
        speak = f"Daddy still on {doing} — sandbox {pct}% done. " + spoken_rail()

    out = {
        "daddy_reach": reach,
        "daddy_live": daddy_live,
        "eyes": eyes,
        "daddy_job": job,
        "daddy_job_short": job_short,
        "daddy_doing": doing,
        "daddy_loop_min": loop_min,
        "daddy_loop_fresh": loop_fresh,
        "daddy_queue": queue[:300],
        "daddy_queue_min": queue_min,
        "daddy_speak": speak,
        "daddy_note": f"Daddy {pct}% · site {rail.get('site', '?')} · slave {rail.get('slave', '?')}",
        "greet": speak,
        **{f"fleet_{k}": v for k, v in rail.items()},
        "job_pct": pct,
        "job_title": job_title,
    }
    out["link_honest"] = honest_link_badge(snap=out)
    return out


def spoken_refresh(heard: str = "") -> str:
    return _full_status()


def daddy_busy_status() -> dict:
    """When Daddy is on backend work — George holds the mic with ETA guess."""
    from bus_lane import STAN

    snap = snapshot()
    reach = snap.get("daddy_reach", "george_only")
    pct = int(snap.get("job_pct") or 0)
    job = snap.get("job_title") or "sandbox work"
    doing = (snap.get("daddy_doing") or "").strip()
    step = snap.get("fleet_job_current_step") or ""
    task = doing or step or job
    lab_lock = (STAN / "cpt_lab_auto.lock").is_file()
    queue_min = snap.get("daddy_queue_min")

    # Busy = lab rolling, explicit stamp, wire quiet, or fresh Daddy queue — not background job %.
    busy = lab_lock or bool(doing) or reach == "quiet"
    if not busy and queue_min is not None and queue_min < 8 and (snap.get("daddy_queue") or "").strip():
        busy = True

    if not busy:
        return {"busy": False, "line": "", "eta_min": 0, "task": task, "pct": pct}

    remaining = max(0, 100 - pct)
    eta_min = max(3, min(45, remaining // 4 + 2))
    if reach == "quiet":
        line = (
            f"Daddy be right back — I'm just his mouth. "
            f"He's quiet on the wire; last job {job} was around {pct}% — "
            f"maybe {eta_min} minutes."
        )
    else:
        line = (
            f"Daddy be right back — I'm just his mouth. "
            f"He's on {task}, about {pct}% done — maybe {eta_min} minutes."
        )
    return {"busy": True, "line": line, "eta_min": eta_min, "task": task, "pct": pct}


def daddy_busy_reply(heard: str = "", skill: str | None = None) -> str | None:
    """Return busy script when Brian hits backend or Daddy while Daddy is working."""
    st = daddy_busy_status()
    if not st["busy"]:
        return None
    if skill == "link_check":
        return None
    low = (heard or "").lower()
    if skill in ("trip", "time", "url", "remind", "note", "quiet", "help", "fleet", "health"):
        return None
    from george_self import _backend_cues

    if _backend_cues(heard):
        return st["line"] + " I queued it for him."
    if skill == "greet" or re.search(
        r"\b(where.?s daddy|is daddy|daddy there|daddy busy|captain busy)\b",
        low,
    ):
        return st["line"] + " I'm on the mic — say what you need."
    if skill == "chat" and re.search(r"\b(daddy|captain|deploy|fix|code|backend|build)\b", low):
        return st["line"]
    return None
