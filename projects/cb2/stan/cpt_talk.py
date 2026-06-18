#!/usr/bin/env python3
"""CPT talk — terminal AWS · fleet watch · speech · vitals to CPT.

  python3 ~/.stan/cpt_talk.py
  python3 ~/.stan/cpt_talk.py "one question"
  AWS_SPEAK=0 to disable voice

Commands: /quit · /new · /clear · /watch
"""
from __future__ import annotations

import os
import sys

import aws_lane as al
import aws_fleet_watch as afw
import aws_speech as asp

try:
    import readline  # noqa: F401
except ImportError:
    pass


def _compact_ask(line: str) -> None:
    sys.stdout.write("\033[1A\033[2K")
    sys.stdout.write(f"· {line}\n")


def _print_reply(text: str) -> None:
    sys.stdout.write("\033[36m")
    for ln in text.splitlines():
        sys.stdout.write(ln.rstrip() + "\n")
    sys.stdout.write("\033[0m\n")


def _speak(text: str) -> None:
    if os.environ.get("AWS_SPEAK", "1").strip() in ("0", "no", "off"):
        return
    method = asp.speak(text)
    if method not in ("empty", "bus-only"):
        sys.stdout.write(f"[speak:{method}]\n")


def once(msg: str) -> None:
    al._load_env()
    afw.watch_once()
    sess = al.load_session()
    reply = sess.send(msg.strip())
    _print_reply(reply)
    _speak(reply)


def repl() -> None:
    al._load_env()
    afw.watch_once()
    sess = al.load_session()
    n = len(sess.history)
    sys.stdout.write(f"aws> memory on · {n} saved turns · /new resets · /quit\n")
    while True:
        try:
            sys.stdout.write("> ")
            sys.stdout.flush()
            line = input().strip()
        except (EOFError, KeyboardInterrupt):
            sys.stdout.write("\n")
            break
        if not line:
            continue
        low = line.lower()
        if low in ("/quit", "/q", "quit", "exit"):
            break
        if low in ("/new", "/reset"):
            sess = al.TalkSession()
            sess.save()
            sys.stdout.write("(new thread — memory file cleared)\n")
            continue
        if low == "/clear":
            os.system("clear")
            continue
        if low == "/watch":
            r = afw.watch_once()
            sys.stdout.write(f"watch changed={r.get('changed')} · {len(r.get('priorities', []))} priorities\n")
            continue
        _compact_ask(line)
        try:
            reply = sess.send(line)
        except SystemExit as e:
            sys.stdout.write(f"err: {e}\n")
            break
        except Exception as e:
            sys.stdout.write(f"err: {e}\n")
            continue
        _print_reply(reply)
        _speak(reply)


def main() -> None:
    if len(sys.argv) > 1:
        once(" ".join(sys.argv[1:]))
    else:
        repl()


if __name__ == "__main__":
    main()
