#!/usr/bin/env python3
"""Picture inbox — detect new photos · OCR · execute (sandbox if unclear).

  python3 ~/.stan/picture_inbox_watch.py once
  python3 ~/.stan/picture_inbox_watch.py watch [sec]

Watches:
  MyDrive/convert_inbox/*.jpg|png|…
  ~/.stan/local_inbox/*.{jpg,png,…}

Posts:
  fleet/bus/PICTURE_INBOX.txt
  fleet/bus/PICTURE_SANDBOX.txt  (when unclear)
  ~/.stan/local_inbox/_ocr/<name>.txt

Law: fleet/PICTURE_INBOX_LAW.txt
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from bus_lane import STAN, bus_root, safe_mkdir

IMG_EXT = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
STATE = STAN / "picture_inbox_state.json"
OCR_DIR = STAN / "local_inbox" / "_ocr"
BUS = bus_root()
INBOX_OUT = BUS / "fleet/bus/PICTURE_INBOX.txt"
SANDBOX_OUT = BUS / "fleet/bus/PICTURE_SANDBOX.txt"
BRIAN_INBOX = BUS / "fleet/bus/BRIAN_INBOX.txt"
MARKER = "--- TYPE BELOW (one line) ---"


def _now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def _drive() -> Path:
    for p in (
        Path("/mnt/shared/GoogleDrive/MyDrive"),
        Path.home() / "GoogleDrive/MyDrive",
        bus_root(),
    ):
        if (p / "fleet").is_dir():
            return p
    return bus_root()


def _file_id(path: Path) -> str:
    try:
        st = path.stat()
        return f"{st.st_size}:{int(st.st_mtime)}"
    except OSError:
        return _hash(path)


def _hash(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()[:24]


def _load_state() -> dict:
    if not STATE.is_file():
        return {"done": {}}
    try:
        return json.loads(STATE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {"done": {}}


def _save_state(state: dict) -> None:
    safe_mkdir(STATE.parent)
    state["updated"] = _now()
    STATE.write_text(json.dumps(state, indent=2), encoding="utf-8")


def _ocr(path: Path) -> str:
    try:
        r = subprocess.run(
            ["tesseract", str(path), "stdout", "-l", "eng"],
            capture_output=True,
            text=True,
            timeout=45,
        )
        if r.returncode == 0 and r.stdout.strip():
            return r.stdout
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        pass
    return ""


def _inbox_dirs() -> list[Path]:
    d = _drive()
    dirs = [d / "convert_inbox", STAN / "local_inbox"]
    return [p for p in dirs if p.is_dir()]


def _find_new_images(state: dict, limit: int = 1) -> list[Path]:
    done: dict[str, str] = state.setdefault("done", {})
    candidates: list[Path] = []
    for inbox in _inbox_dirs():
        for path in inbox.iterdir():
            if not path.is_file() or path.suffix.lower() not in IMG_EXT:
                continue
            if path.name.startswith("."):
                continue
            candidates.append(path)
    if not done and len(candidates) > 1:
        candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        for old in candidates[1:]:
            done[str(old)] = _file_id(old)
        candidates = candidates[:1]
    else:
        candidates = [p for p in candidates if done.get(str(p)) != _file_id(p)]
        candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        candidates = candidates[:limit]
    return candidates


def _run_py(script: str, *args: str) -> tuple[bool, str]:
    try:
        r = subprocess.run(
            [sys.executable, str(STAN / script), *args],
            capture_output=True,
            text=True,
            timeout=60,
        )
        tail = (r.stdout or r.stderr or "").strip().splitlines()
        return r.returncode == 0, tail[-1] if tail else f"exit {r.returncode}"
    except (OSError, subprocess.TimeoutExpired) as e:
        return False, str(e)


def _classify(text: str) -> tuple[str, list[str], str]:
    low = text.lower()
    if any(k in low for k in ("net-clean=poison", "net clean=poison", "cpt✓", "studio~", "fleet 1/3")):
        return (
            "cb1_statusline",
            ["uncle_order_statusline", "gem_listen", "fleet_checkin"],
            "CB1 statusline poison · fix + refresh ack",
        )
    if any(k in low for k in ("buddy ok", "stay awake", "insomniac", "cb1_stay_awake", "hibernat")):
        return (
            "gem_power",
            ["gem_forward", "gem_listen", "fleet_checkin"],
            "Gem stay-awake · sync buddy ack from GEM_UNDERSTAND",
        )
    if any(k in low for k in ("uncle reboot", "uncle checkin", "keep_alive", "dum dum uncle")):
        return (
            "uncle",
            ["uncle_sync", "gem_listen", "fleet_checkin"],
            "Uncle screen · sync loop",
        )
    if any(k in low for k in ("puppy", "dumbass", "new_puppy_boot", "puppy checkin", "mirror lie", "puppy_real_drive")):
        return (
            "puppy",
            ["puppy_wake_order", "fleet_checkin"],
            "Puppy picture · wake orders on bus",
        )
    if len(low.strip()) > 40:
        return ("generic", ["fleet_checkin", "gem_listen"], "OCR ok · no strong rule")
    return ("unclear", [], "OCR empty or too short")


def _execute(actions: list[str], sandbox: bool) -> list[str]:
    ran: list[str] = []
    for act in actions:
        if sandbox and act not in ("fleet_checkin", "gem_listen", "uncle_sync"):
            ran.append(f"SANDBOX skip {act}")
            continue
        if act == "fleet_checkin":
            ok, msg = _run_py("fleet_checkin.py", "once")
            ran.append(f"fleet_checkin: {'OK' if ok else 'FAIL'} {msg[:80]}")
        elif act == "gem_listen":
            ok, msg = _run_py("cpt_gem_loop.py", "listen")
            ran.append(f"gem_listen: {'OK' if ok else 'FAIL'} {msg[:80]}")
        elif act == "gem_forward":
            ok, msg = _run_py("cpt_gem_loop.py", "forward")
            ran.append(f"gem_forward: {'OK' if ok else 'FAIL'} {msg[:80]}")
        elif act == "uncle_sync":
            ok, msg = _run_py("cpt_uncle_sync.py")
            ran.append(f"uncle_sync: {'OK' if ok else 'FAIL'} {msg[:80]}")
        elif act == "uncle_order_statusline":
            order = BUS / "fleet/bus/cpt_to_uncle.txt"
            safe_mkdir(order.parent)
            order.write_text(
                f"--- Daddy → Uncle (PICTURE INBOX auto) ---\n"
                f"time: {_now()}\n"
                f"from: picture_inbox_watch on penguin\n\n"
                f"Brian photo showed bad statusline (NET-clean=POISON).\n\n"
                f"DO NOW on CB1 Linux:\n"
                f"  bash ~/GoogleDrive/MyDrive/lester/CB1_STATUSLINE_FIX.sh\n"
                f"  python3 ~/GoogleDrive/MyDrive/lester/gem_loop_bridge.py\n\n"
                f"Word: UNCLE · PICTURE\n",
                encoding="utf-8",
            )
            ran.append("uncle_order_statusline: cpt_to_uncle.txt")
        elif act == "puppy_wake_order":
            order = BUS / "fleet/bus/cpt_to_puppy.txt"
            safe_mkdir(order.parent)
            order.write_text(
                f"--- Daddy → Puppy (PICTURE INBOX auto) ---\n"
                f"time: {_now()}\n\n"
                f"Brian photo · puppy job.\n"
                f"Paste card: ~/GoogleDrive/MyDrive/dumbass.txt\n"
                f"  bash ~/GoogleDrive/MyDrive/lester/NEW_PUPPY_BOOT.sh\n\n"
                f"Word: PUPPY\n",
                encoding="utf-8",
            )
            ran.append("puppy_wake_order: cpt_to_puppy.txt")
    return ran


def _append_brian_inbox(line: str) -> None:
    if not BRIAN_INBOX.is_file():
        body = f"# Brian inbox\n\n{MARKER}\n\n"
    else:
        body = BRIAN_INBOX.read_text(encoding="utf-8", errors="replace")
        if MARKER not in body:
            body = body.rstrip() + f"\n\n{MARKER}\n\n"
    stamp = _now()
    BRIAN_INBOX.write_text(
        body.rstrip() + f"\n\n[{stamp} picture_inbox] {line}\n",
        encoding="utf-8",
    )


def _process_one(path: Path, state: dict) -> dict:
    ocr = _ocr(path)
    safe_mkdir(OCR_DIR)
    ocr_path = OCR_DIR / f"{path.stem}.txt"
    ocr_path.write_text(ocr or "(no ocr text)", encoding="utf-8")

    kind, actions, reason = _classify(ocr)
    sandbox = kind in ("unclear", "generic")
    executed = _execute(actions, sandbox=sandbox)

    excerpt = "\n".join(ln.strip() for ln in (ocr or "").splitlines() if ln.strip())[:1200]
    card = (
        f"PICTURE INBOX — {_now()}\n"
        f"file: {path.name}\n"
        f"path: {path}\n"
        f"ocr: {ocr_path}\n"
        f"kind: {kind}\n"
        f"reason: {reason}\n"
        f"sandbox: {'YES' if sandbox else 'NO'}\n"
        f"\nOCR EXCERPT:\n{excerpt or '(empty)'}\n"
        f"\nEXECUTED:\n"
        + "\n".join(f"  • {x}" for x in executed)
        + "\n"
    )
    safe_mkdir(INBOX_OUT.parent)
    INBOX_OUT.write_text(card, encoding="utf-8")

    if sandbox:
        safe = (
            f"PICTURE SANDBOX — {_now()}\n"
            f"file: {path.name}\n"
            f"kind: {kind} · auto-execute partial\n\n"
            f"OCR:\n{excerpt[:800]}\n\n"
            f"Safe ran: {', '.join(executed) or 'none'}\n"
            f"Needs Brian/Cursor eyes if still wrong.\n"
        )
        SANDBOX_OUT.write_text(safe, encoding="utf-8")

    _append_brian_inbox(
        f"photo {path.name} · kind={kind} · sandbox={'YES' if sandbox else 'NO'} · read fleet/bus/PICTURE_INBOX.txt"
    )

    try:
        from daddy_team_say import announce

        announce("picture inbox", f"{path.name} · {kind} · sandbox={'YES' if sandbox else 'NO'}")
    except ImportError:
        pass

    state.setdefault("done", {})[str(path)] = _hash(path)
    return {"file": path.name, "kind": kind, "sandbox": sandbox, "executed": executed}


def once() -> list[dict]:
    state = _load_state()
    results = []
    for path in _find_new_images(state):
        results.append(_process_one(path, state))
    _save_state(state)
    return results


def watch(sec: float = 12.0) -> None:
    log = STAN / "logs" / "picture_inbox_watch.log"
    safe_mkdir(log.parent)
    while True:
        try:
            got = once()
            if got:
                line = f"{_now()} processed {len(got)} picture(s)\n"
                with open(log, "a", encoding="utf-8") as f:
                    f.write(line)
        except Exception as exc:
            with open(log, "a", encoding="utf-8") as f:
                f.write(f"{_now()} ERROR {exc}\n")
        time.sleep(sec)


def main() -> int:
    cmd = (sys.argv[1] if len(sys.argv) > 1 else "once").lower()
    if cmd == "once":
        got = once()
        if not got:
            print("PICTURE INBOX — no new images")
            return 0
        for r in got:
            print(json.dumps(r, indent=2))
        print(f"→ {INBOX_OUT}")
        return 0
    if cmd == "watch":
        sec = float(sys.argv[2]) if len(sys.argv) > 2 else 12.0
        watch(sec)
        return 0
    print("Usage: picture_inbox_watch.py once|watch [sec]", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
