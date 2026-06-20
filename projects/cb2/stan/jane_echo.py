#!/usr/bin/env python3
"""Jane phone lane — session + talk."""
from __future__ import annotations

import json
from datetime import datetime, timezone

from bus_lane import STAN, bus_root, safe_mkdir

SESSION = STAN / "jane_echo_session.json"
MAX_TURNS = 8


def _now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def _load_history() -> list[tuple[str, str]]:
    if not SESSION.is_file():
        return []
    try:
        data = json.loads(SESSION.read_text(encoding="utf-8"))
        return [(str(u), str(a)) for u, a in data.get("history", [])][-MAX_TURNS:]
    except (json.JSONDecodeError, OSError, TypeError):
        return []


def _save_history(history: list[tuple[str, str]]) -> None:
    safe_mkdir(SESSION.parent)
    SESSION.write_text(
        json.dumps(
            {"updated": _now(), "turns": len(history), "history": history[-MAX_TURNS:]},
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def get_history() -> list[tuple[str, str]]:
    return _load_history()


def talk(user: str) -> tuple[str, dict]:
    from jane_self import answer, normalize_terms

    text = normalize_terms(user.strip())
    extras: dict = {"actions": [], "open_url": None, "skill": "chat"}
    if not text:
        return "Say that again?", {**extras, "skill": "empty"}

    history = _load_history()
    reply = answer(history, text)
    history.append((text, reply))
    _save_history(history)

    bus = bus_root()
    stamp = bus / "fleet/bus/JANE_LAST_REPLY.txt"
    safe_mkdir(stamp.parent)
    stamp.write_text(
        f"JANE_LAST_REPLY — {_now()}\nheard={text[:200]}\nreply={reply}\n",
        encoding="utf-8",
    )
    return reply, extras


def status() -> dict:
    hist = _load_history()
    return {"agent": "jane", "turns": len(hist), "updated": _now()}
