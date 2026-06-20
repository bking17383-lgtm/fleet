#!/usr/bin/env python3
"""Jane voice — Edge TTS (Amy/Jenny). Fallback: browser TTS."""
from __future__ import annotations

import asyncio
import re

from alexa_speech import for_aloud

VOICE = "en-US-JennyNeural"


def prepare_speech(text: str, *, max_len: int = 1200) -> str:
    aloud = for_aloud(text, max_len=max_len) or text.strip()
    aloud = re.sub(r"\s+", " ", aloud).strip()
    return aloud


async def _edge_mp3(text: str) -> bytes | None:
    try:
        import edge_tts
    except ImportError:
        return None
    comm = edge_tts.Communicate(text, VOICE)
    chunks: list[bytes] = []
    async for chunk in comm.stream():
        if chunk["type"] == "audio":
            chunks.append(chunk["data"])
    return b"".join(chunks) if chunks else None


def synthesize_mp3(text: str) -> bytes | None:
    aloud = prepare_speech(text)
    if not aloud:
        return None
    try:
        return asyncio.run(_edge_mp3(aloud))
    except Exception:
        return None
