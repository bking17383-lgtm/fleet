#!/usr/bin/env python3
"""Send audit pack as plain .txt + URLs + sha256 — no RTF."""
from __future__ import annotations

import hashlib
import os
import smtplib
import sys
from datetime import datetime, timezone
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

STAN = Path.home() / ".stan"
ENV = STAN / "gmail.env"
DRIVE = Path("/mnt/shared/GoogleDrive/MyDrive")
EATME = DRIVE / "drop_pile/eatme"

FILES = [
    ("farthead.txt", EATME / "open/FARTHEAD.txt", "drop_pile/eatme/open/FARTHEAD.txt"),
    ("EATME.txt", EATME / "EATME.txt", "drop_pile/eatme/EATME.txt"),
    ("APPEND_LAST.txt", EATME / "open/APPEND_LAST.txt", "drop_pile/eatme/open/APPEND_LAST.txt"),
    ("FRESH_CURSOR_BOOT.txt", EATME / "open/FRESH_CURSOR_BOOT.txt", "drop_pile/eatme/open/FRESH_CURSOR_BOOT.txt"),
    ("LOYALTY_HINT.txt", EATME / "open/LOYALTY_HINT.txt", "drop_pile/eatme/open/LOYALTY_HINT.txt"),
]

MISSING = ["bigbutt.txt (sealed outsider — not on fleet fuse yet)", "lickface.txt (sealed Bunny — not on fleet fuse yet)"]


def _find_lickface() -> Path | None:
    for root in (
        EATME / "sealed",
        DRIVE / "drop_pile/auditor_inbox/SEALED",
        DRIVE / "drop_pile",
        DRIVE / "drop_pile/from_bbbunny",
    ):
        if not root.is_dir():
            continue
        for p in root.rglob("*") if root != DRIVE / "drop_pile" else []:
            if p.is_file() and "lickface" in p.name.lower() and not p.name.endswith("_SEALED.txt"):
                return p
        for p in root.iterdir() if root.is_dir() else []:
            if p.is_file() and "lickface" in p.name.lower():
                return p
    return None


def send_one_lickface(to: str) -> int:
    src = _find_lickface()
    if src is None:
        print("NO_LICKFACE — not on fuse · Bunny must post drop_pile/eatme/sealed/lickface.txt")
        return 2
    user, pw = _load_env()
    nbytes, sha = _sha(src)
    body = "\n".join(
        [
            f"LICKFACE — Bunny proposal — plain TXT — {_now()}",
            f"bytes: {nbytes}",
            f"sha256: {sha}",
            f"source: {src.relative_to(DRIVE) if src.is_relative_to(DRIVE) else src}",
            f"url: https://hitme.dev/f/{src.relative_to(DRIVE) if src.is_relative_to(DRIVE) else ''}",
            "",
            "Sealed Bunny proposal for auditor ~/audit/",
        ]
    )
    msg = MIMEMultipart()
    msg["From"] = user
    msg["To"] = to
    msg["Subject"] = "lickface — Bunny proposal (plain TXT)"
    msg.attach(MIMEText(body, "plain", "utf-8"))
    part = MIMEBase("text", "plain")
    part.set_payload(src.read_bytes())
    encoders.encode_base64(part)
    part.add_header("Content-Disposition", 'attachment; filename="lickface.txt"')
    msg.attach(part)
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=60) as smtp:
        smtp.login(user, pw)
        smtp.sendmail(user, [to], msg.as_string())
    print(f"OK lickface → {to} · {nbytes} bytes · {sha[:16]}...")
    return 0


def _now() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def _load_env() -> tuple[str, str]:
    user = pw = ""
    if ENV.is_file():
        for line in ENV.read_text(encoding="utf-8").splitlines():
            if line.startswith("GMAIL_USER="):
                user = line.split("=", 1)[1].strip()
            elif line.startswith("GMAIL_APP_PASSWORD="):
                pw = line.split("=", 1)[1].strip().replace(" ", "")
    if not user or not pw:
        raise SystemExit("Missing ~/.stan/gmail.env")
    return user, pw


def _sha(p: Path) -> tuple[int, str]:
    data = p.read_bytes()
    return len(data), hashlib.sha256(data).hexdigest()


def send(to: str) -> int:
    user, pw = _load_env()
    now = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
    lines = [
        f"AUDIT DELIVERY — plain TXT — {now}",
        "",
        "Method: (1) attachments below  (2) hitme.dev URLs  (3) curl on your box",
        "",
        "RTF failed to open — sending plain .txt instead (read as text = same content).",
        "",
        "CANONICAL (fleet side): drop_pile/eatme/",
        "Your ~/audit/ as single truth on your box = good · we will not edit after send.",
        "",
        "--- FILES (name · bytes · sha256 · URL) ---",
    ]
    attachments: list[tuple[str, Path]] = []
    for out_name, path, rel in FILES:
        if not path.is_file():
            lines.append(f"  SKIP missing: {out_name}")
            continue
        nbytes, sha = _sha(path)
        url = f"https://hitme.dev/f/{rel}"
        lines.append(f"  {out_name} · {nbytes} · {sha}")
        lines.append(f"    {url}")
        attachments.append((out_name, path))

    lines.extend(["", "--- NOT SENT YET ---"])
    for m in MISSING:
        lines.append(f"  · {m}")

    lines.extend(
        [
            "",
            "CURL example (on your isolated box):",
            "  curl -fsSL 'https://hitme.dev/f/drop_pile/eatme/open/FARTHEAD.txt' -o proposal-a.txt",
            "",
            "When verdict ready: reply subject VERDICT · or PASS/FAIL + APPEND_LAST A8 answers.",
            "",
            "Word: EATME · TXT · URL · AUDIT",
        ]
    )
    body = "\n".join(lines)

    msg = MIMEMultipart()
    msg["From"] = user
    msg["To"] = to
    msg["Subject"] = "RE: audit — delivery: plain TXT + URLs (RTF substitute)"
    msg.attach(MIMEText(body, "plain", "utf-8"))

    for fn, path in attachments:
        part = MIMEBase("text", "plain")
        part.set_payload(path.read_bytes())
        encoders.encode_base64(part)
        part.add_header("Content-Disposition", f'attachment; filename="{fn}"')
        msg.attach(part)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=60) as smtp:
        smtp.login(user, pw)
        smtp.sendmail(user, [to], msg.as_string())

    print(f"OK → {to} · {len(attachments)} txt attachments")
    return 0


if __name__ == "__main__":
    args = sys.argv[1:]
    if "--only" in args and "lickface" in args:
        dest = "tpgoround@gmail.com"
        for a in args:
            if "@" in a:
                dest = a
        raise SystemExit(send_one_lickface(dest))
    dest = args[0] if args and not args[0].startswith("-") else "tpgoround@gmail.com"
    raise SystemExit(send(dest))
