"""Fleet bus paths — local first. Brian is never admin."""
from __future__ import annotations

import shutil
from pathlib import Path

STAN = Path.home() / ".stan"
LOCAL_BUS = STAN / "fleet_bus"
STAGING = STAN / "fleet_staging"
LOCAL_INBOX = STAN / "local_inbox"
LOGS = STAN / "logs"

DRIVE_CANDIDATES = [
    Path("/mnt/shared/GoogleDrive/MyDrive"),
    Path("/mnt/home/google_drive/MyDrive"),
    Path.home() / "GoogleDrive/MyDrive",
]


def drive_live() -> Path | None:
    for p in DRIVE_CANDIDATES:
        try:
            if (p / "fleet").is_dir():
                return p
        except OSError:
            continue
    return None


def _ensure_local_bus() -> Path:
    LOCAL_BUS.mkdir(parents=True, exist_ok=True)
    if not (LOCAL_BUS / "fleet").is_dir() and (STAGING / "fleet").is_dir():
        shutil.copytree(STAGING / "fleet", LOCAL_BUS / "fleet", dirs_exist_ok=True)
    if not (LOCAL_BUS / "drop_pile").is_dir() and (STAGING / "drop_pile").is_dir():
        shutil.copytree(STAGING / "drop_pile", LOCAL_BUS / "drop_pile", dirs_exist_ok=True)
    (LOCAL_BUS / "fleet" / "bus").mkdir(parents=True, exist_ok=True)
    return LOCAL_BUS


def bus_root() -> Path:
    live = drive_live()
    if live:
        return live
    return _ensure_local_bus()


def is_drive_live() -> bool:
    return drive_live() is not None


def safe_is_file(path: Path) -> bool:
    try:
        return path.is_file()
    except OSError:
        return False


def safe_read_text(path: Path, default: str = "") -> str:
    try:
        if path.is_file():
            return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        pass
    return default


def safe_mkdir(path: Path) -> None:
    try:
        path.mkdir(parents=True, exist_ok=True)
    except OSError:
        pass


def sync_to_drive() -> bool:
    live = drive_live()
    if not live:
        return False
    bus = _ensure_local_bus()
    for sub in ("fleet", "drop_pile"):
        src = bus / sub
        if src.is_dir():
            shutil.copytree(src, live / sub, dirs_exist_ok=True)
    return True
