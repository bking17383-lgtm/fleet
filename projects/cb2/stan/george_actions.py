#!/usr/bin/env python3
"""George skills — do stuff locally (Alexa-style) · back-end still Daddy."""
from __future__ import annotations

import re
import subprocess
import urllib.request
from datetime import datetime, timezone
from typing import Any

from bus_lane import STAN, bus_root, safe_is_file, safe_mkdir, safe_read_text

REMINDERS = "fleet/bus/GEORGE_REMINDERS.txt"
OPEN_STAMP = "fleet/bus/GEORGE_OPEN.txt"
ACTION_LOG = "fleet/bus/GEORGE_LAST_ACTION.json"

# spoken name → path
OPEN_MAP: dict[str, str] = {
    "dirt strong": "/dirt-strong",
    "dirt": "/dirt-strong",
    "homestead": "/dirt-strong",
    "parcels": "/parcels",
    "five parcels": "/parcels",
    "lab": "/lab",
    "daddy": "/lab",
    "bunny": "/bunny",
    "bunny lab": "/bunny",
    "goal": "/goal",
    "fleet": "/goal",
    "george": "/george",
    "landing": "/landing",
    "sarah": "/sarah",
    "cards": "/cards/sell",
    "app solution": "/app-solution",
    "confession": "/app-solution",
}


def _now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def _domain() -> str:
    p = bus_root() / "fleet/HITME_DOMAIN.txt"
    if safe_is_file(p):
        line = safe_read_text(p).strip().splitlines()
        if line and line[0].strip():
            return line[0].strip()
    return "hitme.dev"


def _url(path: str) -> str:
    p = path if path.startswith("/") else f"/{path}"
    return f"https://{_domain()}{p}"


def _log_action(name: str, **fields: Any) -> None:
    import json

    bus = bus_root()
    p = bus / ACTION_LOG
    safe_mkdir(p.parent)
    payload = {"time": _now(), "skill": name, **fields}
    p.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def last_action() -> dict:
    import json

    p = bus_root() / ACTION_LOG
    if not safe_is_file(p):
        return {}
    try:
        return json.loads(safe_read_text(p))
    except json.JSONDecodeError:
        return {}


def _open(path: str, *, label: str) -> tuple[str, list[str], str | None]:
    url = _url(path)
    bus = bus_root()
    safe_mkdir((bus / OPEN_STAMP).parent)
    (bus / OPEN_STAMP).write_text(f"GEORGE_OPEN — {_now()}\nurl={url}\nlabel={label}\n", encoding="utf-8")
    _log_action("open", url=url, label=label)
    return f"Opening {label}.", [f"open:{path}"], url


def team_roster() -> str:
    return (
        "Our team: Brian, Daddy on CB2 penguin — captain and code. "
        "Puppy on puppy64 — mesh and URLs. Uncle on CB1 — studio. "
        "Gem on CB1 Chrome — Drive. Bunny on her indie lane. "
        "I'm George — front-end voice here; Daddy runs back-end on this box."
    )


def _file_age_minutes(rel: str) -> int | None:
    p = bus_root() / rel
    if not safe_is_file(p):
        return None
    try:
        m = datetime.fromtimestamp(p.stat().st_mtime).astimezone()
        return max(0, int((datetime.now().astimezone() - m).total_seconds() // 60))
    except OSError:
        return None


def george_update_info() -> str:
    """Minutes since last George file touch — team clock, not a coding lecture."""
    ages = {
        "memory": _file_age_minutes("fleet/bus/GEORGE_MEMORY.txt"),
        "upgrade": _file_age_minutes("fleet/bus/GEORGE_UPGRADE_STAMP.txt"),
        "reply": _file_age_minutes("fleet/bus/GEORGE_LAST_REPLY.txt"),
    }
    parts = [f"{k} {v} min ago" for k, v in ages.items() if v is not None]
    if not parts:
        return "No George stamps yet — I'm still your front-end; Daddy runs back-end on this box."
    return (
        "George last touched: "
        + ", ".join(parts)
        + ". I'm on our team — front-end voice; Daddy is back-end captain."
    )


def _fleet_summary() -> str:
    bus = bus_root()
    chk = bus / "fleet/bus/FLEET_CHECKIN.txt"
    if not safe_is_file(chk):
        try:
            subprocess.run(
                ["python3", str(STAN / "fleet_checkin.py"), "once"],
                capture_output=True,
                timeout=25,
                check=False,
            )
        except (OSError, subprocess.SubprocessError):
            pass
    if not safe_is_file(chk):
        return "Fleet check-in file missing — Daddy may be down."
    lines = [ln.strip() for ln in safe_read_text(chk).splitlines() if ln.strip()]
    hits: list[str] = []
    for ln in lines:
        if ln.startswith("✓") or ln.startswith("✗") or ln.startswith("DADDY") or ln.startswith("GEM"):
            hits.append(ln[:70])
        if len(hits) >= 4:
            break
    if not hits:
        hits = lines[:4]
    return "Roll call: " + ". ".join(hits)[:220]


def _health() -> str:
    ok_local = False
    try:
        with urllib.request.urlopen("http://127.0.0.1:8770/health", timeout=3) as r:
            ok_local = r.status == 200
    except OSError:
        pass
    pub = False
    try:
        with urllib.request.urlopen(f"https://{_domain()}/health", timeout=6) as r:
            pub = r.status == 200
    except OSError:
        pass
    parts = []
    if ok_local:
        parts.append("CB2 desk is up")
    else:
        parts.append("desk down")
    if pub:
        parts.append(f"{_domain()} is live")
    else:
        parts.append("public site flaky")
    return ". ".join(parts) + "."


def _wake_daddy(job: str, heard: str) -> tuple[str, list[str], str | None]:
    from george_self import _ping_daddy

    _ping_daddy(job, heard)
    try:
        subprocess.Popen(
            ["python3", str(STAN / "cpt_lab_auto.py"), "once"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except OSError:
        pass
    _log_action("wake_daddy", job=job[:200])
    return "Done — I woke Daddy on the back end.", [f"daddy:{job[:80]}"], None


def _remind(text: str) -> tuple[str, list[str], str | None]:
    bus = bus_root()
    p = bus / REMINDERS
    safe_mkdir(p.parent)
    line = f"- [{_now()}] {text.strip()[:240]}"
    prior = safe_read_text(p).strip() if safe_is_file(p) else ""
    header = f"GEORGE REMINDERS\nUpdated: {_now()}\n"
    body = (prior + "\n" + line).strip() if prior else header + "\n" + line
    p.write_text(body + "\n", encoding="utf-8")
    _log_action("remind", text=text[:200])
    short = text.strip()[:60]
    return f"Got it — I'll remember: {short}.", ["remind"], None


def _help() -> tuple[str, list[str], str | None]:
    msg = (
        "Try: what time · fleet status · open dirt strong · "
        "check doc google idea · read more · "
        "remind me to … · ask daddy to fix something · health check."
    )
    return msg, ["help"], None


def try_local(heard: str) -> tuple[str, list[str], str | None] | None:
    """Fast skill match — no AWS. Returns (spoken, actions, open_url)."""
    msg = heard.strip()
    if not msg:
        return None
    low = msg.lower()

    if re.search(r"\b(what can you do|help|skills)\b", low):
        return _help()

    if re.search(
        r"\b(?:time\s*stamp|estamp|stamp)\b.*\bsilent\b|\bsilent\b.*\b(?:time\s*stamp|estamp|stamp)\b|"
        r"only (?:give|say|read).*time\s*stamp.*(?:if|when) (?:i|you) ask|"
        r"no time\s*stamp(?:s)? unless (?:i|you) ask",
        low,
    ):
        from george_self import _write_pref

        _write_pref("Timestamps silent — only read file-age/min-ago aloud when Brian explicitly asks")
        _log_action("pref", text="timestamp_silent")
        return "Got it — timestamps stay silent unless you ask.", ["pref:timestamp_silent"], None

    doc = None
    try:
        from george_docs import try_doc

        doc = try_doc(msg)
    except ImportError:
        pass
    if doc:
        return doc

    if re.search(r"\b(read more|continue|keep going|finish)\b", low):
        try:
            from george_docs import find_doc, read_doc, summarize_for_voice

            hits = find_doc(" ".join(low.split()[-4:]))
            if hits:
                path, _ = hits[0]
                body = read_doc(path)
                return summarize_for_voice(path.stem, body, cap=2400), ["doc:more"], None
        except ImportError:
            pass

    if re.search(r"^(hi|hey|hello|yo|howdy|george)\b", low) or re.search(
        r"\b(you there|anyone there|wake up)\b", low
    ):
        from george_chatter import greet_reply

        msg = greet_reply()
        _log_action("greet")
        return msg, ["greet"], None

    if re.search(r"\b(what time|what'?s the time|time is it)\b", low):
        t = datetime.now().astimezone().strftime("%I:%M %p").lstrip("0")
        _log_action("time")
        return f"It's {t}.", ["time"], None

    if re.search(r"\b(health|status check|are you up|system status)\b", low) and "fleet" not in low:
        return _health(), ["health"], None

    if re.search(
        r"\b(our team|who(?:'s| is| are) on (?:the |our )?team|team members?|who are we)\b", low
    ):
        return team_roster(), ["team"], None

    if re.search(
        r"\b(alexa or george|is this alexa|this alexa|you alexa|like alexa|amazon voice|awe voice|alexa\.?\s*politic)\b",
        low,
    ):
        return "I'm George — our front-end voice on this box. Not Alexa.", ["identity"], None

    if re.search(
        r"\b(sound like daddy|like daddy|be like daddy|talk like daddy|more like daddy|"
        r"make you like daddy|be more like daddy|think like daddy|away from alexa|not alexa)\b",
        low,
    ):
        return (
            "Copy — Daddy voice on the mic: direct, crew-first, zero Amazon fluff. "
            "I'm George; he builds on the back end."
        ), ["daddy_voice"], None

    if re.search(r"\b(alexa|amazon|trashy whore|that whore)\b", low) and re.search(
        r"\b(away|not|unlike|uninstall|kill|ditch|hate|trash)\b", low
    ):
        return (
            "Yeah — screw the Amazon script. I'm George on our ranch, talking like Daddy now."
        ), ["daddy_voice"], None

    if re.search(r"\b(politics?|political|alexa[\s\.]*politics?|corporate|alexa tone|sound like alexa)\b", low):
        return (
            "Our home lab — no Amazon disclaimers. "
            "Ask about the crew or the ranch and I'll answer straight like Daddy would."
        ), ["no_politics"], None

    if re.search(r"\b(stop talk|stop talking|shut up|be quiet|silence)\b", low):
        return "Got it — I'll listen.", ["quiet"], None

    if re.search(
        r"\b(last update|got an update|minutes since|how many minutes|timestamp|"
        r"when.*update|george.*update|new update|reflect minutes|minutes as a net)\b",
        low,
    ) or low.strip() in ("when", "when?"):
        return george_update_info(), ["update_age"], None

    if re.search(r"\b(fleet|roll call|who'?s up|check.?in)\b", low):
        return _fleet_summary(), ["fleet"], None

    if re.search(r"\b(working url|the url|link|bookmark)\b", low):
        w = bus_root() / "fleet/bus/WORKING_URL.txt"
        url = "https://hitme.dev/george"
        if safe_is_file(w):
            for ln in safe_read_text(w).splitlines():
                if ln.strip().startswith("http"):
                    url = ln.strip()
                    break
        return f"Your link is {url.replace('https://', '')}.", ["url"], url

    m = re.search(r"\b(?:remind me(?: to)?|remember to)\s+(.+)", low)
    if m:
        return _remind(m.group(1))

    m = re.search(r"\b(?:note|write down)\s+(.+)", low)
    if m:
        from george_self import _write_note

        note = m.group(1).strip()
        _write_note(note)
        _log_action("note", text=note[:200])
        return "Noted.", ["note"], None

    if re.search(r"\b(?:open|go to|launch)\s+(?:the\s+)?", low):
        for key, path in sorted(OPEN_MAP.items(), key=lambda x: -len(x[0])):
            if re.search(rf"\b{re.escape(key)}\b", low):
                label = key.title()
                return _open(path, label=label)

    if re.search(r"\b(ask daddy|tell daddy|wake daddy|have daddy|ping daddy)\b", low):
        job = re.sub(r"^.*?(ask daddy|tell daddy|wake daddy|have daddy|ping daddy)\s*", "", low, flags=re.I).strip()
        if not job:
            job = msg
        return _wake_daddy(job, heard)

    return None
