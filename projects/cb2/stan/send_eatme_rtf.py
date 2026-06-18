#!/usr/bin/env python3
"""Convert eatme proposal txt → RTF · email to Brian for auditor handoff."""
from __future__ import annotations

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
if not DRIVE.is_dir():
    DRIVE = Path.home() / "GoogleDrive/MyDrive"
EATME = DRIVE / "drop_pile/eatme"
OUT = EATME / "email_out"

# name → search roots (first match wins)
PACK = {
    "farthead": [
        EATME / "open/FARTHEAD.txt",
        DRIVE / "fleet/FARTHEAD.txt",
    ],
    "bigbutt": [
        EATME / "sealed",
        DRIVE / "drop_pile/auditor_inbox/SEALED",
        DRIVE / "drop_pile",
    ],
    "lickface": [
        EATME / "sealed",
        DRIVE / "drop_pile/auditor_inbox/SEALED",
        DRIVE / "drop_pile",
    ],
}


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
        raise SystemExit("Missing GMAIL_USER / GMAIL_APP_PASSWORD in ~/.stan/gmail.env")
    return user, pw


def _rtf_escape(text: str) -> str:
    out: list[str] = []
    for ch in text:
        o = ord(ch)
        if ch == "\\":
            out.append("\\\\")
        elif ch == "{":
            out.append("\\{")
        elif ch == "}":
            out.append("\\}")
        elif ch == "\n":
            out.append("\\par\n")
        elif ch == "\r":
            continue
        elif ch == "\t":
            out.append("\\tab ")
        elif o < 128:
            out.append(ch)
        else:
            out.append(f"\\u{o}?")
    return "".join(out)


def txt_to_rtf(src: Path, dst: Path) -> None:
    text = src.read_text(encoding="utf-8", errors="replace")
    body = _rtf_escape(text)
    rtf = (
        "{\\rtf1\\ansi\\deff0\n"
        "{\\fonttbl{\\f0\\fmodern Courier New;}}\n"
        "\\f0\\fs22\n"
        f"{body}\n"
        "}"
    )
    dst.write_text(rtf, encoding="utf-8")


def _shallow_find(root: Path, pat: str, maxdepth: int = 4) -> Path | None:
    if not root.is_dir():
        return None
    for dirpath, dirnames, filenames in os.walk(root):
        rel = Path(dirpath).relative_to(root)
        if len(rel.parts) >= maxdepth:
            dirnames.clear()
            continue
        for fn in filenames:
            if pat in fn.lower() and not fn.endswith("_SEALED.txt"):
                return Path(dirpath) / fn
    return None


def _find_sealed(name: str, roots: list) -> Path | None:
    pat = name.lower()
    for root in roots:
        if isinstance(root, Path) and root.is_file():
            if pat in root.name.lower():
                return root
        if isinstance(root, Path) and root.is_dir():
            hit = _shallow_find(root, pat)
            if hit:
                return hit
    return None


def collect() -> tuple[list[tuple[str, Path]], list[str]]:
    found: list[tuple[str, Path]] = []
    missing: list[str] = []
    for name, roots in PACK.items():
        src = _find_sealed(name, roots) if name != "farthead" else next(
            (p for p in roots if isinstance(p, Path) and p.is_file()), None
        )
        if src is None and name == "farthead":
            src = _find_sealed(name, roots)
        if src is None:
            missing.append(name)
            continue
        found.append((name, src))
    return found, missing


def send(to_addr: str | None = None) -> int:
    user, pw = _load_env()
    to_addr = to_addr or user
    found, missing = collect()
    OUT.mkdir(parents=True, exist_ok=True)
    attachments: list[tuple[str, Path]] = []
    for name, src in found:
        dst = OUT / f"{name}.rtf"
        txt_to_rtf(src, dst)
        attachments.append((f"{name}.rtf", dst))

    # bonus entry file for empty auditor account
    eatme_src = EATME / "EATME.txt"
    if eatme_src.is_file():
        dst = OUT / "EATME.rtf"
        txt_to_rtf(eatme_src, dst)
        attachments.append(("EATME.rtf", dst))

    append_src = EATME / "open/APPEND_LAST.txt"
    if append_src.is_file():
        dst = OUT / "APPEND_LAST.rtf"
        txt_to_rtf(append_src, dst)
        attachments.append(("APPEND_LAST.rtf", dst))

    now = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
    subj = "eatme auditor pack — RTF"
    body_lines = [
        f"eatme RTF pack — {now}",
        "",
        "For Fresh Cursor auditor (other Google account).",
        "",
        "Attached:",
    ]
    for fn, _ in attachments:
        body_lines.append(f"  · {fn}")
    if missing:
        body_lines.extend(["", "MISSING on Drive (drop in eatme/sealed/ · re-run send):", ""])
        for m in missing:
            body_lines.append(f"  · {m}")
    body_lines.extend(
        [
            "",
            "Local copies: drop_pile/eatme/email_out/",
            "Forward attachments to auditor email or save on CB1.",
            "",
            "Word: EATME · RTF · AUDITOR",
        ]
    )
    body = "\n".join(body_lines)

    msg = MIMEMultipart()
    msg["From"] = user
    msg["To"] = to_addr
    msg["Subject"] = subj
    msg.attach(MIMEText(body, "plain", "utf-8"))

    for fn, path in attachments:
        part = MIMEBase("application", "rtf")
        part.set_payload(path.read_bytes())
        encoders.encode_base64(part)
        part.add_header("Content-Disposition", f'attachment; filename="{fn}"')
        msg.attach(part)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=60) as smtp:
        smtp.login(user, pw)
        smtp.sendmail(user, [to_addr], msg.as_string())

    print(f"OK sent to {to_addr} · {len(attachments)} attachments")
    if missing:
        print("MISSING:", ", ".join(missing))
    for fn, p in attachments:
        print(f"  {fn} · {p.stat().st_size} bytes")
    return 0 if not missing else 2


if __name__ == "__main__":
    dest = sys.argv[1] if len(sys.argv) > 1 else None
    raise SystemExit(send(dest))
