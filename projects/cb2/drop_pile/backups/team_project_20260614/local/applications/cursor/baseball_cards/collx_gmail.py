"""Optional Gmail IMAP pull for CollX CSV attachments."""

from __future__ import annotations

import email
import imaplib
import os
from email.header import decode_header
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any

from collx_data import (
    CANONICAL_PATH,
    COLLX_CURRENT,
    ensure_inbox_layout,
    load_catalog,
    load_collx_expected,
    preview_csv_text,
)


def _decode_header(value: str | None) -> str:
    if not value:
        return ""
    parts = decode_header(value)
    out: list[str] = []
    for chunk, enc in parts:
        if isinstance(chunk, bytes):
            out.append(chunk.decode(enc or "utf-8", errors="replace"))
        else:
            out.append(str(chunk))
    return "".join(out)


def _gmail_creds() -> tuple[str, str] | None:
    user = (
        os.environ.get("GMAIL_USER")
        or os.environ.get("STAN_GMAIL_USER")
        or "bking17383@gmail.com"
    ).strip()
    password = (
        os.environ.get("GMAIL_APP_PASSWORD")
        or os.environ.get("STAN_GMAIL_APP_PASSWORD")
        or ""
    ).strip()
    if not user or not password:
        return None
    return user, password


def _should_skip_partial_csv(preview: dict[str, Any]) -> tuple[bool, str]:
    """Don't overwrite canonical with a smaller partial export."""
    expected = load_collx_expected()
    exp_items = expected.get("items")
    rows = int(preview.get("rows") or 0)
    catalog_len = len(load_catalog())
    if not exp_items or rows >= exp_items - 15:
        return False, ""
    if rows > catalog_len:
        return False, ""
    return True, (
        f"CSV has {rows} rows vs ~{exp_items} expected — not replacing canonical (audit)."
    )


def audit_collx_emails(max_messages: int = 25) -> dict[str, Any]:
    """Audit CollX email attachments — row counts only, no import (for puppy GIGO check)."""
    creds = _gmail_creds()
    if not creds:
        return {
            "status": "skipped",
            "message": "Gmail not configured (~/.stan/gmail.env GMAIL_APP_PASSWORD)",
            "emails": [],
        }

    user, password = creds
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com", timeout=45)
        mail.login(user, password)
        mail.select("INBOX")
        typ, data = mail.search(
            None,
            "(OR SUBJECT \"CollX\" SUBJECT \"collection\" SUBJECT \"export\" FROM \"collx\")",
        )
        if typ != "OK" or not data or not data[0]:
            mail.logout()
            return {"status": "ok", "message": "No CollX-related emails in INBOX", "emails": []}

        msg_ids = data[0].split()
        emails: list[dict[str, Any]] = []
        best_attachment: dict[str, Any] | None = None

        for msg_id in reversed(msg_ids[-max_messages:]):
            typ, msg_data = mail.fetch(msg_id, "(RFC822)")
            if typ != "OK" or not msg_data or not msg_data[0]:
                continue
            raw = msg_data[0][1]
            if not isinstance(raw, bytes):
                continue
            msg = email.message_from_bytes(raw)
            subject = _decode_header(msg.get("Subject"))
            date_raw = msg.get("Date")
            try:
                date_iso = (
                    parsedate_to_datetime(date_raw).isoformat() if date_raw else ""
                )
            except (TypeError, ValueError):
                date_iso = str(date_raw or "")

            attachments: list[dict[str, Any]] = []
            for part in msg.walk():
                if part.get_content_maintype() == "multipart":
                    continue
                filename = _decode_header(part.get_filename())
                if not filename or not filename.lower().endswith(".csv"):
                    continue
                payload = part.get_payload(decode=True)
                if not payload or len(payload) < 50:
                    continue
                text = payload.decode("utf-8", errors="replace")
                preview = preview_csv_text(text)
                att = {
                    "filename": filename,
                    "size_bytes": len(payload),
                    "rows": preview.get("rows", 0),
                    "skipped_rows": preview.get("skipped", 0),
                    "total_mid": preview.get("total_mid", 0),
                    "preview_error": preview.get("error"),
                }
                attachments.append(att)
                if not best_attachment or att.get("rows", 0) > best_attachment.get("rows", 0):
                    best_attachment = {**att, "subject": subject, "date": date_iso}

            if attachments:
                emails.append(
                    {
                        "subject": subject,
                        "date": date_iso,
                        "attachments": attachments,
                    }
                )

        mail.logout()
        return {
            "status": "ok",
            "email_count": len(emails),
            "emails": emails,
            "best_attachment": best_attachment,
        }
    except imaplib.IMAP4.error as exc:
        return {"status": "error", "message": f"Gmail login failed: {exc}", "emails": []}
    except OSError as exc:
        return {"status": "error", "message": f"Gmail audit failed: {exc}", "emails": []}


def pull_collx_csv_from_gmail() -> dict[str, Any]:
    """Fetch latest CollX CSV attachment into inbox/current/collx_export.csv."""
    creds = _gmail_creds()
    if not creds:
        return {
            "status": "skipped",
            "message": "Gmail auto-pull not configured. Set GMAIL_APP_PASSWORD in ~/.stan/gmail.env",
        }

    user, password = creds
    ensure_inbox_layout()

    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com", timeout=30)
        mail.login(user, password)
        mail.select("INBOX")
        typ, data = mail.search(
            None,
            "(OR SUBJECT \"CollX\" SUBJECT \"collection\" FROM \"collx\")",
        )
        if typ != "OK" or not data or not data[0]:
            mail.logout()
            return {"status": "skipped", "message": "No CollX emails found"}

        msg_ids = data[0].split()
        saved: Path | None = None
        saved_preview: dict[str, Any] | None = None
        for msg_id in reversed(msg_ids[-15:]):
            typ, msg_data = mail.fetch(msg_id, "(RFC822)")
            if typ != "OK" or not msg_data or not msg_data[0]:
                continue
            raw = msg_data[0][1]
            if not isinstance(raw, bytes):
                continue
            msg = email.message_from_bytes(raw)
            subject = _decode_header(msg.get("Subject"))
            if "collx" not in subject.lower() and "export" not in subject.lower():
                continue
            for part in msg.walk():
                if part.get_content_maintype() == "multipart":
                    continue
                filename = _decode_header(part.get_filename())
                if not filename or not filename.lower().endswith(".csv"):
                    continue
                payload = part.get_payload(decode=True)
                if not payload or len(payload) < 50:
                    continue
                text = payload.decode("utf-8", errors="replace")
                preview = preview_csv_text(text)
                skip, reason = _should_skip_partial_csv(preview)
                if skip:
                    mail.logout()
                    return {
                        "status": "skipped",
                        "message": reason,
                        "preview": preview,
                        "subject": subject,
                        "filename": filename,
                    }
                COLLX_CURRENT.mkdir(parents=True, exist_ok=True)
                CANONICAL_PATH.write_bytes(payload)
                saved = CANONICAL_PATH
                saved_preview = preview
                break
            if saved:
                break
        mail.logout()
        if saved:
            return {
                "status": "ok",
                "message": "Pulled CollX CSV from Gmail",
                "path": str(saved),
                "size_bytes": saved.stat().st_size,
                "preview": saved_preview,
            }
        return {"status": "skipped", "message": "CollX emails found but no CSV attachment"}
    except imaplib.IMAP4.error as exc:
        return {"status": "error", "message": f"Gmail login failed: {exc}"}
    except OSError as exc:
        return {"status": "error", "message": f"Gmail fetch failed: {exc}"}
