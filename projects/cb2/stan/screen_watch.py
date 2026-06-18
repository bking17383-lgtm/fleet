#!/usr/bin/env python3
"""Daddy screen watch — capture every 20s · bus status · background only.

  python3 ~/.stan/screen_watch.py once
  python3 ~/.stan/screen_watch.py watch [seconds]

Writes fleet/bus/DADDY_SCREEN.txt · keeps ~/.stan/screen/latest.png fresh.
"""
from __future__ import annotations

import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from bus_lane import bus_root, safe_mkdir, STAN, LOGS

INTERVAL = float(os.environ.get("SCREEN_SEC", "20"))
OUT_DIR = STAN / "screen"
LATEST = OUT_DIR / "latest.png"
HELD = OUT_DIR / "held.png"
STATUS_REL = "fleet/bus/DADDY_SCREEN.txt"
LOG = LOGS / "screen_watch.log"
MAX_STAMPS = 30
MIN_GOOD_BYTES = int(os.environ.get("SCREEN_MIN_BYTES", "15000"))
SCROT_EVERY = float(os.environ.get("SCREEN_SCROT_EVERY", "120"))  # slow scrot on penguin
_last_scrot = 0.0


def _log(msg: str) -> None:
    safe_mkdir(LOG.parent)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(f"{datetime.now(timezone.utc).isoformat(timespec='seconds')} {msg}\n")


def _trim_stamps() -> None:
    if not OUT_DIR.is_dir():
        return
    stamps = sorted(OUT_DIR.glob("capture_*.png"), key=lambda p: p.stat().st_mtime, reverse=True)
    for old in stamps[MAX_STAMPS:]:
        try:
            old.unlink()
        except OSError:
            pass


def _run_sh(script: str) -> tuple[bool, str]:
    path = STAN / script
    if not path.is_file():
        return False, f"missing {script}"
    try:
        r = subprocess.run(["bash", str(path)], capture_output=True, text=True, timeout=30)
        out = (r.stdout or "").strip() or (r.stderr or "").strip()
        return r.returncode == 0 and LATEST.is_file(), out[:240]
    except (OSError, subprocess.SubprocessError) as exc:
        return False, str(exc)[:240]


def _good_file(path: Path) -> bool:
    try:
        return path.is_file() and path.stat().st_size >= MIN_GOOD_BYTES
    except OSError:
        return False


def _promote(src: Path, source: str) -> tuple[bool, str]:
    """Copy good capture → latest + held (held sticks until next good snap)."""
    if not _good_file(src):
        return False, f"too small: {src}"
    safe_mkdir(OUT_DIR)
    shutil = __import__("shutil")
    shutil.copyfile(src, LATEST)
    shutil.copyfile(src, HELD)
    stamp = OUT_DIR / f"capture_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    try:
        shutil.copyfile(src, stamp)
    except OSError:
        pass
    _trim_stamps()
    return True, f"{source} · {src.name} · {src.stat().st_size}b"


def tick() -> dict:
    global _last_scrot
    bus = bus_root()
    now = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
    host = os.uname().nodename
    safe_mkdir(OUT_DIR)

    ok, detail, source = False, "", "none"

    # 1) EYES inbox — CB1-style camera/screen snaps (best on ChromeOS)
    ok, detail = _run_sh("read_eyes.sh")
    if ok:
        source = "eyes_inbox"
    else:
        # 2) Brian drops png in Drive snaps folder
        ok, detail = _run_sh("read_snap.sh")
        if ok:
            source = "drive_snap"
        else:
            # 3) scrot — only occasionally on penguin (usually black)
            try_scrot = (time.time() - _last_scrot) >= SCROT_EVERY
            if try_scrot:
                _last_scrot = time.time()
                ok, detail = _run_sh("screen_capture.sh")
                if ok:
                    source = "scrot"

    # If fallback copied a good file, promote to held
    if ok and LATEST.is_file() and _good_file(LATEST):
        if not _good_file(HELD):
            shutil = __import__("shutil")
            shutil.copyfile(LATEST, HELD)
    elif _good_file(HELD) and not _good_file(LATEST):
        shutil = __import__("shutil")
        shutil.copyfile(HELD, LATEST)
        ok, source = True, "held_sticky"

    bytes_n = LATEST.stat().st_size if _good_file(LATEST) else (HELD.stat().st_size if _good_file(HELD) else 0)
    held_n = HELD.stat().st_size if _good_file(HELD) else 0
    mtime = ""
    show_path = LATEST if _good_file(LATEST) else (HELD if _good_file(HELD) else None)
    if show_path:
        mtime = datetime.fromtimestamp(show_path.stat().st_mtime, tz=timezone.utc).astimezone().isoformat(
            timespec="seconds"
        )

    url = f"http://127.0.0.1:{os.environ.get('HITME_PORT', '8770')}/screen/held.png"
    lines = [
        f"DADDY SCREEN — {now}",
        f"host={host} · interval={INTERVAL:.0f}s · capture={'OK' if ok or held_n else 'WAITING'}",
        f"source={source} · bytes={bytes_n} · held_bytes={held_n} · mtime={mtime or 'none'}",
        f"path={show_path or LATEST}",
        f"url={url}",
        f"detail={detail or '(none)'}",
        "",
        "Brian: open /screen · tap SHOW SCREEN (held until next snap)",
        "Or mesh :8765 SNAP · or drop png in drop_pile/from_brian/snaps/",
        "Word: SCREEN",
    ]
    out = bus / STATUS_REL
    safe_mkdir(out.parent)
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    _log(f"tick ok={ok} bytes={bytes_n} src={source}")
    return {"now": now, "ok": ok, "bytes": bytes_n, "source": source, "mtime": mtime}


def watch_loop(sec: float) -> None:
    _log(f"START interval={sec}s")
    while True:
        try:
            tick()
        except Exception as exc:
            _log(f"ERR {exc}")
        time.sleep(sec)


def main() -> int:
    cmd = sys.argv[1] if len(sys.argv) > 1 else "once"
    if cmd == "once":
        r = tick()
        print(f"screen ok={r['ok']} bytes={r['bytes']} src={r['source']}")
        print(f"→ {LATEST}")
        print(f"→ {bus_root() / STATUS_REL}")
        return 0 if r["ok"] or LATEST.is_file() else 1
    if cmd == "watch":
        sec = float(sys.argv[2]) if len(sys.argv) > 2 else INTERVAL
        watch_loop(sec)
        return 0
    print("Usage: screen_watch.py once|watch [seconds]", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
