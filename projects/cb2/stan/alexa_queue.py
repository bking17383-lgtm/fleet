#!/usr/bin/env python3
"""Alexa say queue — seq/ack so Echo does not repeat the same line."""
from __future__ import annotations

from bus_lane import bus_root, safe_is_file, safe_mkdir, safe_read_text

SAY_SEQ = "phone/say_seq.txt"
SAY_ACK = "phone/say_ack.txt"
SAY_LAST = "phone/say_last.txt"
IDLE = "(George heard — mic open for next)"


def _read_int(path, default: int = 0) -> int:
    if not safe_is_file(path):
        return default
    try:
        return int(safe_read_text(path).strip() or default)
    except ValueError:
        return default


def _write_int(path, value: int) -> None:
    safe_mkdir(path.parent)
    path.write_text(f"{value}\n", encoding="utf-8")


def status() -> dict:
    bus = bus_root()
    say_path = bus / "phone/say.txt"
    seq = _read_int(bus / SAY_SEQ)
    ack = _read_int(bus / SAY_ACK)
    aloud = safe_read_text(say_path).strip() if safe_is_file(say_path) else ""
    if aloud == IDLE:
        aloud = ""
    return {
        "seq": seq,
        "ack": ack,
        "pending": seq > ack and bool(aloud),
        "aloud": aloud,
    }


def queue_aloud(aloud: str, *, force: bool = False) -> tuple[int, bool]:
    """Queue filtered text. Returns (seq, queued_new)."""
    aloud = aloud.strip()
    if not aloud:
        return status()["seq"], False

    bus = bus_root()
    say_path = bus / "phone/say.txt"
    seq_path = bus / SAY_SEQ
    cur = status()

    if not force:
        if aloud == cur["aloud"] and cur["pending"]:
            return cur["seq"], False
        last = safe_read_text(bus / SAY_LAST).strip() if safe_is_file(bus / SAY_LAST) else ""
        if aloud == last and not cur["pending"]:
            return cur["seq"], False

    seq = cur["seq"] + 1
    safe_mkdir(say_path.parent)
    say_path.write_text(aloud + "\n", encoding="utf-8")
    _write_int(seq_path, seq)
    return seq, True


def set_idle() -> dict:
    """Mark current line heard and clear queue (stops repeat loops)."""
    bus = bus_root()
    say_path = bus / "phone/say.txt"
    seq_path = bus / SAY_SEQ
    ack_path = bus / SAY_ACK
    aloud = safe_read_text(say_path).strip() if safe_is_file(say_path) else ""
    seq = _read_int(seq_path)
    if aloud and aloud != IDLE:
        if seq <= 0:
            seq = 1
        safe_mkdir((bus / SAY_LAST).parent)
        (bus / SAY_LAST).write_text(aloud + "\n", encoding="utf-8")
        _write_int(seq_path, seq)
    if seq <= 0:
        seq = 1
        _write_int(seq_path, seq)
    _write_int(ack_path, seq)
    say_path.write_text(IDLE + "\n", encoding="utf-8")
    return status()


def ack(seq: int | None = None) -> dict:
    bus = bus_root()
    seq_path = bus / SAY_SEQ
    ack_path = bus / SAY_ACK
    say_path = bus / "phone/say.txt"
    current_seq = _read_int(seq_path)
    target = current_seq if seq is None else int(seq)
    if target <= 0:
        target = current_seq
    _write_int(ack_path, target)
    aloud = safe_read_text(say_path).strip() if safe_is_file(say_path) else ""
    if aloud and aloud != IDLE:
        safe_mkdir((bus / SAY_LAST).parent)
        (bus / SAY_LAST).write_text(aloud + "\n", encoding="utf-8")
        say_path.write_text(IDLE + "\n", encoding="utf-8")
    return status()
