#!/usr/bin/env python3
"""George phone/Echo lane — front-end voice · skills · Daddy is back-end."""
from __future__ import annotations

import json
from datetime import datetime, timezone

from bus_lane import STAN, bus_root, safe_is_file, safe_mkdir, safe_read_text

SESSION = STAN / "george_echo_session.json"
MAX_TURNS = 10


def get_history() -> list[tuple[str, str]]:
    return _load_history()


def _now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def _load_history() -> list[tuple[str, str]]:
    if not SESSION.is_file():
        return []
    try:
        from george_self import is_bad_response

        data = json.loads(SESSION.read_text(encoding="utf-8"))
        clean: list[tuple[str, str]] = []
        for u, a in data.get("history", []):
            u, a = str(u), str(a)
            if is_bad_response(a):
                continue
            clean.append((u, a))
        return clean[-MAX_TURNS:]
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


def talk(user: str) -> tuple[str, dict]:
    """Returns (spoken reply, extras e.g. open_url, actions)."""
    from george_actions import last_action, try_local
    from george_self import bedrock, process_turn

    text = user.strip()
    extras: dict = {"actions": [], "open_url": None, "skill": None}
    if not text:
        from george_chatter import empty_reply

        reply = empty_reply()
        extras["skill"] = "empty"
        return reply, extras

    history = _load_history()

    local = try_local(text)
    if local:
        reply, actions, open_url = local
        extras["actions"] = actions
        extras["open_url"] = open_url
        extras["skill"] = "open" if open_url else (actions[0].split(":")[0] if actions else "local")
    else:
        raw = bedrock(history, text)
        reply, actions = process_turn(raw, heard=text)
        extras["actions"] = actions
        extras["skill"] = "chat"
        for act in actions:
            if act.startswith("open:"):
                from george_actions import _url

                path = act.split(":", 1)[1]
                extras["open_url"] = _url(path)
                extras["skill"] = "open"
                break
            if act.startswith("action:"):
                extras["skill"] = "action"

    if not reply:
        from george_chatter import empty_reply

        reply = empty_reply()

    from george_self import is_bad_response

    if not is_bad_response(reply):
        history.append((text, reply))
    _save_history(history)

    try:
        from george_memory import upgrade_from_heard

        upgrade_from_heard(user)
    except ImportError:
        pass

    bus = bus_root()
    stamp = bus / "fleet/bus/GEORGE_LAST_REPLY.txt"
    safe_mkdir(stamp.parent)
    act = ", ".join(extras.get("actions") or []) or "chat"
    stamp.write_text(
        f"GEORGE_LAST_REPLY — {_now()}\nheard={text[:200]}\nreply={reply}\nactions={act}\n",
        encoding="utf-8",
    )
    return reply, extras


def status() -> dict:
    from george_actions import _file_age_minutes, last_action

    hist = _load_history()
    last = hist[-1] if hist else ("", "")
    bus = bus_root()
    stamp = bus / "fleet/bus/GEORGE_LAST_REPLY.txt"
    daddy = safe_read_text(bus / "fleet/bus/george_to_daddy.txt")[:200] if safe_is_file(
        bus / "fleet/bus/george_to_daddy.txt"
    ) else ""
    ages = {
        "memory_min": _file_age_minutes("fleet/bus/GEORGE_MEMORY.txt"),
        "upgrade_min": _file_age_minutes("fleet/bus/GEORGE_UPGRADE_STAMP.txt"),
        "reply_min": _file_age_minutes("fleet/bus/GEORGE_LAST_REPLY.txt"),
    }
    return {
        "ok": True,
        "turns": len(hist),
        "last_heard": last[0][:120] if last[0] else "",
        "last_reply": last[1][:120] if last[1] else "",
        "stamp": safe_read_text(stamp)[:200] if safe_is_file(stamp) else "",
        "daddy_queue": daddy,
        "last_action": last_action(),
        **ages,
    }
