#!/usr/bin/env python3
"""George — GL/Alexa-style voice memory · self-upgrades from heard lines."""
from __future__ import annotations

import re
from datetime import datetime, timezone

from bus_lane import bus_root, safe_is_file, safe_mkdir, safe_read_text

MEMORY = "fleet/bus/GEORGE_MEMORY.txt"
UPGRADE_STAMP = "fleet/bus/GEORGE_UPGRADE_STAMP.txt"
MAX_FACTS = 36
HEADER = """GEORGE MEMORY — self-upgrading · real Echo in Brian's room
Updated: {ts}

name=George
role=front-end voice · mic · Echo · phone · Daddy is back-end captain on CB2
brian=Brian
voice=real Echo speaks · smart · warm · not robotic

heard_facts:
"""


def _now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def _parse_facts(text: str) -> list[str]:
    facts: list[str] = []
    in_facts = False
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("heard_facts:"):
            in_facts = True
            continue
        if in_facts and s.startswith("- "):
            facts.append(s[2:].strip())
    return facts


def load_brief(max_chars: int = 1200) -> str:
    bus = bus_root()
    path = bus / MEMORY
    if not safe_is_file(path):
        return "name=George · brian=Brian · voice=Echo in room · learn fast from heard lines"
    return safe_read_text(path).strip()[:max_chars]


def upgrade_from_heard(text: str) -> dict:
    """Immediate self-upgrade — no ten-year wait · no tokens in learn mode."""
    msg = re.sub(r"\s+", " ", text.strip())
    if not msg or len(msg) < 3:
        return {"ok": False, "error": "empty"}

    bus = bus_root()
    path = bus / MEMORY
    safe_mkdir(path.parent)
    prior = safe_read_text(path) if safe_is_file(path) else ""
    facts = _parse_facts(prior) if prior else []
    low = msg.lower()
    if any(low in f.lower() or f.lower() in low for f in facts):
        return {"ok": True, "upgraded": False, "reason": "already known"}

    facts.append(msg[:240])
    facts = facts[-MAX_FACTS:]
    body = HEADER.format(ts=_now()) + "".join(f"  - {f}\n" for f in facts)
    path.write_text(body, encoding="utf-8")
    stamp = bus / UPGRADE_STAMP
    stamp.write_text(f"GEORGE_UPGRADE — {_now()}\nlast={msg[:200]}\nfacts={len(facts)}\n", encoding="utf-8")
    return {"ok": True, "upgraded": True, "facts": len(facts)}


def status() -> dict:
    bus = bus_root()
    path = bus / MEMORY
    facts = _parse_facts(safe_read_text(path)) if safe_is_file(path) else []
    stamp = safe_read_text(bus / UPGRADE_STAMP).strip() if safe_is_file(bus / UPGRADE_STAMP) else ""
    return {"facts": len(facts), "memory": str(path), "stamp": stamp[:200]}
