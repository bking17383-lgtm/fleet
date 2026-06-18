#!/usr/bin/env python3
"""AWS speech — local TTS or phone/say.txt · Alexa gets filtered aloud text only."""
from __future__ import annotations

import os
import subprocess

from bus_lane import bus_root, safe_is_file, safe_mkdir

from alexa_speech import for_aloud
from alexa_queue import queue_aloud, status as queue_status

SPEAK_BUS = "fleet/bus/AWS_SPEAK.txt"
SPEAK_ALOUD = "fleet/bus/AWS_SPEAK_ALOUD.txt"
SPEAK_SILENT = "fleet/bus/AWS_SPEAK_SILENT.txt"
REAL_ALEXA_MARKERS = (
    "fleet/bus/REAL_ALEXA.txt",
    "fleet/REAL_ALEXA.txt",
)


def real_alexa() -> bool:
    """Physical Echo in room — write say.txt only; never CB2 espeak."""
    if os.environ.get("REAL_ALEXA", "").strip() in ("1", "yes", "true", "on"):
        return True
    bus = bus_root()
    return any(safe_is_file(bus / rel) for rel in REAL_ALEXA_MARKERS)


def _plain(text: str) -> str:
    """Legacy strip — prefer for_aloud()."""
    return for_aloud(text)


def _try_cmd(args: list[str]) -> bool:
    try:
        subprocess.run(args, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=45)
        return True
    except (OSError, subprocess.SubprocessError):
        return False


def speak(text: str) -> str:
    """Speak answer only. Returns method used or 'text-only'."""
    full = text.strip()
    aloud = for_aloud(full)
    if not aloud:
        return "empty"

    bus = bus_root()
    say_path = bus / "phone/say.txt"
    bus_speak = bus / SPEAK_BUS
    bus_aloud = bus / SPEAK_ALOUD
    bus_silent = bus / SPEAK_SILENT
    safe_mkdir(say_path.parent)
    safe_mkdir(bus_speak.parent)

    # Bus keeps full reply; Echo/phone get aloud-only
    bus_speak.write_text(full + "\n", encoding="utf-8")
    bus_aloud.write_text(aloud + "\n", encoding="utf-8")
    if full != aloud:
        bus_silent.write_text(
            f"(directions not spoken)\n{full}\n",
            encoding="utf-8",
        )

    seq, queued = queue_aloud(aloud)
    cur = queue_status()
    if not queued and not cur["pending"]:
        return "unchanged"

    if real_alexa():
        return f"echo/say.txt#{seq}"

    for cmd in (
        ["espeak-ng", "-v", "en-us+m3", "-s", "158", "-p", "42", aloud],
        ["espeak-ng", "-v", "en+m3", "-s", "158", "-p", "42", aloud],
        ["espeak-ng", "-s", "158", "-p", "40", aloud],
        ["espeak", "-s", "158", "-p", "40", aloud],
        ["spd-say", aloud],
    ):
        if _try_cmd(cmd):
            return cmd[0]

    return f"phone/say.txt#{seq}"
