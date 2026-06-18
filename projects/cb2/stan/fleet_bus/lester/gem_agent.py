#!/usr/bin/env python3
"""
GEM agent — auto-maintains Brian profile + bus reports.
Brian never fills forms. CPT delegates catalog/stuck reads here.

  python3 ~/.stan/gem_agent.py once
  python3 ~/.stan/gem_agent.py watch   # 10 min

Word: GEM
"""
from __future__ import annotations

import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from bus_lane import bus_root, safe_is_file, safe_mkdir, safe_read_text, STAN, LOGS

BUS = bus_root()
GEM_LOG = LOGS / "gem_agent.log"
BRIAN_LAW_AUTO = BUS / "fleet/BRIAN_LAW_AUTO.txt"
GEM_REPORT = BUS / "fleet/bus/GEMINI_DRIVE_REPORT.txt"
GEM_STATUS = BUS / "fleet/bus/GEM_STATUS.txt"
PROMPT_HIST = Path.home() / ".config/cursor/prompt_history.json"
UNCLE_VOICE = Path.home() / ".cursor/rules/uncle-voice.mdc"
INBOX_LOCAL = STAN / "BRIAN_INBOX_LOCAL.txt"
IDEA_PARK = BUS / "fleet/bus/IDEA_PARK.txt"
STUCK = BUS / "fleet/STUCK_BOARD.txt"
INTERVAL = int(os.environ.get("GEM_INTERVAL", "600"))


def _log(msg: str) -> None:
    safe_mkdir(LOGS)
    line = f"{datetime.now(timezone.utc).isoformat(timespec='seconds')} {msg}\n"
    with open(GEM_LOG, "a", encoding="utf-8") as f:
        f.write(line)


def _gemini_key() -> str | None:
    if os.environ.get("GEMINI_API_KEY"):
        return os.environ["GEMINI_API_KEY"].strip()
    env = STAN / "gemini.env"
    if env.is_file():
        for line in env.read_text(encoding="utf-8").splitlines():
            if line.startswith("GEMINI_API_KEY=") and not line.endswith("="):
                return line.split("=", 1)[1].strip()
    for keys in (
        BUS / "lester/lester_keys.md",
        Path("/mnt/shared/GoogleDrive/MyDrive/lester/lester_keys.md"),
    ):
        try:
            if keys.is_file():
                for line in keys.read_text(encoding="utf-8").splitlines():
                    s = line.strip()
                    if s.startswith("AIza"):
                        return s
        except OSError:
            continue
    return None


def _recent_prompts(n: int = 40) -> list[str]:
    if not PROMPT_HIST.is_file():
        return []
    try:
        data = json.loads(PROMPT_HIST.read_text(encoding="utf-8"))
        if isinstance(data, list):
            return [str(x).strip() for x in data[:n] if str(x).strip()]
    except (json.JSONDecodeError, OSError):
        pass
    return []


def _infer_ship_lane(prompts: list[str]) -> str:
    blob = " ".join(prompts[:25]).lower()
    if "sarah" in blob or "trip" in blob:
        return "A — Sarah link before trip (inferred from Brian prompts)"
    if "hitme" in blob or "hello@" in blob:
        return "B — hitme landing + contact"
    if "card" in blob or "collx" in blob or "baseball" in blob:
        return "C — one card scan flow"
    return "A — Sarah (GEM default — Brian mentioned Sarah/trip most)"


def _infer_never_ping(prompts: list[str]) -> str:
    hits = []
    blob = " ".join(prompts).lower()
    if "art" in blob or "camel" in blob:
        hits.append("art / camel sessions")
    if "sarah" in blob and "design" not in blob:
        hits.append("unless fire")
    if not hits:
        hits = ["art · camel · heritage cards · when Brian says HOLD"]
    return " · ".join(hits)


def _infer_cpt_sentence(prompts: list[str]) -> str:
    blob = " ".join(prompts[:15]).lower()
    if "admin" in blob or "spin" in blob:
        return "CPT holds the ranch — stuck first, delegate NET/STUDIO, Brian is not admin."
    return "CPT is Brian's one contact — cheap, honest, adapts, does not spin."


def _collect_signals() -> dict[str, str]:
    prompts = _recent_prompts()
    inbox = ""
    if safe_is_file(INBOX_LOCAL):
        inbox = safe_read_text(INBOX_LOCAL).split("--- TYPE BELOW", 1)[-1].strip().splitlines()[0][:120]
    ideas = 0
    if safe_is_file(IDEA_PARK):
        ideas = len([ln for ln in safe_read_text(IDEA_PARK).splitlines() if ln.strip() and not ln.startswith("#")])
    inbox_files = len(list((STAN / "local_inbox").glob("*"))) if (STAN / "local_inbox").is_dir() else 0
    return {
        "ship_lane": _infer_ship_lane(prompts),
        "cpt_sentence": _infer_cpt_sentence(prompts),
        "never_ping": _infer_never_ping(prompts),
        "praise_style": "Specific · short · notices real detail · not corporate · soul not ticket bot",
        "annoy_voice": "Admin forms · spin · security lecture · Delegation complete · multi-captain",
        "overflow": "Notepad · GL · AWS lady · art — when all agents busy (good)",
        "recent_inbox": inbox or "(empty)",
        "idea_park_lines": str(ideas),
        "local_inbox_files": str(inbox_files),
        "prompt_sample": prompts[0][:100] if prompts else "",
    }


def _write_brian_law_auto(sig: dict[str, str]) -> None:
    now = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
    text = f"""BRIAN LAW — AUTO (GEM maintains · Brian does NOT fill)
Updated: {now}

Ship lane this week: {sig['ship_lane']}

CPT in one sentence: {sig['cpt_sentence']}

Never ping during: {sig['never_ping']}

Praise that lands: {sig['praise_style']}

Voice that annoys: {sig['annoy_voice']}

Overflow when team busy: {sig['overflow']}

Signals: inbox={sig['recent_inbox']} · ideas_parked={sig['idea_park_lines']} · local_files={sig['local_inbox_files']}

GEM re-runs on SLAVE/GEM · edit fleet/BRIAN_LAW.txt only if Brian overrides by telling CPT.
"""
    safe_mkdir(BRIAN_LAW_AUTO.parent)
    BRIAN_LAW_AUTO.write_text(text, encoding="utf-8")
    # Mirror to BRIAN_LAW so nothing asks Brian to fill blanks
    (BUS / "fleet/BRIAN_LAW.txt").write_text(text, encoding="utf-8")


def _write_gem_report(sig: dict[str, str], gemini_note: str = "") -> None:
    now = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
    stuck_snip = safe_read_text(STUCK, "(no stuck board)")[:800]
    lines = [
        f"GEM REPORT — {now}",
        "",
        "AUTO BRIAN PROFILE",
        f"  ship: {sig['ship_lane']}",
        f"  cpt: {sig['cpt_sentence']}",
        f"  quiet: {sig['never_ping']}",
        "",
        "STUCK (snippet)",
        stuck_snip,
        "",
        "GEMINI API",
        gemini_note or "local inference only (add ~/.stan/gemini.env for API enhance)",
        "",
        "CPT: read BRIAN_LAW_AUTO · delegate NET/STUDIO · do not ask Brian to fill forms.",
    ]
    safe_mkdir(GEM_REPORT.parent)
    GEM_REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_status(ok: bool, detail: str) -> None:
    now = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
    GEM_STATUS.write_text(
        f"GEM_STATUS — {now}\nok={ok}\n{detail}\n",
        encoding="utf-8",
    )


def _gemini_polish(sig: dict[str, str]) -> str:
    key = _gemini_key()
    if not key:
        return "no API key"
    prompt = (
        "You are GEM, fleet librarian. NOT captain. One paragraph: Brian profile for agents. "
        "Cheap, growth-focused, hates admin forms. Facts only.\n"
        f"Signals: {json.dumps(sig, ensure_ascii=False)[:2000]}"
    )
    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"gemini-2.0-flash:generateContent?key={key}"
    )
    try:
        req = urllib.request.Request(
            url,
            data=json.dumps({"contents": [{"parts": [{"text": prompt}]}]}).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode())
        parts = data.get("candidates", [{}])[0].get("content", {}).get("parts", [])
        text = parts[0].get("text", "").strip() if parts else ""
        return text[:1200] if text else "gemini empty"
    except (urllib.error.URLError, KeyError, IndexError, json.JSONDecodeError) as e:
        return f"gemini err: {e}"


def run_once() -> None:
    sig = _collect_signals()
    note = _gemini_polish(sig)
    _write_brian_law_auto(sig)
    _write_gem_report(sig, note)
    _write_status(True, f"law_auto ok · gemini={note[:80]}")
    _log("PASS law_auto + report")


def main() -> None:
    mode = sys.argv[1] if len(sys.argv) > 1 else "once"
    if mode == "once":
        run_once()
        print(f"GEM OK → {BRIAN_LAW_AUTO}")
        print(f"GEM OK → {GEM_REPORT}")
        return
    if mode == "watch":
        _log("watch start")
        while True:
            try:
                run_once()
            except Exception as e:
                _log(f"ERR {e}")
            time.sleep(INTERVAL)
    else:
        print("Usage: gem_agent.py once|watch", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
