#!/usr/bin/env python3
"""Alexa / Echo aloud filter — never speak directions, paths, or protocol meta."""
from __future__ import annotations

import re

# Spoken aloud (Echo / phone/say.txt / espeak). Full text stays on bus only.
_META_PREFIXES = (
    r"do now:\s*",
    r"→\s*cpt:\s*",
    r"tell captain:\s*",
    r"reply shape.*",
    r"output:.*",
    r"law:.*",
    r"session:.*",
    r"fleet snapshot.*",
)
_PATH_RE = re.compile(
    r"[`\"']?(?:~/?)?(?:fleet/|drop_pile/|lester/|phone/|\.stan/)[^\s`\"']+[`\"']?",
    re.I,
)
_FILE_RE = re.compile(r"\b[\w./-]+\.txt\b", re.I)
_PORT_STATUS = re.compile(r":(\d{3,5})=(UP|DOWN)\b", re.I)
_INSTR_ONLY = re.compile(
    r"^(?:check|read|open|look at|write|scan|post|update|see)\b.*(?:immediate tasks|for tasks|the board)?\s*$",
    re.I,
)
_SKIP_PHRASES = (
    "exactly this structure",
    "plain bullets",
    "under 70 words",
    "no intro",
    "check fleet",
    "read fleet",
    "write priorities",
    "aws protocol",
    "reply shape",
    "for immediate tasks",
    "write one short line",
    "post /api",
)


def _strip_meta_line(line: str) -> str:
    s = line.strip()
    if not s:
        return ""
    s = re.sub(r"^[-*•#>\s]+", "", s)
    for pat in _META_PREFIXES:
        s = re.sub(pat, "", s, flags=re.I)
    s = _PATH_RE.sub("", s)
    s = _FILE_RE.sub("", s)
    s = re.sub(r"\s+", " ", s).strip(" ·,-")
    return s


def _compact_status(text: str) -> str:
    """Turn protocol dumps into short answers Alexa can say fast."""
    chunks: list[str] = []
    if re.search(r"\bping\s*=\s*FAIL\b", text, re.I):
        chunks.append("Connection failed")
    down = sorted(set(_PORT_STATUS.findall(text)))
    down_ports = [p for p, st in down if st.upper() == "DOWN"]
    up_ports = [p for p, st in down if st.upper() == "UP"]
    if down_ports:
        if len(down_ports) == 1:
            chunks.append(f"Port {down_ports[0]} is down")
        else:
            joined = " and ".join(down_ports)
            chunks.append(f"Ports {joined} are down")
    if up_ports and not down_ports:
        chunks.append(f"Port {up_ports[0]} is up")
    pri = re.search(
        r"prioritize(?: fixing)?(?: ports?)?\s*([\d,\sand]+)",
        text,
        re.I,
    )
    if pri:
        ports = re.findall(r"\d{3,5}", pri.group(1))
        if ports:
            chunks.append(f"Prioritize port {' and '.join(ports)}")
    roll = re.search(r"\broll\s+is\s+([^.\n]+)", text, re.I)
    if roll:
        chunks.append(f"Roll is {roll.group(1).strip()}")
    stale = re.search(r"\bpuppy\s+stale\b", text, re.I)
    if stale and not any("puppy" in c.lower() for c in chunks):
        chunks.append("Puppy check-in is stale")
    keyboard = re.search(r"keyboard\s+needed\s+on\s+(\S+)", text, re.I)
    if keyboard:
        chunks.append(f"Keyboard needed on {keyboard.group(1)}")
    return ". ".join(chunks)


def for_aloud(text: str, max_len: int = 180) -> str:
    """What Echo should say — answers only, no self-instructions."""
    if not text or not text.strip():
        return ""

    raw = text.strip()
    compact = _compact_status(raw)
    if compact and any(
        tok in raw.lower()
        for tok in ("do now:", "tell captain:", "→ cpt:", "ping=", "=down", "=up")
    ):
        out = compact
    else:
        parts: list[str] = []
        for line in raw.splitlines():
            s = _strip_meta_line(line)
            if not s or len(s) < 3:
                continue
            low = s.lower()
            if low.startswith("captn:"):
                continue
            if any(
                x in low
                for x in _SKIP_PHRASES
                + (
                    "do now:",
                    "post vitals",
                    "fleet/bus",
                )
            ):
                continue
            if _INSTR_ONLY.match(s):
                continue
            if low in ("read", "check", "open", "write"):
                continue
            parts.append(s)
        if not parts:
            fallback = _strip_meta_line(raw.replace("\n", " "))
            low = fallback.lower()
            if fallback and not low.startswith("captn:") and not any(
                x in low for x in _SKIP_PHRASES
            ):
                parts.append(fallback)
        out = ". ".join(p for p in parts if p)
        if not out:
            return ""

    out = re.sub(r"\bping=FAIL\b", "connection failed", out, flags=re.I)
    out = re.sub(
        r"\b(DOWN|UP)\b",
        lambda m: "down" if m.group(1).upper() == "DOWN" else "up",
        out,
    )
    try:
        from george_self import strip_spoken_timestamps

        out = strip_spoken_timestamps(out)
    except ImportError:
        out = re.sub(
            r"George last touched:[^.]*\.\s*|I'll queue Daddy to check the exact changes[^.]*\.?\s*",
            "",
            out,
            flags=re.I,
        )
    out = re.sub(r"\s+", " ", out).strip()
    if len(out) > max_len:
        cut = out[: max_len - 1].rsplit(" ", 1)[0]
        out = (cut + "…") if cut else out[:max_len]
    return out


def split_bus(full: str) -> tuple[str, str]:
    """(silent_bus_text, aloud_text)"""
    aloud = for_aloud(full)
    return full.strip(), aloud
