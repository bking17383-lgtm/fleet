#!/usr/bin/env python3
"""Kids fetch mail. Never prints secrets. Never writes passwords.

Git Jane-river is always mail. Gmail IMAP only if ~/.stan/gmail.env or env exists.

  ./scripts/kids-fetch-mail.py
  ./scripts/kids-fetch-mail.py --json

Done-test: kid runs this; PASS/FAIL is the printed STATUS line + bus/jane/river/mail-last.txt
"""
from __future__ import annotations

import argparse
import imaplib
import json
import os
import socket
import sys
from datetime import datetime, timezone
from email.header import decode_header, make_header
from pathlib import Path

ROOT = Path(os.environ.get("FLEET_ROOT") or Path.home() / "fleet")
if not (ROOT / ".git").is_dir():
    ROOT = Path(__file__).resolve().parent.parent
ENV = Path.home() / ".stan" / "gmail.env"
OUT = ROOT / "bus" / "jane" / "river" / "mail-last.txt"
HEAD = ROOT / "bus" / "jane" / "river" / "HEAD.md"


def now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load_creds() -> tuple[str, str]:
    user = os.environ.get("GMAIL_USER", "")
    pw = os.environ.get("GMAIL_APP_PASSWORD", "") or os.environ.get("GMAIL_PASSWORD", "")
    if ENV.is_file():
        for line in ENV.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            k, v = k.strip(), v.strip().strip("'\"")
            if k == "GMAIL_USER":
                user = user or v
            elif k in ("GMAIL_APP_PASSWORD", "GMAIL_PASSWORD"):
                pw = pw or v
    return user.strip(), pw.replace(" ", "")


def hdr(raw: str) -> str:
    if not raw:
        return ""
    try:
        return str(make_header(decode_header(raw)))
    except Exception:
        return raw


def git_river() -> dict:
    if not HEAD.is_file():
        return {"status": "FAIL", "detail": "HEAD.md missing"}
    text = HEAD.read_text(encoding="utf-8", errors="replace")
    stamp = ""
    for line in text.splitlines():
        if line.startswith("stamp:"):
            stamp = line.split(":", 1)[1].strip()
            break
    return {"status": "PASS", "detail": stamp or "HEAD.md present", "bytes": len(text)}


def imap_reach() -> dict:
    try:
        with socket.create_connection(("imap.gmail.com", 993), timeout=10):
            return {"status": "PASS", "detail": "imap.gmail.com:993 open"}
    except OSError as exc:
        return {"status": "FAIL", "detail": type(exc).__name__}


def gmail_inbox(user: str, pw: str, limit: int = 5) -> dict:
    mail = imaplib.IMAP4_SSL("imap.gmail.com", timeout=20)
    try:
        mail.login(user, pw)
        mail.select("INBOX", readonly=True)
        typ, data = mail.search(None, "ALL")
        if typ != "OK" or not data or not data[0]:
            return {"status": "PASS", "count": 0, "subjects": []}
        ids = data[0].split()
        subjects = []
        for uid in ids[-limit:]:
            typ, fetched = mail.fetch(uid, "(BODY.PEEK[HEADER.FIELDS (FROM SUBJECT DATE)])")
            if typ != "OK" or not fetched or not fetched[0]:
                continue
            raw = fetched[0][1]
            if isinstance(raw, bytes):
                blob = raw.decode("utf-8", errors="replace")
            else:
                blob = str(raw)
            fields: dict[str, str] = {}
            key = ""
            for line in blob.splitlines():
                if not line.strip():
                    continue
                if ":" in line and not line.startswith(" ") and not line.startswith("\t"):
                    key, val = line.split(":", 1)
                    fields[key.title()] = val.strip()
                elif key:
                    fields[key] = (fields.get(key, "") + " " + line.strip()).strip()
            subjects.append(
                {
                    "from": hdr(fields.get("From", ""))[:80],
                    "subject": hdr(fields.get("Subject", ""))[:80] or "(no subject)",
                    "date": fields.get("Date", "")[:40],
                }
            )
        return {"status": "PASS", "count": len(ids), "subjects": subjects}
    except imaplib.IMAP4.error as exc:
        return {"status": "FAIL-IMAP", "detail": "login/select rejected", "err": type(exc).__name__}
    finally:
        try:
            mail.logout()
        except Exception:
            pass


def write_report(report: dict) -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    gmail = report["gmail"]
    lines = [
        f"KIDS-MAIL TEST  as_of={report['as_of']}  by={report['by']}",
        f"STATUS: {report['status']}",
        f"git_river: {report['git_river']['status']}  {report['git_river'].get('detail', '')}",
        f"gmail_reach: {report['gmail_reach']['status']}  {report['gmail_reach'].get('detail', '')}",
        f"gmail_inbox: {gmail['status']}"
        + (f"  n={gmail['count']}" if "count" in gmail else "")
        + (f"  {gmail.get('detail', '')}" if gmail.get("detail") else ""),
        "subjects:",
    ]
    for row in gmail.get("subjects") or []:
        lines.append(f"  - {row.get('date', '')} | {row.get('from', '')} | {row.get('subject', '')}")
    if not gmail.get("subjects"):
        lines.append("  (none)")
    lines.append("secrets: never written")
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    user, pw = load_creds()
    git = git_river()
    reach = imap_reach()
    if not user or not pw:
        gmail: dict = {
            "status": "FAIL-NO-CREDS",
            "detail": "no ~/.stan/gmail.env and no GMAIL_* env (do not paste password in chat)",
        }
    elif reach["status"] != "PASS":
        gmail = {"status": "FAIL-REACH", "detail": reach.get("detail", "")}
    else:
        gmail = gmail_inbox(user, pw)

    # Overall: kids path is green if git river works AND the script ran.
    # Gmail is a separate line — do not false-green inbox without IMAP proof.
    overall = "PASS" if git["status"] == "PASS" and gmail["status"] == "PASS" else "PARTIAL"
    if git["status"] != "PASS":
        overall = "FAIL"
    if gmail["status"] == "FAIL-IMAP":
        overall = "FAIL"

    report = {
        "as_of": now(),
        "by": "kids",
        "status": overall,
        "git_river": git,
        "gmail_reach": reach,
        "gmail_inbox": gmail,
        "gmail": gmail,
    }
    write_report(report)
    if args.json:
        print(json.dumps({k: v for k, v in report.items() if k != "gmail"}, indent=2))
    else:
        print(OUT.read_text(encoding="utf-8"), end="")
    return 0 if overall == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
