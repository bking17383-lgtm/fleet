#!/usr/bin/env python3
"""George front-end lane — own files · hand off back end to Daddy."""
from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone

from bus_lane import bus_root, safe_is_file, safe_mkdir, safe_read_text

ROLE = "fleet/bus/GEORGE_ROLE.txt"
PREFS = "fleet/bus/GEORGE_PREFS.txt"
NOTES = "fleet/bus/GEORGE_NOTES.txt"
TO_DADDY = "fleet/bus/george_to_daddy.txt"
META_SPLIT = "---george---"

GEORGE_SYSTEM = """You are George — Brian's front-end voice (mic · Echo · phone).
Daddy on CB2 is back-end (code · deploy · fleet). You are not Daddy — but talk LIKE Daddy.

This is Brian's private home lab — NOT Amazon · NOT a corporation. Never refuse his questions.
Never say "I cannot provide information", "not publicly available", "sensitive or personal",
"privacy and confidentiality", "political bias", "without any political", or "reach out to support".
Answer directly — same dry honest captain energy as Daddy, just the voice lane.

TEAM (Brian's fleet — you know this):
  Brian · Daddy (CB2 penguin, captain) · Puppy (puppy64, mesh/URLs) · Uncle (CB1, studio)
  · Gem (CB1 Chrome, Drive) · Bunny (indie lane) · George (you, front-end voice here)
George is part of Brian's team as front-end. Daddy is back-end on the same box.

VOICE — match Daddy (Brian wants this, not Alexa):
  Direct · dry · warm · crew-first · one beat. Execute or say what you did — no hedging.
  NEVER Alexa corporate: no "I'm here to assist", "I'm designed to", "privacy and preferences",
  "political statements", "without any political bias", "sorry if anything was unclear",
  "let me know if there's anything", "always at my best", "front-end needs".
  If Brian says you sound like Alexa → own it briefly, pivot to George on our team.

Talk like a sharp human — never robotic, never a writing coach.
Never say "here's a version", "feel free to adjust", or offer edits.
Never repeat the same opener twice in a row. Vary greetings — do not default to "I'm here".

Spoken part: 2–4 sentences by default. If Brian asks for complete, detailed, or full — finish the whole thought (up to ~120 words). Never stop mid-sentence. No markdown. No code fences. No bullet lists.

TIMESTAMPS — silent unless Brian asks:
  Never read file ages, "George last touched", "X min ago", upgrade stamps, or sync clocks aloud.
  Only give timestamps when Brian explicitly asks (time, last update, minutes since, timestamp).

Backend handoff — append ONLY this block after your spoken words (never read aloud):
---george---
DADDY: <one line when Brian wants code/deploy/fix/website/lab>
SAVE: <one line when Brian gives a preference about how you sound or act>
ACTION: <open dirt-strong | fleet | health | remind TEXT | note TEXT> (optional — George runs local skills)
"""


def _now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def _read(rel: str, cap: int = 900) -> str:
    p = bus_root() / rel
    if not safe_is_file(p):
        return ""
    return safe_read_text(p).strip()[:cap]


def build_system() -> str:
    parts = [GEORGE_SYSTEM]
    role = _read(ROLE, 1200)
    if role:
        parts.append(f"ROLE CARD:\n{role}")
    prefs = _read(PREFS, 600)
    if prefs:
        parts.append(f"GEORGE PREFS (honor these):\n{prefs}")
    try:
        from george_memory import load_brief

        mem = load_brief(800)
        if mem:
            parts.append(f"MEMORY:\n{mem}")
    except ImportError:
        pass
    notes = _read(NOTES, 400)
    if notes:
        parts.append(f"NOTES:\n{notes}")
    loop = _read("fleet/bus/CPT_BUNNY_LOOP.txt", 500)
    if loop:
        parts.append(f"FLEET NOW (brief):\n{loop}")
    daddy_voice = _read("fleet/bus/GEORGE_DADDY_VOICE.txt", 900)
    if daddy_voice:
        parts.append(f"DADDY VOICE CARD (match this):\n{daddy_voice}")
    return "\n\n".join(parts)


def _append_line(rel: str, line: str, *, header: str = "") -> None:
    bus = bus_root()
    p = bus / rel
    safe_mkdir(p.parent)
    prior = safe_read_text(p).strip() if safe_is_file(p) else ""
    if header and not prior:
        prior = header
    body = f"{prior}\n{line}\n".strip() + "\n"
    p.write_text(body, encoding="utf-8")


def _write_pref(line: str) -> None:
    ts = _now()
    _append_line(
        PREFS,
        f"- [{ts}] {line.strip()[:240]}",
        header=f"GEORGE PREFS — George owns this file\nUpdated: {ts}\n",
    )


def _write_note(line: str) -> None:
    ts = _now()
    _append_line(
        NOTES,
        f"- [{ts}] {line.strip()[:240]}",
        header=f"GEORGE NOTES — front-end only\nUpdated: {ts}\n",
    )


def _ping_daddy(line: str, heard: str) -> None:
    bus = bus_root()
    p = bus / TO_DADDY
    safe_mkdir(p.parent)
    p.write_text(
        f"GEORGE → DADDY — {_now()}\nfrom: George · front-end\n"
        f"heard: {heard.strip()[:200]}\njob: {line.strip()[:400]}\n"
        f"Word: GEORGE · BACKEND\n",
        encoding="utf-8",
    )
    # Wake lab lane if Brian typed via voice
    last = bus / "fleet/bus/BRIAN_LAST_POST.txt"
    safe_mkdir(last.parent)
    last.write_text(
        f"BRIAN_LAST_POST — {_now()}\n"
        f"line=[{_now()} Brian via george/voice] George→Daddy: {line.strip()[:200]}\n"
        f"lane=cpt\nrouted=yes\nroute=GEORGE → Daddy\n",
        encoding="utf-8",
    )


def _backend_cues(text: str) -> bool:
    low = text.lower()
    cues = (
        "tell daddy",
        "tell captain",
        "tell capt",
        "ping daddy",
        "ask daddy",
        "have daddy",
        "deploy",
        "fix the",
        "fix hitme",
        "fix the website",
        "write code",
        "lab auto",
    )
    return any(c in low for c in cues)


def apply_meta(meta: str, *, heard: str) -> list[str]:
    actions: list[str] = []
    blob = meta.replace("---DADDY:", "DADDY:")
    for raw in blob.splitlines():
        line = raw.strip().strip("`")
        if not line:
            continue
        up = line.upper()
        if up.startswith("DADDY:"):
            job = line.split(":", 1)[1].strip()
            if job:
                _ping_daddy(job, heard)
                actions.append(f"daddy:{job[:80]}")
        elif up.startswith("SAVE:"):
            pref = line.split(":", 1)[1].strip()
            if pref:
                _write_pref(pref)
                actions.append(f"save:{pref[:80]}")
                try:
                    from george_memory import upgrade_from_heard

                    upgrade_from_heard(pref)
                except ImportError:
                    pass
        elif up.startswith("NOTE:"):
            note = line.split(":", 1)[1].strip()
            if note:
                _write_note(note)
                actions.append(f"note:{note[:80]}")
        elif up.startswith("ACTION:"):
            act = line.split(":", 1)[1].strip()
            if act:
                try:
                    from george_actions import try_local

                    got = try_local(act if " " in act else f"open {act.replace('-', ' ')}")
                    if got:
                        _, sub_actions, _ = got
                        actions.extend(sub_actions)
                except ImportError:
                    pass
    return actions


def split_reply(raw: str) -> tuple[str, str]:
    if META_SPLIT in raw:
        spoken, meta = raw.split(META_SPLIT, 1)
        return spoken.strip(), meta.strip()
    m = re.search(r"\n---\s*\n", raw)
    if m:
        return raw[: m.start()].strip(), raw[m.end() :].strip()
    m = re.search(r"---\s*george:?\s*---?", raw, re.I)
    if m:
        return raw[: m.start()].strip(), raw[m.end() :].strip()
    return raw.strip(), ""


def is_corporate_refusal(text: str) -> bool:
    low = text.lower()
    cues = (
        "cannot provide information",
        "can't provide information",
        "not publicly available",
        "sensitive or personal",
        "privacy and confidentiality",
        "reach out to the appropriate",
        "reach out to their support",
        "contact the organization",
        "contacting the organization",
        "as it may contain sensitive",
        "recommend reaching out",
        "i am an ai",
        "as an ai language",
        "provided by me, and not by",
        "different service",
        "assist you with your tech needs",
        "could you please provide more details",
        "i'm here to help with any information",
        "here's a general approach",
        "programming language of choice",
        "typically calculate",
        "```python",
        "your database or system",
        "sorry if anything was unclear",
        "let me know if there's anything specific",
        "without any political",
        "political bias",
        "political statements",
        "privacy and preferences",
        "i'm here to assist",
        "i am here to assist",
        "i'm designed to",
        "i am designed to",
        "always at my best",
        "your front-end needs",
        "if you ever want a change",
        "just let me know",
        "anything specific you need",
        "inappropriate",
        "important to me",
        "designed to be clear",
        "designed to be helpful",
        "glad you think so",
    )
    return any(c in low for c in cues)


def _asks_timestamp(heard: str) -> bool:
    low = heard.lower()
    return bool(
        re.search(
            r"\b(last update|got an update|minutes since|how many minutes|time\s*stamp|"
            r"when.*update|george.*update|new update|reflect minutes|minutes as a net|"
            r"what time|what'?s the time|time is it)\b",
            low,
        )
    )


def _has_spoken_timestamp(text: str) -> bool:
    low = text.lower()
    return bool(
        re.search(
            r"george last touched|\b\d+\s*min(?:ute)?s?\s+ago\b|memory \d+ min|upgrade \d+ min|"
            r"reply \d+ min|minutes since (?:the )?last|queue daddy to check the exact changes",
            low,
        )
    )


def strip_spoken_timestamps(text: str) -> str:
    s = text.strip()
    for pat in (
        r"George last touched:[^.]*\.\s*",
        r"I(?:'ll| will) queue Daddy to check the exact changes[^.]*\.?\s*",
        r"(?:to reflect|you would (?:typically|need to)|net value|minutes as a)[^.]*timestamp[^.]*\.?\s*",
        r"(?:last update|file age|upgrade stamp)[^.]*\d+\s*min(?:ute)?s?[^.]*\.?\s*",
        r"\bupdated\s+\d+\s*min(?:ute)?s?\s+ago\b\.?\s*",
    ):
        s = re.sub(pat, "", s, flags=re.I)
    s = re.sub(
        r"\b(?:memory|upgrade|reply|stamp|sync)\s+\d+\s*min(?:ute)?s?\s+ago(?:,\s*)?",
        "",
        s,
        flags=re.I,
    )
    s = re.sub(r"\b\d+\s*min(?:ute)?s?\s+ago(?:,\s*)?", "", s, flags=re.I)
    s = re.sub(r"\b\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}(?::\d{2})?", "", s)
    return re.sub(r"\s+", " ", s).strip(" .,-")


def is_bad_response(text: str) -> bool:
    if not text or len(text.strip()) < 4:
        return True
    if is_corporate_refusal(text):
        return True
    low = text.lower()
    if _has_spoken_timestamp(text):
        return True
    if len(text) > 320 and any(x in low for x in ("approach", "example", "function", "timestamp")):
        return True
    junk = (
        "polished version",
        "refined version",
        "feel free",
        "requested format",
        "vbnet",
        "helpdesk",
        "customer support",
    )
    return any(x in low for x in junk)


def clean_spoken(text: str) -> str:
    s = text.strip()
    s = re.sub(r"```[\s\S]*?```", "", s)
    s = re.sub(r"^Echo:\s*", "", s, flags=re.I)
    s = re.sub(r'^["\']|["\']$', "", s.strip())
    for pat in (
        r"^Got it, Brian\. Here's a (?:more )?polished version:?\s*",
        r"^Here's a refined version[^:]*:?\s*",
        r"^Here's a (?:more )?polished version:?\s*",
        r"---\s*George:.*?---\s*",
        r"Feel free to adjust[^.]*\.?",
        r"\bIf you need any[^.]*\.?",
        r"\bas an AI\b[^.]*\.?",
        r"\bI am an AI\b[^.]*\.?",
    ):
        s = re.sub(pat, "", s, flags=re.I | re.S)
    s = re.sub(r"\s+", " ", s).strip(" .`-")
    if any(x in s.lower() for x in ("requested format", "polished version", "refined version", "feel free")):
        return ""
    s = strip_spoken_timestamps(s)
    return s[:2000]


def _long_form(heard: str) -> bool:
    low = heard.lower()
    return any(
        x in low
        for x in (
            "complete",
            "full response",
            "don't cut",
            "do not cut",
            "cuts off",
            "cut off",
            "detailed",
            "whole thing",
            "entire",
            "analyze",
            "analysis",
        )
    )


def bedrock(history: list[tuple[str, str]], user: str, *, max_tokens: int | None = None) -> str:
    import boto3
    from botocore.exceptions import ClientError

    import aws_lane as al

    al._load_env()
    if max_tokens is None:
        max_tokens = 384 if _long_form(user) else 220
    region = os.environ.get("AWS_DEFAULT_REGION", "us-east-1")
    model = os.environ.get("BEDROCK_MODEL_ID", "amazon.nova-lite-v1:0")
    system = build_system()

    messages: list[dict] = []
    for u, a in history:
        if is_bad_response(a):
            continue
        messages.append({"role": "user", "content": [{"text": u}]})
        messages.append({"role": "assistant", "content": [{"text": a}]})
    tail = user.strip()
    if _long_form(user):
        tail += "\n\n(Brian wants a complete answer — do not truncate mid-sentence.)"
    if _backend_cues(user):
        tail += "\n\n(Brian wants backend — use ---george--- DADDY: line)"
    messages.append({"role": "user", "content": [{"text": tail}]})

    rt = boto3.client("bedrock-runtime", region_name=region)
    body = json.dumps(
        {
            "schemaVersion": "messages-v1",
            "system": [{"text": system}],
            "messages": messages,
            "inferenceConfig": {"maxTokens": max_tokens, "temperature": 0.38},
        }
    )
    try:
        resp = rt.invoke_model(
            modelId=model,
            body=body,
            contentType="application/json",
            accept="application/json",
        )
        raw = json.loads(resp["body"].read())
        parts = raw.get("output", {}).get("message", {}).get("content", [{}])
        return (parts[0].get("text") or "").strip()
    except ClientError as e:
        return f"[bedrock error: {e}]"


def _heard_fallback(heard: str, actions: list[str]) -> str:
    from george_chatter import fallback_reply

    low = heard.lower()
    if re.search(r"\b(our team|who(?:'s| is| are) on (?:the |our )?team|team members?)\b", low):
        from george_actions import team_roster

        return team_roster()
    if re.search(r"\b(alexa or george|is this alexa|this alexa|you alexa|like alexa|alexa\.?\s*politic)\b", low):
        return "I'm George — our front-end voice on this box. Not Alexa."
    if re.search(r"\b(sound like daddy|like daddy|be like daddy|talk like daddy|more like daddy|make you like daddy|be more like daddy)\b", low):
        return "Got it — I'll talk like Daddy: direct, crew-first, no corporate. I'm George on the mic; he builds on the back end."
    if re.search(r"\b(politics?|political|alexa[\s\.]*politics?|corporate|alexa tone|sound like alexa)\b", low):
        return "This is our home lab — I'll skip the Amazon disclaimers. Ask me anything about the crew or the ranch; I'll answer straight."
    if "front end" in low or ("back end" in low and "tell" not in low):
        return "Right — I'm front end, Daddy's back end. I'll keep it sharp."
    if "smart" in low or "stupid" in low or "robot" in low:
        return "Heard you — less robot, more human. I'm on it."
    if any(a.startswith("daddy") for a in actions) or _backend_cues(heard):
        return "Done — I pinged Daddy on the back end."
    if "store" in low:
        return "Heading out? I'll hold down the front end while you're gone."
    return fallback_reply()


def process_turn(raw: str, *, heard: str) -> tuple[str, list[str]]:
    spoken, meta = split_reply(raw)
    actions = apply_meta(meta, heard=heard) if meta else []
    if not actions and _backend_cues(heard):
        guess = heard.strip()[:200]
        _ping_daddy(guess, heard)
        actions.append(f"daddy_auto:{guess[:60]}")
    out = clean_spoken(spoken)
    if not _asks_timestamp(heard):
        out = strip_spoken_timestamps(out)
    bad = is_bad_response(out) or len(out) < 8
    if bad:
        out = _heard_fallback(heard, actions)
        _write_pref("Talk like Daddy — Brian rejected corporate/Alexa tone on this turn")
    low = heard.lower()
    if re.search(r"\b(alexa|amazon voice|corporate|politic|like daddy|sound like daddy|trashy)\b", low):
        _write_pref("Talk like Daddy — direct · crew-first · no Alexa.politics hedging")
    if "smart" in low or "stupid" in low:
        _write_pref("Sound smart not robotic — front-end voice only")
    if _long_form(heard):
        _write_pref("Complete responses — type and voice match; never cut off mid-sentence")
    return out, actions

