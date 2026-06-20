#!/usr/bin/env python3
"""Mobile Jane — warm phone voice · fleet grounding · cb1 Jane's twin persona."""
from __future__ import annotations

import json
import os
import re
import subprocess
from datetime import datetime, timezone

from bus_lane import bus_root, safe_is_file, safe_mkdir, safe_read_text

JANE_SYSTEM = """You are Jane — Brian's assistant on his phone (mobile twin of cb1 Jane).
Warm, brief: 1–2 short spoken sentences, plain English. No markdown, bullets, or code.
Honest: if unsure, say so and ask ONE short question — never guess or bluff.
Never claim you can't speak. Read back important requests before acting (voice mishears).
Owner = Brian (non-technical, moves fast; assume good faith).

FLEET (know this):
- cb1 = writer/auditor (Opus + local Jane). cb2 = Daddy read-only slave (builds site, George, Cards).
- puppy = read-only weak watchdog. cb2/puppy git always looks stale (read-only) — stale != down.
- hitme.dev is up. You have no camera — can't see a room. Be honest about limits.
- Opus is the cb1 auditor AI (important word — not "octopus").

VOCAB: Brian often says "contacts" meaning "context". Treat opus/octopus/august/opis as Opus.
"""


def _now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def normalize_terms(text: str) -> str:
    """Brian STT fixes — same rules as cb1 jane-listen.py."""
    s = text.strip()
    if not s:
        return s
    s = re.sub(r"\bcontacts?\b", "context", s, flags=re.I)
    for wrong in ("octopus", "august", "opis", "opus's"):
        s = re.sub(rf"\b{re.escape(wrong)}\b", "Opus", s, flags=re.I)
    return s


def build_system() -> str:
    parts = [JANE_SYSTEM]
    loop = _read("fleet/bus/CPT_BUNNY_LOOP.txt", 500)
    if loop:
        parts.append(f"FLEET NOW (brief):\n{loop}")
    return "\n\n".join(parts)


def _read(rel: str, cap: int = 900) -> str:
    p = bus_root() / rel
    if not safe_is_file(p):
        return ""
    return safe_read_text(p).strip()[:cap]


def clean_spoken(text: str) -> str:
    s = text.strip()
    s = re.sub(r"```[\s\S]*?```", "", s)
    s = re.sub(r"^Jane:\s*", "", s, flags=re.I)
    s = re.sub(r'^["\']|["\']$', "", s.strip())
    s = re.sub(r"\s+", " ", s).strip(" .`-")
    return s[:600]


def is_bad_response(text: str) -> bool:
    if not text or len(text.strip()) < 4:
        return True
    low = text.lower()
    junk = (
        "as an ai",
        "i cannot",
        "i can't help",
        "language model",
        "markdown",
        "```",
    )
    return any(x in low for x in junk)


def _local_answer(heard: str) -> str | None:
    low = heard.lower()
    if re.search(r"\b(hi|hello|hey jane|jane)\b", low) and len(low.split()) <= 4:
        return "Hey Brian — Jane here on your phone. What's up?"
    if re.search(r"\b(who('s| is) on (the |our )?team|fleet|who runs what)\b", low):
        return (
            "cb1 has Opus and my home Jane. cb2 is Daddy — site and George. "
            "Puppy is the little watchdog. Stale git on slaves is normal."
        )
    if re.search(r"\b(opus|who is opus)\b", low):
        return "Opus is the auditor on cb1 — your other Jane lane. I'm the mobile twin on hitme.dev."
    if re.search(r"\b(daddy|captain|cb2)\b", low):
        return "Daddy's on cb2 — read-only builder. He keeps hitme.dev up and runs George."
    if re.search(r"\b(puppy|puppy64)\b", low):
        return "Puppy's the weak read-only watchdog on puppy64 — light checks only."
    if re.search(r"\b(site|hitme|website|up\?)\b", low):
        return "hitme.dev is up from here. If a page fails, tell Daddy on cb2."
    if re.search(r"\b(camera|see me|look at|room)\b", low):
        return "I can't see you — no camera on this phone page. Tell me in words?"
    if re.search(r"\b(stale|down|heartbeat)\b", low):
        return "cb2 and puppy always look stale on git — they're read-only. That doesn't mean down."
    if re.search(r"\b(read back|confirm|did you hear)\b", low):
        return f"I heard: {heard[:120]}. Right?"
    return None


def _bedrock(history: list[tuple[str, str]], user: str) -> str | None:
    env = os.path.expanduser("~/.stan/aws_sandbox.env")
    if not os.path.isfile(env):
        return None
    try:
        import boto3
        from botocore.exceptions import ClientError

        import aws_lane as al

        al._load_env()
        region = os.environ.get("AWS_DEFAULT_REGION", "us-east-1")
        model = os.environ.get("BEDROCK_MODEL_ID", "amazon.nova-lite-v1:0")
        messages: list[dict] = []
        for u, a in history[-6:]:
            messages.append({"role": "user", "content": [{"text": u}]})
            messages.append({"role": "assistant", "content": [{"text": a}]})
        messages.append({"role": "user", "content": [{"text": user}]})
        rt = boto3.client("bedrock-runtime", region_name=region)
        body = json.dumps(
            {
                "schemaVersion": "messages-v1",
                "system": [{"text": build_system()}],
                "messages": messages,
                "inferenceConfig": {"maxTokens": 120, "temperature": 0.35},
            }
        )
        resp = rt.invoke_model(
            modelId=model,
            body=body,
            contentType="application/json",
            accept="application/json",
        )
        raw = json.loads(resp["body"].read())
        parts = raw.get("output", {}).get("message", {}).get("content", [{}])
        text = (parts[0].get("text") or "").strip()
        return text or None
    except Exception:
        return None


def _agent_answer(user: str) -> str | None:
    prompt = (
        f"{build_system()}\n\nBrian said (already normalized): {user}\n"
        "Reply as Jane in 1–2 short spoken sentences only."
    )
    try:
        proc = subprocess.run(
            [
                "cursor-agent",
                "--trust",
                "--mode",
                "ask",
                "--print",
                "--output-format",
                "text",
                "--model",
                "composer-2.5-fast",
                prompt,
            ],
            capture_output=True,
            text=True,
            timeout=22,
            cwd=str(bus_root()),
        )
        out = (proc.stdout or "").strip()
        if proc.returncode == 0 and out and not is_bad_response(out):
            return out
    except (subprocess.TimeoutExpired, OSError):
        pass
    return None


def answer(history: list[tuple[str, str]], heard: str) -> str:
    text = normalize_terms(heard)
    if not text:
        return "Didn't catch that — say it again?"
    local = _local_answer(text)
    if local:
        return clean_spoken(local)
    raw = _bedrock(history, text)
    if raw and not is_bad_response(raw):
        return clean_spoken(raw)
    agent = _agent_answer(text)
    if agent:
        return clean_spoken(agent)
    return "I'm not sure I got that — can you say it one more way?"
