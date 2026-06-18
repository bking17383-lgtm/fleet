#!/usr/bin/env python3
"""Watch MyDrive/gl/ for GL writes; post Cursor agent responses to gl/from_cursor/."""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path

DRIVE = Path("/mnt/shared/GoogleDrive/MyDrive")
GL = DRIVE / "gl"
INBOX = DRIVE / "inbox"
FROM_CURSOR = GL / "from_cursor"
STATE_FILE = GL / "scan_state.json"
PENDING_FILE = FROM_CURSOR / "PENDING.md"
LOG_FILE = GL / "scan_log.txt"

SKIP_NAMES = {
    "scan_state.json",
    "scan_log.txt",
    "apps_script_auto_export.gs",
    "gdoc_export_manifest.json",
}
SKIP_DIRS = {"from_cursor", "__pycache__"}


def _now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat()


def _load_state() -> dict:
    if STATE_FILE.is_file():
        try:
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    return {"files": {}, "last_scan": None}


def _save_state(state: dict) -> None:
    state["last_scan"] = _now()
    STATE_FILE.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")


def _log(msg: str) -> None:
    line = f"{_now()} {msg}\n"
    try:
        with LOG_FILE.open("a", encoding="utf-8") as f:
            f.write(line)
    except OSError:
        pass
    print(line, end="", flush=True)


def _iter_watch_files() -> list[Path]:
    paths: list[Path] = []
    for root in (GL, INBOX):
        if not root.is_dir():
            continue
        for p in root.rglob("*"):
            if not p.is_file():
                continue
            if p.suffix.lower() not in (".txt", ".md", ".json"):
                continue
            if p.name in SKIP_NAMES:
                continue
            if any(part in SKIP_DIRS for part in p.parts):
                continue
            paths.append(p)
    return paths


def _scan_once() -> list[dict]:
    state = _load_state()
    known: dict[str, float] = state.get("files", {})
    changes: list[dict] = []

    for path in _iter_watch_files():
        key = str(path.relative_to(DRIVE))
        try:
            mtime = path.stat().st_mtime
        except OSError:
            continue
        prev = known.get(key)
        if prev is None or mtime > prev + 0.5:
            snippet = ""
            try:
                text = path.read_text(encoding="utf-8", errors="replace")
                snippet = text.strip().replace("\n", " ")[:240]
            except OSError:
                snippet = "(unreadable)"
            changes.append(
                {
                    "path": key,
                    "event": "new" if prev is None else "updated",
                    "snippet": snippet,
                    "mtime": mtime,
                }
            )
        known[key] = mtime

    state["files"] = known
    _save_state(state)
    return changes


def _write_response(changes: list[dict]) -> None:
    FROM_CURSOR.mkdir(parents=True, exist_ok=True)
    INBOX.mkdir(parents=True, exist_ok=True)

    lines = [
        "# GL ↔ Cursor bus",
        f"**Scanned:** {_now()}",
        f"**Changes:** {len(changes)}",
        "",
        "**CAPTN reply (persistent):** `gl/from_cursor/RESPONSE.md`",
        "",
    ]
    if changes:
        lines.append("## Latest GL writes")
        for c in changes:
            lines.append(f"- **{c['event']}** `{c['path']}`")
            if c["snippet"]:
                lines.append(f"  > {c['snippet']}")
            lines.append("")
    else:
        lines.append("_No new GL file changes this scan._")
        lines.append("")

    lines.extend(
        [
            "## GL reads this",
            "1. `RESPONSE.md` — CAPTN answer (do not overwrite)",
            "2. Drop transcripts in `MyDrive/inbox/` every 2–3 min",
            "",
        ]
    )

    body = "\n".join(lines)
    PENDING_FILE.write_text(body, encoding="utf-8")

    if changes:
        stamp = datetime.now().strftime("%Y%m%dT%H%M%S")
        hist = FROM_CURSOR / f"scan_{stamp}.md"
        hist.write_text(body, encoding="utf-8")


def scan_gl() -> int:
    if not GL.is_dir():
        _log("FAIL gl/ missing on Drive mount")
        return 1
    INBOX.mkdir(parents=True, exist_ok=True)
    FROM_CURSOR.mkdir(parents=True, exist_ok=True)

    changes = _scan_once()
    if changes:
        _write_response(changes)
        _log(f"OK {len(changes)} change(s) → gl/from_cursor/PENDING.md")
    else:
        _log("OK no changes")
    return 0


def watch_loop(interval: float = 120.0) -> None:
    _log(f"START watch interval={interval}s")
    while True:
        try:
            scan_gl()
        except Exception as e:
            _log(f"ERR {e}")
        time.sleep(interval)


if __name__ == "__main__":
    import sys

    cmd = sys.argv[1] if len(sys.argv) > 1 else "scan"
    if cmd == "scan":
        raise SystemExit(scan_gl())
    if cmd == "watch":
        interval = float(sys.argv[2]) if len(sys.argv) > 2 else 120.0
        watch_loop(interval)
    else:
        print("Usage: gl_scanner.py [scan|watch] [seconds]")
        raise SystemExit(1)
