#!/usr/bin/env python3
"""
AWS lane — Bedrock talk + batch. NOT captain. NOT Echo Dot (separate Alexa API).

  python3 ~/.stan/aws_lane.py greet      # status + one-liner hello on bus
  python3 ~/.stan/aws_lane.py talk "…"  # chat → drop_pile/from_aws/
  python3 ~/.stan/aws_lane.py probe     # same as aws_sandbox_probe.py
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from bus_lane import bus_root, safe_mkdir, safe_read_text, safe_is_file, STAN, LOGS

ENV = STAN / "aws_sandbox.env"
BUS = bus_root()
CHAT_DIR = BUS / "drop_pile/from_aws"
STATUS = BUS / "fleet/bus/AWS_STATUS.txt"
VITALS = BUS / "fleet/bus/AWS_VITALS.txt"
PROBE = BUS / "fleet/bus/AWS_PROBE_REPORT.txt"
LOG = LOGS / "aws_lane.log"
SESSION_LOCAL = STAN / "aws_session.json"
SESSION_BUS = BUS / "fleet/bus/AWS_SESSION.json"
MEMORY_FILE = BUS / "fleet/bus/AWS_MEMORY.txt"
TREE_FILE = BUS / "fleet/AWS_TREE.txt"
VOICE_FILE = BUS / "fleet/AWS_VOICE.txt"
PROTOCOL_FILE = BUS / "fleet/AWS_PROTOCOL.txt"
LAW_FILE = BUS / "fleet/AWS_CHAT_LAW.txt"

AWS_SYSTEM = """AWS overflow lane. NOT CPT. See fleet/AWS_PROTOCOL.txt for reply shape."""


def _strip_comments(text: str) -> str:
    lines = []
    for ln in text.splitlines():
        s = ln.strip()
        if s.startswith("#") or s.startswith("━"):
            continue
        if not s:
            continue
        lines.append(ln.rstrip())
    return "\n".join(lines).strip()


def _load_protocols(max_chars: int = 2200) -> str:
    parts: list[str] = []
    if PROTOCOL_FILE.is_file():
        parts.append(_strip_comments(safe_read_text(PROTOCOL_FILE)))
    elif VOICE_FILE.is_file():
        parts.append(_strip_comments(safe_read_text(VOICE_FILE)))
    else:
        parts.append(AWS_SYSTEM)
    if LAW_FILE.is_file():
        law = _strip_comments(safe_read_text(LAW_FILE))
        parts.append(law[:600])
    return "\n\n".join(p for p in parts if p)[:max_chars]


def _memory_brief(max_chars: int = 800) -> str:
    if safe_is_file(MEMORY_FILE):
        return safe_read_text(MEMORY_FILE).strip()[:max_chars]
    return "brian_name=Brian · aws_role=overflow · captain=CPT"


def _tree_brief(max_chars: int = 900) -> str:
    if safe_is_file(TREE_FILE):
        return _strip_comments(safe_read_text(TREE_FILE))[:max_chars]
    return "AWS under CPT · not captain · vitals to bus"


def _identity_block() -> str:
    return (
        f"MEMORY (persistent):\n{_memory_brief()}\n\n"
        f"FLEET TREE (your place):\n{_tree_brief()}\n"
    )


def _load_voice() -> str:
    return _load_protocols()


def _system_full() -> str:
    return (
        f"{_load_voice()}\n\n{_identity_block()}\n"
        "SESSION: you have disk memory + saved turns. NEVER re-introduce. NEVER 'nice to meet you'."
    )


def _load_env() -> None:
    if not ENV.is_file():
        raise SystemExit(f"missing {ENV}")
    for line in ENV.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        os.environ.setdefault(k.strip(), v.strip())


def _fleet_brief(max_chars: int = 1600) -> str:
    bus = bus_root()
    rels = (
        "fleet/bus/PUPPY_DOWN.txt",
        "fleet/bus/CPT_FOCUS.txt",
        "fleet/bus/CPT_DELEGATE_NOW.txt",
        "fleet/bus/BRIAN_BROADCAST.txt",
        "fleet/bus/AWS_STATUS.txt",
        "fleet/bus/gem_to_cpt.txt",
        "fleet/bus/cpt_to_gem.txt",
        "fleet/bus/puppy_outbox.txt",
        "fleet/STUCK_BOARD.txt",
    )
    chunks: list[str] = []
    for rel in rels:
        p = bus / rel
        if not safe_is_file(p):
            continue
        txt = safe_read_text(p).strip()
        if not txt:
            continue
        n = 10 if rel.endswith("STUCK_BOARD.txt") else 6
        tail = "\n".join(txt.splitlines()[:n] if rel.endswith("STUCK_BOARD.txt") else txt.splitlines()[-n:])
        chunks.append(f"[{rel}]\n{tail}")
    if not chunks:
        return ""
    return "\n\n".join(chunks)[:max_chars]


def _bedrock_chat(user: str, *, bullets: bool = True, max_tokens: int = 220) -> str:
    import boto3
    from botocore.exceptions import ClientError

    region = os.environ.get("AWS_DEFAULT_REGION", "us-east-1")
    model = os.environ.get("BEDROCK_MODEL_ID", "amazon.nova-lite-v1:0")
    system = _system_full()
    if bullets:
        system += (
            "\n\nOUTPUT: exact terminal shape from protocol. "
            "Start with '- do now:'. Max 3 decision bullets. No numbered lists."
        )
    prompt = f"{system}\n\n---\nBrian:\n{user.strip()}"
    rt = boto3.client("bedrock-runtime", region_name=region)
    body = json.dumps(
        {
            "messages": [
                {
                    "role": "user",
                    "content": [{"text": prompt}],
                }
            ],
            "inferenceConfig": {"maxTokens": max_tokens, "temperature": 0.2},
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
        return (parts[0].get("text") or "").strip()[:4000]
    except ClientError as e:
        return f"[bedrock error: {e}]"


def _bedrock_session(
    history: list[tuple[str, str]],
    user: str,
    *,
    bullets: bool = True,
    echo: bool = False,
    max_tokens: int = 220,
) -> str:
    """Multi-turn — system once via first user wrap; history keeps it from resetting dumb."""
    import boto3
    from botocore.exceptions import ClientError

    region = os.environ.get("AWS_DEFAULT_REGION", "us-east-1")
    model = os.environ.get("BEDROCK_MODEL_ID", "amazon.nova-lite-v1:0")
    if echo:
        system = _strip_comments(safe_read_text(VOICE_FILE))[:900] if safe_is_file(VOICE_FILE) else AWS_SYSTEM
        try:
            from george_memory import load_brief

            system += f"\n\nGEORGE MEMORY:\n{load_brief(900)}\n"
        except ImportError:
            pass
        system += (
            "\n\nECHO SPOKEN: You are George — Brian's room assistant (beats Gem GL). "
            "Real Echo reads this aloud. Under 35 words. One short spoken answer only. "
            "No bullet list. No '- do now:'. No file paths. No fleet protocol. "
            "Never say 'Echo:' or quote yourself. Never give examples. "
            "Sound like a smart friend on speakerphone — warm, fast, a little wit. "
            "Use GEORGE MEMORY when relevant."
        )
        bullets = False
        max_tokens = min(max_tokens, 72)
    else:
        system = _system_full()
        if bullets:
            system += (
                "\n\nOUTPUT: exact terminal shape. '- do now:' first. "
                "Max 3 decisions. No intro. No numbered lists."
            )

    messages: list[dict] = []
    if not history:
        brief = "" if echo else _fleet_brief()
        snap = f"\n\nFLEET SNAPSHOT (ground truth — use this):\n{brief}\n" if brief else ""
        iden = "" if echo else _identity_block()
        messages.append(
            {
                "role": "user",
                "content": [{"text": f"{system}\n\n{iden}{snap}\n\nBrian:\n{user.strip()}"}],
            }
        )
    else:
        for u, a in history:
            messages.append({"role": "user", "content": [{"text": u}]})
            messages.append({"role": "assistant", "content": [{"text": a}]})
        tail_user = user.strip()
        if echo:
            tail_user += "\n\n(spoken Echo answer · under 50 words · no protocol · no paths)"
        else:
            tail_user += (
                f"\n\n(session memory: {_memory_brief(400)} · place: AWS under CPT not captain · "
                f"no 'as an AI' · no re-intro · use tree from MEMORY)"
            )
        messages.append({"role": "user", "content": [{"text": tail_user}]})

    if bullets and history and not echo:
        messages[-1]["content"][0]["text"] += (
            "\n\n(continue saved session · know Brian · know tree · '- do now:' · no re-intro)"
        )

    rt = boto3.client("bedrock-runtime", region_name=region)
    body = json.dumps(
        {
            "messages": messages,
            "inferenceConfig": {"maxTokens": max_tokens, "temperature": 0.2},
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
        return (parts[0].get("text") or "").strip()[:4000]
    except ClientError as e:
        return f"[bedrock error: {e}]"


class TalkSession:
    """Persistent session — survives button press · server restart · terminal reopen."""

    def __init__(self) -> None:
        self.history: list[tuple[str, str]] = []

    @classmethod
    def load(cls) -> TalkSession:
        sess = cls()
        for path in (SESSION_LOCAL, SESSION_BUS):
            if not path.is_file():
                continue
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                raw = data.get("history", [])
                sess.history = [(str(u), str(a)) for u, a in raw]
                break
            except (json.JSONDecodeError, OSError, TypeError):
                continue
        return sess

    def save(self) -> None:
        data = {
            "updated": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
            "turns": len(self.history),
            "history": self.history,
        }
        safe_mkdir(SESSION_LOCAL.parent)
        blob = json.dumps(data, indent=2) + "\n"
        SESSION_LOCAL.write_text(blob, encoding="utf-8")
        try:
            safe_mkdir(SESSION_BUS.parent)
            SESSION_BUS.write_text(blob, encoding="utf-8")
        except OSError:
            pass

    def send(self, user: str) -> str:
        reply = _bedrock_session(self.history, user.strip(), bullets=True)
        self.history.append((user.strip(), reply))
        if len(self.history) > 12:
            self.history = self.history[-12:]
        self.save()
        _vitals_for_cpt(user, reply)
        return reply

    def send_echo(self, user: str) -> str:
        """Cheap spoken shape for real Echo — no protocol dump · low tokens."""
        reply = _bedrock_session(self.history, user.strip(), bullets=False, echo=True, max_tokens=96)
        self.history.append((user.strip(), reply))
        if len(self.history) > 12:
            self.history = self.history[-12:]
        self.save()
        _vitals_for_cpt(user, reply)
        return reply


def load_session() -> TalkSession:
    return TalkSession.load()


def _log(msg: str) -> None:
    safe_mkdir(LOG.parent)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(f"{datetime.now(timezone.utc).isoformat(timespec='seconds')} {msg}\n")


def _status(ok: bool, detail: str) -> None:
    now = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
    safe_mkdir(STATUS.parent)
    STATUS.write_text(
        f"AWS_STATUS — {now}\nok={'YES' if ok else 'NO'}\n{detail}\n"
        "lane=talk+batch only · not captain · not Echo Dot\n"
        "law=fleet/AWS_CHAT_LAW.txt\n",
        encoding="utf-8",
    )


def _vitals_for_cpt(user: str, reply: str) -> None:
    """AWS lane → bus so CPT/SLAVE sees terminal talk without being captain."""
    now = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
    safe_mkdir(VITALS.parent)
    probe_ok = "?"
    if PROBE.is_file():
        probe_ok = "SANDBOX_OK" if "SANDBOX_OK" in PROBE.read_text(encoding="utf-8", errors="replace") else "check probe"
    VITALS.write_text(
        f"AWS_VITALS — {now}\n"
        f"for_captn=YES\n"
        f"probe={probe_ok}\n"
        f"last_brian={user.strip()[:240]}\n"
        f"last_aws={reply.strip()[:360]}\n"
        f"cpt_reads=fleet/bus/AWS_VITALS.txt · CPT_SLAVE.txt\n"
        f"law=overflow lane only · captain=Cursor CPT\n",
        encoding="utf-8",
    )
    _status(True, f"last_talk={now}\n{reply.strip()[:280]}")
    _log(f"vitals → {VITALS.name}")
    try:
        import aws_fleet_watch as afw

        afw.watch_once()
    except Exception:
        pass


def cmd_greet() -> None:
    _load_env()
    reply = _bedrock_chat("Say AWS_LANE_OK and one smart bullet about being talk-only.", bullets=True)
    _status(True, reply[:500])
    print(reply)


def cmd_talk(msg: str) -> None:
    if not msg.strip():
        print("usage: aws_lane.py talk \"message\"")
        return
    _load_env()
    reply = TalkSession.load().send(msg.strip())
    now = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    safe_mkdir(CHAT_DIR)
    path = CHAT_DIR / f"talk_{now}.md"
    path.write_text(
        f"# AWS talk — {now}\n\n**Brian:** {msg.strip()}\n\n**AWS:** {reply}\n",
        encoding="utf-8",
    )
    _log(f"talk {len(msg)} chars → {path.name}")
    _vitals_for_cpt(msg, reply)
    print(reply)
    print(f"\n→ {path}")


def cmd_probe() -> None:
    import subprocess
    subprocess.run([sys.executable, str(STAN / "aws_sandbox_probe.py")], check=False)


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: aws_lane.py greet|talk|probe")
        raise SystemExit(1)
    cmd = sys.argv[1].lower()
    if cmd == "greet":
        cmd_greet()
    elif cmd == "talk":
        cmd_talk(" ".join(sys.argv[2:]))
    elif cmd == "probe":
        cmd_probe()
    else:
        raise SystemExit(f"unknown: {cmd}")


if __name__ == "__main__":
    main()
