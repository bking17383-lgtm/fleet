#!/usr/bin/env python3
"""George natural voice — AWS Polly neural (Matthew). Fallback: None → browser TTS."""
from __future__ import annotations

import html
import os
import re
from pathlib import Path

from alexa_speech import for_aloud
from george_self import strip_spoken_timestamps

STAN = Path.home() / ".stan"
ENV = STAN / "aws_sandbox.env"
VOICE = os.environ.get("GEORGE_POLLY_VOICE", "Matthew")
ENGINE = os.environ.get("GEORGE_POLLY_ENGINE", "neural")
REGION = os.environ.get("AWS_DEFAULT_REGION", "us-east-1")


def _load_aws_env() -> None:
    if not ENV.is_file():
        return
    for ln in ENV.read_text(encoding="utf-8").splitlines():
        s = ln.strip()
        if not s or s.startswith("#") or "=" not in s:
            continue
        k, v = s.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip())


def prepare_speech(text: str, *, max_len: int = 2000) -> str:
    aloud = for_aloud(text, max_len=max_len) or text.strip()
    return strip_spoken_timestamps(aloud) or aloud


def _ssml(text: str) -> str:
    safe = html.escape(text, quote=False)
    safe = re.sub(r"\s+", " ", safe).strip()
    return (
        '<speak><prosody rate="94%" pitch="-4%">'
        f"{safe}"
        "</prosody></speak>"
    )


def synthesize_mp3(text: str) -> bytes | None:
    """Natural male voice mp3. Returns None if Polly unavailable."""
    aloud = prepare_speech(text)
    if not aloud:
        return None
    _load_aws_env()
    if not os.environ.get("AWS_ACCESS_KEY_ID"):
        return None
    try:
        import boto3

        polly = boto3.client("polly", region_name=REGION)
        for engine in (ENGINE, "standard"):
            try:
                resp = polly.synthesize_speech(
                    Text=_ssml(aloud),
                    TextType="ssml",
                    OutputFormat="mp3",
                    VoiceId=VOICE,
                    Engine=engine,
                )
                data = resp["AudioStream"].read()
                if data:
                    return data
            except Exception:
                if engine == "standard":
                    raise
                continue
    except Exception:
        return None
    return None
