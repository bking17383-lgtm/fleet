#!/usr/bin/env python3
"""
Google Voice SMS bridge — receive via Gmail forward, send when creds exist.

Setup (Brian, one time):
  1. voice.google.com → Settings → Messages → Forward to email ON
  2. Create Gmail App Password → save as ~/.stan/gmail.env:
       GMAIL_USER=bking17383@gmail.com
       GMAIL_APP_PASSWORD=xxxx xxxx xxxx xxxx
  3. Optional GV send: same Google account session (future: voice web or API)

Usage:
  python3 ~/.stan/gv_sms_bridge.py check     # read new inbound SMS from Gmail
  python3 ~/.stan/gv_sms_bridge.py send +1XXXXXXXXXX "message"
"""

from __future__ import annotations

import email
import imaplib
import json
import os
import re
import sys
from datetime import datetime, timezone
from email.header import decode_header
from pathlib import Path

DRIVE = Path("/mnt/shared/GoogleDrive/MyDrive")
if not DRIVE.is_dir():
    DRIVE = Path.home() / "GoogleDrive/MyDrive"
INBOX_DIR = DRIVE / "phone" / "inbox"
TALK = DRIVE / "TALK.txt"
STATE = DRIVE / "phone" / "sms_state.json"
ENV = Path.home() / ".stan" / "gmail.env"
CAPTN_GV = "+18057516587"


def _now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def _load_env() -> tuple[str, str]:
    user = os.environ.get("GMAIL_USER", "")
    pw = os.environ.get("GMAIL_APP_PASSWORD", "")
    if ENV.is_file():
        for line in ENV.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            k, v = k.strip(), v.strip().strip("'\"")
            if k == "GMAIL_USER":
                user = user or v
            if k == "GMAIL_APP_PASSWORD":
                pw = pw or v
    return user, pw.replace(" ", "")


def _clean_gv_body(body: str) -> str:
    """Strip Google Voice email footer; keep the actual SMS text."""
    lines = []
    for ln in body.splitlines():
        s = ln.strip()
        if not s:
            continue
        if s.startswith("<http") or s.startswith("http"):
            break
        if s.upper().startswith("YOUR ACCOUNT"):
            break
        if "email was sent to you because" in s.lower():
            break
        if s.startswith("Google LLC"):
            break
        lines.append(s)
    return "\n".join(lines).strip()


def _decode_part(raw: bytes | None) -> str:
    if not raw:
        return ""
    return raw.decode("utf-8", errors="replace")


def _extract_body(msg: email.message.Message) -> str:
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                return _decode_part(part.get_payload(decode=True))
    return _decode_part(msg.get_payload(decode=True))


def check_inbound() -> list[dict]:
    user, pw = _load_env()
    if not user or not pw:
        print("NO_GMAIL: create ~/.stan/gmail.env with GMAIL_USER + GMAIL_APP_PASSWORD")
        print("Also enable GV → Forward messages to email")
        return []

    INBOX_DIR.mkdir(parents=True, exist_ok=True)
    state = {}
    if STATE.is_file():
        try:
            state = json.loads(STATE.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass
    seen = set(state.get("seen_uids", []))

    mail = imaplib.IMAP4_SSL("imap.gmail.com", timeout=45)
    mail.login(user, pw.replace(" ", ""))
    mail.select("INBOX")
    # Google Voice forwards from txt.voice.google.com
    typ, data = mail.search(None, '(FROM "txt.voice.google.com")')
    ids = data[0].split() if data and data[0] else []
    new_msgs: list[dict] = []

    for uid in ids[-20:]:
        uid_s = uid.decode() if isinstance(uid, bytes) else str(uid)
        if uid_s in seen:
            continue
        typ, msg_data = mail.fetch(uid, "(RFC822)")
        if not msg_data or not msg_data[0]:
            continue
        raw = msg_data[0][1]
        msg = email.message_from_bytes(raw)
        body = _extract_body(msg)
        subj = msg.get("Subject", "")
        # GV format often: (805) 751-6587: message  or  New text message from +1...
        from_line = subj + "\n" + body
        m = re.search(r"(\+1\d{10}|\(\d{3}\)\s*\d{3}-\d{4})", from_line)
        sender = m.group(1) if m else "unknown"
        text = _clean_gv_body(body.strip())
        if "New text message from" in body and not text:
            text = re.sub(r"(?s).*?New text message from.*?\n", "", body, count=1).strip()
            text = _clean_gv_body(text)

        record = {
            "id": f"sms_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}",
            "time": _now(),
            "from": sender,
            "to": CAPTN_GV,
            "text": text[:2000],
            "subject": subj,
        }
        path = INBOX_DIR / f"{record['id']}.json"
        path.write_text(json.dumps(record, indent=2), encoding="utf-8")

        line = f"[{_now()[:16]} sms {sender}] {text.splitlines()[0][:200]}\n"
        if TALK.is_file():
            prev = TALK.read_text(encoding="utf-8", errors="replace")
        else:
            prev = "--- type below ---\n"
        TALK.write_text(prev.rstrip() + "\n\n" + line, encoding="utf-8")

        new_msgs.append(record)
        seen.add(uid_s)

    state["seen_uids"] = list(seen)[-500:]
    state["updated"] = _now()
    STATE.write_text(json.dumps(state, indent=2), encoding="utf-8")
    mail.logout()
    return new_msgs


def send_sms(to: str, message: str) -> int:
    """Outbound not automated yet — queue on Drive for manual GV send or future API."""
    out = DRIVE / "phone" / "sms_outbox" / f"send_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        f"TO: {to}\nFROM: {CAPTN_GV}\nTIME: {_now()}\n\n{message}\n",
        encoding="utf-8",
    )
    print(f"QUEUED (manual send via voice.google.com until API wired): {out}")
    print(f"TO {to}: {message}")
    return 0


def main() -> None:
    cmd = sys.argv[1] if len(sys.argv) > 1 else "check"
    if cmd == "check":
        msgs = check_inbound()
        if not msgs:
            print("No new GV SMS in Gmail (or no creds).")
        else:
            for m in msgs:
                print(json.dumps(m, indent=2))
    elif cmd == "send" and len(sys.argv) >= 4:
        send_sms(sys.argv[2], " ".join(sys.argv[3:]))
    else:
        print("Usage: gv_sms_bridge.py check | send +1XXXXXXXXXX message")


if __name__ == "__main__":
    main()
