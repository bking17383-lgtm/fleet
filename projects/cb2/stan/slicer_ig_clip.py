#!/usr/bin/env python3
"""Find Instagram link in recent Gmail · download · clip with Video Slicer stack."""
from __future__ import annotations

import email
import imaplib
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from email.header import decode_header
from pathlib import Path

STAN = Path.home() / ".stan"
DRIVE = Path("/mnt/shared/GoogleDrive/MyDrive")
OUT_DIR = DRIVE / "Videos" / "clips"
SRC_DIR = DRIVE / "Videos" / "inbox"
BUS = DRIVE / "fleet/bus/SLICER_CLIP_JOB.txt"
YT_DLP = Path("/tmp/yt-dlp")
FFMPEG = Path("/tmp/ffmpeg-7.0.2-amd64-static/ffmpeg")
IG_RE = re.compile(
    r"https?://(?:www\.)?(?:instagram\.com/(?:reel|reels|p|tv)/[A-Za-z0-9_-]+|instagr\.am/(?:reel|p)/[A-Za-z0-9_-]+)",
    re.I,
)
SHARE_GOOGLE_RE = re.compile(r"https?://share\.google/[A-Za-z0-9]+", re.I)
TIME_RE = re.compile(r"(?:start|from|at)\s*[:=]?\s*(\d+(?:\.\d+)?)\s*(?:s|sec)?", re.I)
DUR_RE = re.compile(r"(?:duration|length|clip)\s*[:=]?\s*(\d+(?:\.\d+)?)\s*(?:s|sec)?", re.I)


def _now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def _load_gmail_env() -> None:
    env = STAN / "gmail.env"
    if not env.is_file():
        return
    for line in env.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def _decode(raw: bytes | str) -> str:
    if isinstance(raw, str):
        return raw
    parts = []
    for chunk, enc in decode_header(raw):
        if isinstance(chunk, bytes):
            parts.append(chunk.decode(enc or "utf-8", errors="replace"))
        else:
            parts.append(chunk)
    return "".join(parts)


def _body_text(msg: email.message.Message) -> str:
    chunks: list[str] = []
    if msg.is_multipart():
        for part in msg.walk():
            ctype = part.get_content_type()
            if ctype not in ("text/plain", "text/html"):
                continue
            payload = part.get_payload(decode=True)
            if payload:
                chunks.append(payload.decode(part.get_content_charset() or "utf-8", errors="replace"))
    else:
        payload = msg.get_payload(decode=True)
        if payload:
            chunks.append(payload.decode(msg.get_content_charset() or "utf-8", errors="replace"))
    return "\n".join(chunks)


def _resolve_share_google(url: str) -> str:
    import urllib.request

    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            html = resp.read().decode("utf-8", errors="replace")
    except OSError:
        return url
    m = re.search(r"instagram\.com/reel/[A-Za-z0-9_-]+", html, re.I)
    if m:
        return "https://www." + m.group(0).rstrip("/") + "/"
    return url


def _find_ig_in_mail(max_messages: int = 40) -> dict | None:
    user = os.environ.get("GMAIL_USER") or os.environ.get("GMAIL_ADDRESS") or "bking17383@gmail.com"
    pwd = os.environ.get("GMAIL_APP_PASSWORD") or os.environ.get("GMAIL_PASSWORD")
    if not pwd:
        return None
    mail = imaplib.IMAP4_SSL("imap.gmail.com", timeout=45)
    mail.login(user, pwd)
    mail.select("INBOX")
    _, data = mail.search(None, "ALL")
    ids = data[0].split()[-max_messages:]
    best = None
    for mid in reversed(ids):
        _, msg_data = mail.fetch(mid, "(RFC822)")
        raw = msg_data[0][1]
        msg = email.message_from_bytes(raw)
        subj = _decode(msg.get("Subject", ""))
        body = _body_text(msg)
        blob = subj + "\n" + body
        urls = IG_RE.findall(blob)
        if not urls:
            share = SHARE_GOOGLE_RE.findall(blob)
            if share:
                urls = [_resolve_share_google(share[0])]
        if not urls:
            continue
        start = 0.0
        dur = 10.0
        m = TIME_RE.search(blob)
        if m:
            start = float(m.group(1))
        m = DUR_RE.search(blob)
        if m:
            dur = float(m.group(1))
        best = {
            "url": urls[0].rstrip(").,"),
            "subject": subj[:160],
            "start": start,
            "duration": dur,
            "from": _decode(msg.get("From", ""))[:120],
        }
        break
    mail.logout()
    return best


def _run(cmd: list[str], **kw) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


def main() -> int:
    _load_gmail_env()
    url = (sys.argv[1] if len(sys.argv) > 1 else "").strip()
    start = float(sys.argv[2]) if len(sys.argv) > 2 else 0.0
    dur = float(sys.argv[3]) if len(sys.argv) > 3 else 10.0
    meta = {}
    if not url:
        hit = _find_ig_in_mail()
        if not hit:
            BUS.write_text(
                f"SLICER CLIP JOB — {_now()}\nstatus=NO_IG_IN_EMAIL\n"
                f"hint=Forward email to self with Instagram link or pass URL arg\n",
                encoding="utf-8",
            )
            print("NO_IG_IN_EMAIL")
            return 1
        url = hit["url"]
        start = hit.get("start", 0.0)
        dur = hit.get("duration", 10.0)
        meta = hit

    if not YT_DLP.is_file() or not FFMPEG.is_file():
        print("missing yt-dlp or ffmpeg")
        return 1

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    SRC_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    src = SRC_DIR / f"ig_{stamp}.mp4"
    clip = OUT_DIR / f"clip_{stamp}.mp4"

    dl = _run([str(YT_DLP), "-f", "best[ext=mp4]/best", "-o", str(src), url], timeout=300)
    if dl.returncode != 0 or not src.is_file():
        err = (dl.stderr or dl.stdout or "download failed")[:500]
        BUS.write_text(
            f"SLICER CLIP JOB — {_now()}\nstatus=DOWNLOAD_FAIL\nurl={url}\nerr={err}\n",
            encoding="utf-8",
        )
        print("DOWNLOAD_FAIL", err[:200])
        return 1

    ff = _run(
        [
            str(FFMPEG),
            "-y",
            "-ss",
            str(start),
            "-i",
            str(src),
            "-t",
            str(dur),
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-c:a",
            "aac",
            "-movflags",
            "+faststart",
            str(clip),
        ],
        timeout=120,
    )
    if ff.returncode != 0 or not clip.is_file():
        err = (ff.stderr or ff.stdout or "clip failed")[:500]
        BUS.write_text(
            f"SLICER CLIP JOB — {_now()}\nstatus=CLIP_FAIL\nurl={url}\nsrc={src}\nerr={err}\n",
            encoding="utf-8",
        )
        print("CLIP_FAIL", err[:200])
        return 1

    lines = [
        f"SLICER CLIP JOB — {_now()}",
        "status=OK",
        f"url={url}",
        f"start={start}",
        f"duration={dur}",
        f"src={src}",
        f"clip={clip}",
    ]
    if meta:
        lines.append(f"email_subject={meta.get('subject', '')}")
    BUS.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"ok": True, "clip": str(clip), "url": url, "start": start, "duration": dur}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
