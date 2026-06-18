#!/usr/bin/env python3
"""Pull audit reply email from tpgoround@gmail.com → bus verdict file."""
from __future__ import annotations

import email
import imaplib
import os
import re
import sys
from datetime import datetime, timezone
from email.header import decode_header
from pathlib import Path

STAN = Path.home() / ".stan"
ENV = STAN / "gmail.env"
DRIVE = Path("/mnt/shared/GoogleDrive/MyDrive")
if not DRIVE.is_dir():
    DRIVE = Path.home() / "GoogleDrive/MyDrive"

AUDIT_FROM = "tpgoround@gmail.com"
INBOX_DIR = DRIVE / "drop_pile/eatme/audit_inbox"
VERDICT = DRIVE / "fleet/bus/FRESH_CURSOR_VERDICT.txt"
STATE = STAN / "audit_email_state.json"


def _now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def _load_env() -> tuple[str, str]:
    user = os.environ.get("GMAIL_USER", "")
    pw = os.environ.get("GMAIL_APP_PASSWORD", "").replace(" ", "")
    if ENV.is_file():
        for line in ENV.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            if k == "GMAIL_USER":
                user = v.strip()
            elif k == "GMAIL_APP_PASSWORD":
                pw = v.strip().replace(" ", "")
    if not user or not pw:
        raise SystemExit("Missing ~/.stan/gmail.env")
    return user, pw


def _hdr(msg: email.message.Message, name: str) -> str:
    raw = msg.get(name, "") or ""
    parts = decode_header(raw)
    out = ""
    for p, enc in parts:
        out += p.decode(enc or "utf-8", errors="replace") if isinstance(p, bytes) else p
    return out.strip()


def _body_text(msg: email.message.Message) -> str:
    chunks: list[str] = []
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_maintype() == "multipart":
                continue
            if part.get_content_type() == "text/plain":
                payload = part.get_payload(decode=True)
                if payload:
                    chunks.append(payload.decode(part.get_content_charset() or "utf-8", errors="replace"))
    else:
        payload = msg.get_payload(decode=True)
        if payload:
            chunks.append(payload.decode(msg.get_content_charset() or "utf-8", errors="replace"))
    return "\n".join(chunks).strip()


def _load_state() -> set[str]:
    if not STATE.is_file():
        return set()
    import json

    try:
        data = json.loads(STATE.read_text(encoding="utf-8"))
        return set(data.get("seen_ids", []))
    except (OSError, json.JSONDecodeError):
        return set()


def _save_state(seen: set[str]) -> None:
    import json

    STATE.write_text(
        json.dumps({"seen_ids": sorted(seen)[-200:], "updated": _now()}, indent=2),
        encoding="utf-8",
    )


def _is_audit(msg: email.message.Message) -> bool:
    frm = _hdr(msg, "From").lower()
    sub = _hdr(msg, "Subject").lower()
    # only inbound from auditor account — not our own outbound eatme sends
    if AUDIT_FROM.split("@")[0] not in frm and AUDIT_FROM not in frm:
        return False
    return True


def check(save: bool = True) -> int:
    user, pw = _load_env()
    seen = _load_state()
    INBOX_DIR.mkdir(parents=True, exist_ok=True)

    mail = imaplib.IMAP4_SSL("imap.gmail.com", timeout=45)
    mail.login(user, pw)
    mail.select("INBOX")
    _, data = mail.search(None, "ALL")
    ids = data[0].split()[-40:]
    new_hits: list[tuple[str, email.message.Message]] = []

    for mid in ids:
        mid_s = mid.decode()
        if mid_s in seen:
            continue
        _, md = mail.fetch(mid, "(RFC822)")
        msg = email.message_from_bytes(md[0][1])
        if _is_audit(msg):
            new_hits.append((mid_s, msg))
    mail.logout()

    if not new_hits:
        print(f"NO_AUDIT_EMAIL — watching {user} for {AUDIT_FROM} · {_now()}")
        return 1

    for mid_s, msg in new_hits:
        seen.add(mid_s)
        frm = _hdr(msg, "From")
        sub = _hdr(msg, "Subject")
        body = _body_text(msg)
        stamp = re.sub(r"[^0-9T-]", "", _now())[:19]
        raw_path = INBOX_DIR / f"audit_{stamp}_{mid_s}.txt"
        block = "\n".join(
            [
                f"AUDIT EMAIL — {_now()}",
                f"from: {frm}",
                f"subject: {sub}",
                f"imap_id: {mid_s}",
                "---",
                body or "(empty body)",
            ]
        )
        if save:
            raw_path.write_text(block, encoding="utf-8")
            # verdict file if looks like one
            low = (sub + body).lower()
            if any(w in low for w in ("verdict", "pass", "fail", "hold", "audit")):
                VERDICT.write_text(
                    "\n".join(
                        [
                            f"FRESH CURSOR VERDICT — via email — {_now()}",
                            f"from: {frm}",
                            f"subject: {sub}",
                            "---",
                            body or "(empty)",
                        ]
                    ),
                    encoding="utf-8",
                )
                print(f"VERDICT saved → {VERDICT}")
            print(f"RAW saved → {raw_path}")
        print(f"HIT from={frm[:60]} subj={sub[:70]}")

    if save:
        _save_state(seen)
    return 0


if __name__ == "__main__":
    save = "--dry" not in sys.argv
    raise SystemExit(check(save=save))
