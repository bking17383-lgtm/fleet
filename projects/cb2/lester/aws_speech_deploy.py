#!/usr/bin/env python3
"""AWS speech — local TTS or phone/say.txt · Alexa gets filtered aloud text only."""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

from bus_lane import bus_root, safe_mkdir

from alexa_speech import for_aloud

SPEAK_BUS = "fleet/bus/AWS_SPEAK.txt"
SPEAK_ALOUD = "fleet/bus/AWS_SPEAK_ALOUD.txt"
SPEAK_SILENT = "fleet/bus/AWS_SPEAK_SILENT.txt"


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

    for cmd in (
        ["espeak-ng", "-s", "175", aloud],
        ["espeak", "-s", "175", aloud],
        ["spd-say", aloud],
    ):
        if _try_cmd(cmd):
            return cmd[0]

    try:
        say_path.write_text(aloud + "\n", encoding="utf-8")
        return "phone/say.txt"
    except OSError:
        return "bus-only"
