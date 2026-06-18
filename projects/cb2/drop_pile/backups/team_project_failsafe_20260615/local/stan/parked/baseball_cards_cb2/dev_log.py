"""Developer-only debug log — pull from phone via /api/dev/log (key in data/dev/dev.key)."""

from __future__ import annotations

import json
import secrets
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parent
DEV_DIR = BASE_DIR / "data" / "dev"
LOG_FILE = DEV_DIR / "phone_debug.log"
KEY_FILE = DEV_DIR / "dev.key"
MAX_BYTES = 512 * 1024

_lock = threading.Lock()


def _now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat()


def _ensure_dev_dir() -> None:
    DEV_DIR.mkdir(parents=True, exist_ok=True)


def dev_key() -> str:
    """Return or create the developer API key (stored on server only)."""
    _ensure_dev_dir()
    if KEY_FILE.is_file():
        return KEY_FILE.read_text(encoding="utf-8").strip()
    key = secrets.token_urlsafe(12)
    KEY_FILE.write_text(key + "\n", encoding="utf-8")
    return key


def check_key(provided: str | None) -> bool:
    if not provided:
        return False
    return provided.strip() == dev_key()


def _rotate_if_needed() -> None:
    if not LOG_FILE.is_file():
        return
    try:
        if LOG_FILE.stat().st_size <= MAX_BYTES:
            return
        backup = LOG_FILE.with_suffix(".log.1")
        if backup.is_file():
            backup.unlink()
        LOG_FILE.rename(backup)
    except OSError:
        pass


def log(event: str, **fields: Any) -> None:
    """Append one JSON line to the debug log."""
    _ensure_dev_dir()
    record = {
        "ts": _now(),
        "event": event,
        **fields,
    }
    line = json.dumps(record, default=str, ensure_ascii=False) + "\n"
    with _lock:
        _rotate_if_needed()
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line)


def log_exception(event: str, exc: BaseException, **fields: Any) -> None:
    log(event, error=str(exc), error_type=type(exc).__name__, **fields)


def log_fetch_result(result: dict[str, Any], trigger: str = "fetch") -> None:
    """Log sync outcome plus catalog vs expected snapshot (missing cards debugging)."""
    try:
        from collx_data import diagnostic_snapshot

        snap = diagnostic_snapshot()
    except Exception as exc:
        snap = {"snapshot_error": str(exc)}

    imp = result.get("import") or {}
    log(
        "collx_sync",
        trigger=trigger,
        status=result.get("status"),
        gmail=result.get("gmail"),
        consolidate=result.get("consolidate"),
        promote=result.get("promote"),
        import_status=imp.get("status"),
        import_message=imp.get("message"),
        imported=imp.get("imported"),
        import_reason=imp.get("import_reason"),
        snapshot=snap,
    )


def tail(max_lines: int = 300) -> str:
    if not LOG_FILE.is_file():
        return ""
    try:
        lines = LOG_FILE.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return ""
    if max_lines <= 0:
        return "\n".join(lines)
    return "\n".join(lines[-max_lines:])


def human_tail(max_lines: int = 200) -> str:
    """Readable log lines for phone preview."""
    if not LOG_FILE.is_file():
        return "No debug log yet."
    try:
        lines = LOG_FILE.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return "Could not read log file."
    out: list[str] = []
    for raw in lines[-max_lines:]:
        try:
            rec = json.loads(raw)
            ts = rec.get("ts", "")[:19].replace("T", " ")
            event = rec.get("event", "?")
            rest = {k: v for k, v in rec.items() if k not in ("ts", "event")}
            out.append(f"{ts}  {event}  {json.dumps(rest, default=str, ensure_ascii=False)}")
        except json.JSONDecodeError:
            out.append(raw)
    return "\n".join(out) if out else "Log file is empty."


def stats() -> dict[str, Any]:
    _ensure_dev_dir()
    size = 0
    lines = 0
    if LOG_FILE.is_file():
        try:
            size = LOG_FILE.stat().st_size
            with open(LOG_FILE, encoding="utf-8", errors="replace") as f:
                lines = sum(1 for _ in f)
        except OSError:
            pass
    backup = LOG_FILE.with_suffix(".log.1")
    return {
        "log_path": str(LOG_FILE),
        "key_path": str(KEY_FILE),
        "exists": LOG_FILE.is_file(),
        "size_bytes": size,
        "line_count": lines,
        "has_rotated_backup": backup.is_file(),
        "max_bytes": MAX_BYTES,
    }


def clear() -> dict[str, Any]:
    with _lock:
        removed = 0
        if LOG_FILE.is_file():
            try:
                LOG_FILE.unlink()
                removed = 1
            except OSError:
                pass
        backup = LOG_FILE.with_suffix(".log.1")
        if backup.is_file():
            try:
                backup.unlink()
                removed += 1
            except OSError:
                pass
    log("log_cleared", session=uuid.uuid4().hex[:8])
    return {"status": "ok", "removed_files": removed}


def startup_note(host: str, port: int) -> str:
    key = dev_key()
    log(
        "server_start",
        host=host,
        port=port,
        pid=__import__("os").getpid(),
        key_path=str(KEY_FILE),
        log_path=str(LOG_FILE),
    )
    return key
