#!/usr/bin/env python3
"""
Brian Router — type once on Drive; get paste blocks for CB1, CB2, puppy64.

Reads:  fleet/bus/BRIAN_INBOX.txt
Writes: fleet/bus/routed/*.txt, fleet/bus/BRIAN_ROUTED_SUMMARY.txt
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DRIVE_ROOT = Path("/mnt/shared/GoogleDrive/MyDrive")
FLEET_BUS = DRIVE_ROOT / "fleet" / "bus"
INBOX = FLEET_BUS / "BRIAN_INBOX.txt"
TALK = DRIVE_ROOT / "TALK.txt"
ROUTED_DIR = FLEET_BUS / "routed"
SUMMARY = FLEET_BUS / "BRIAN_ROUTED_SUMMARY.txt"
STATE = FLEET_BUS / "brian_router_state.json"
MAC_INBOX = FLEET_BUS / "mac_inbox.txt"

MARKER = "--- TYPE BELOW (one line) ---"
TALK_MARKER = "--- type below ---"

# Brian typos / retired words → fleet law (ONE_WORD_TRIGGERS.md)
TYPO_WORD: list[tuple[re.Pattern[str], str, str]] = [
    (re.compile(r"\bADDY\b", re.I), "DADDY", "ADDY→DADDY"),
    (re.compile(r"\bDADY\b", re.I), "DADDY", "DADY→DADDY"),
    (re.compile(r"\bCAPTIN\b", re.I), "CAPTN", "CAPTIN→CAPTN"),
    (re.compile(r"\bCAPTAN\b", re.I), "CAPTN", "CAPTAN→CAPTN"),
    (re.compile(r"\bCAPTAIN\b", re.I), "CAPTN", "CAPTAIN→CAPTN"),
    (re.compile(r"\bWRANGLER\b", re.I), "UNCLE", "WRANGLER→UNCLE (retired)"),
    (re.compile(r"\bBEACON\b", re.I), "DADDY", "BEACON→DADDY (retired)"),
    (re.compile(r"\bREADY\b", re.I), "UNCLE", "READY→UNCLE on CB1"),
    (re.compile(r"\bGLOB\b", re.I), "UNCLE", "GLOB→UNCLE"),
    (re.compile(r"\bPUPY64\b", re.I), "PUPPY", "PUPY64→PUPPY"),
    (re.compile(r"\bPUPY\b", re.I), "PUPPY", "PUPY→PUPPY"),
    (re.compile(r"\bPUPPI\b", re.I), "PUPPY", "PUPPI→PUPPY"),
    (re.compile(r"\bPUPPEY\b", re.I), "PUPPY", "PUPPEY→PUPPY"),
    (re.compile(r"\bcompters?\b", re.I), "computers", "spelling"),
    (re.compile(r"\bcomputrs?\b", re.I), "computers", "spelling"),
]

# LINK is wrong on Puppy Chrome — always PLATE for Lester6 bind
LINK_CONTEXT = re.compile(r"\b(link|linked|linking)\b", re.I)

PASTE_BLOCKS: dict[str, dict[str, str]] = {
    "UNCLE": {
        "cursor": (
            "UNCLE — read CB1_STANDING_LOOP.md. Post cb1_ready.txt. "
            "Camel parked unless Brian said CAMEL."
        ),
        "chrome": (
            "UNCLE — mode slave. Refresh lester6_to_uncle.md on Drive. "
            "Read drop_pile/to_lester/ for orders."
        ),
    },
    "DADDY": {
        "cursor": (
            "DADDY — read FLEET_TERMINAL_MAP.txt + DADDY_DELEGATE_ONLY.md. "
            "You are T3 captain. Delegate only. No execute."
        ),
        "chrome": (
            "DADDY — read lester/lester6_daddy_slave.md + ACK_FILE_LAW.md. "
            "Overwrite lester6_to_daddy.md plain .md. Say: BEACON live."
        ),
    },
    "CAPTN": {
        "cursor": (
            "CAPTN — read fleet/FLEET_AVAILABLE.txt + daddy_status.md. "
            "Delegate only. Post mac_inbox when Brian orders land."
        ),
        "chrome": (
            "DADDY — read lester/lester6_daddy_slave.md + ACK_FILE_LAW.md. "
            "Overwrite lester6_to_daddy.md plain .md."
        ),
    },
    "PUPPY": {
        "cursor": (
            "PUPPY — read PLATE_SLAVE_FIX_NOW.md + PUPPY_NOW.md. "
            "Confirm lester6_to_puppy.md mode:slave today. Execute queue."
        ),
        "chrome": (
            "PLATE — read lester/lester6_puppy_slave.md + ACK_FILE_LAW.md + "
            "PLATE_BIND_NOW.md. Overwrite lester6_to_puppy.md plain .md. Say: PLATE ready."
        ),
    },
    "PLATE": {
        "chrome": (
            "PLATE — read lester/lester6_puppy_slave.md + ACK_FILE_LAW.md + "
            "PLATE_BIND_NOW.md. Overwrite lester6_to_puppy.md plain .md. Say: PLATE ready."
        ),
    },
    "EXPORT": {
        "chrome": (
            "EXPORT — read EXPORT_FREE_LESTER.md. Write plain .md on Drive. Say: exported."
        ),
    },
    "CAMEL": {
        "cursor": (
            "CAMEL — read session_note.md. Game lane open. Still use Drive for handoff."
        ),
    },
    "DESK": {
        "cursor": "DESK — read FLEET_AVAILABLE.txt. Report fleet green list in plain English.",
        "chrome": "DESK — read FLEET_AVAILABLE.txt on Drive. One paragraph status for Brian.",
    },
    "IDEA": {
        "cursor": (
            "IDEA — prepend one line to MyDrive/IDEAS.txt under the header. "
            "Format: [<time> <machine>] <Brian's words>. Say: on bus."
        ),
        "chrome": (
            "IDEA — prepend one line to MyDrive/IDEAS.txt. Say aloud: on bus."
        ),
    },
}

TARGET_ALIASES: dict[str, set[str]] = {
    "cb1": {"cb1", "uncle", "wrangler", "camel", "cb1 chrome", "cb1 cursor"},
    "cb2": {"cb2", "daddy", "captn", "captain", "penguin", "cb2 chrome", "cb2 cursor"},
    "puppy": {"puppy", "puppy64", "plate", "puppy chrome", "puppy cursor"},
}

ALL_ALIASES = {"all", "every", "fleet", "everywhere", "3 computers", "three computers"}


def _now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def _read_text(path: Path) -> str:
    if not path.is_file():
        return ""
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def _write_text(path: Path, text: str) -> bool:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return True
    except OSError:
        return False


def _load_state() -> dict[str, Any]:
    raw = _read_text(STATE)
    if not raw.strip():
        return {"processed_hashes": [], "last_run": None}
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return {"processed_hashes": [], "last_run": None}
    if not isinstance(data.get("processed_hashes"), list):
        data["processed_hashes"] = []
    return data


def _save_state(data: dict[str, Any]) -> None:
    data["last_run"] = _now()
    _write_text(STATE, json.dumps(data, indent=2))


def normalize_line(line: str) -> tuple[str, list[str]]:
    """Fix typos; return cleaned line + notes."""
    notes: list[str] = []
    out = line.strip()
    if not out or out.startswith("#"):
        return out, notes

    for pat, repl, note in TYPO_WORD:
        if pat.search(out):
            out = pat.sub(repl, out)
            notes.append(note)

    # Brian said LINK — fleet law uses PLATE on Puppy Chrome
    if LINK_CONTEXT.search(out) and not re.search(r"\bPLATE\b", out, re.I):
        notes.append("LINK→use PLATE on Puppy Chrome (LINK is retired/wrong)")
        if re.fullmatch(r"\s*LINK\s*", out, re.I):
            out = "PLATE link puppy"

    return out, notes


def _detect_word(line: str) -> str | None:
    upper = line.upper()
    for word in (
        "UNCLE",
        "DADDY",
        "CAPTN",
        "PUPPY",
        "PLATE",
        "EXPORT",
        "CAMEL",
        "DESK",
        "IDEA",
        "VOICE",
    ):
        if re.search(rf"\b{word}\b", upper):
            return word
    return None


def _detect_targets(line: str) -> set[str]:
    low = line.lower()
    if any(a in low for a in ALL_ALIASES):
        return {"cb1", "cb2", "puppy"}

    found: set[str] = set()
    for target, aliases in TARGET_ALIASES.items():
        for a in aliases:
            if a in low:
                found.add(target)
                break

    word = _detect_word(line)
    if word in ("UNCLE", "CAMEL", "EXPORT") and "EXPORT" in (word or ""):
        found.add("cb1")
    elif word == "UNCLE":
        found.add("cb1")
    elif word in ("DADDY", "CAPTN", "DESK", "IDEA"):
        found.add("cb2")
    elif word in ("PUPPY", "PLATE"):
        found.add("puppy")

    if not found and word:
        if word == "CAMEL":
            found.add("cb1")
        elif word == "EXPORT":
            found.add("cb1")
            found.add("cb2")
            found.add("puppy")
        elif word == "IDEA":
            return {"cb1", "cb2", "puppy"}

    return found


def _custom_tail(line: str, word: str | None) -> str:
    if not word:
        return line
    m = re.search(rf"\b{word}\b\s*[—\-:]?\s*(.+)", line, re.I)
    if m:
        return m.group(1).strip()
    if ":" in line:
        return line.split(":", 1)[1].strip()
    return ""


def _paste_for(slot: str, word: str, custom: str) -> str:
    blocks = PASTE_BLOCKS.get(word, {})
    base = blocks.get(slot, "")
    if not base and word == "CAPTN" and slot == "cursor":
        base = PASTE_BLOCKS["CAPTN"]["cursor"]
    if not base:
        return ""
    if custom:
        return f"{base}\n\nBrian also said: {custom}"
    return base


def route_line(raw_line: str) -> dict[str, Any]:
    line, fix_notes = normalize_line(raw_line)
    word = _detect_word(line)
    targets = _detect_targets(line)
    custom = _custom_tail(line, word)

    if not targets and line:
        targets = {"cb2"}
        fix_notes.append("no machine named — default CB2 CAPTN")

    if not word and line:
        word = "CAPTN" if "cb2" in targets else "UNCLE" if targets == {"cb1"} else "PUPPY"
        fix_notes.append(f"inferred wake word {word}")

    pastes: dict[str, str] = {}

    if "cb1" in targets:
        if word in ("UNCLE", "CAMEL", "DESK", "IDEA"):
            w = word
        else:
            w = "UNCLE"
        c = _paste_for("cursor", w, custom)
        h = _paste_for("chrome", w if w != "CAMEL" else "UNCLE", custom)
        if c:
            pastes["cb1_cursor"] = c
        if h:
            pastes["cb1_chrome"] = h

    if "cb2" in targets:
        w = word if word in ("DADDY", "CAPTN", "DESK", "IDEA", "EXPORT") else "CAPTN"
        c = _paste_for("cursor", w, custom)
        h = _paste_for("chrome", "DADDY" if w != "EXPORT" else "EXPORT", custom)
        if c:
            pastes["cb2_cursor"] = c
        if h:
            pastes["cb2_chrome"] = h

    if "puppy" in targets:
        w = "PUPPY" if word not in ("PLATE", "EXPORT", "IDEA") else word
        c = _paste_for("cursor", "PUPPY", custom)
        h = _paste_for("chrome", "PLATE" if w != "EXPORT" else "EXPORT", custom)
        if LINK_CONTEXT.search(line):
            h = (
                "PLATE — bind slave now (LINK is wrong word). "
                "Read PLATE_BIND_NOW.md + lester6_puppy_slave.md. "
                "Overwrite lester6_to_puppy.md. Say: PLATE ready."
            )
            if custom:
                h += f"\n\nBrian also said: {custom}"
        if c:
            pastes["puppy_cursor"] = c
        if h:
            pastes["puppy_chrome"] = h

    return {
        "raw": raw_line,
        "line": line,
        "word": word,
        "targets": sorted(targets),
        "fix_notes": fix_notes,
        "pastes": pastes,
    }


def _inbox_lines(text: str, marker: str) -> list[str]:
    if marker in text:
        _, below = text.split(marker, 1)
        chunk = below
    else:
        chunk = text
    lines = []
    for ln in chunk.splitlines():
        s = ln.strip()
        if not s or s.startswith("#"):
            continue
        lines.append(s)
    return lines


def _collect_inbox_lines() -> list[tuple[str, str]]:
    """(source_label, line) — TALK.txt first (Brian's front door)."""
    out: list[tuple[str, str]] = []
    talk = _read_text(TALK)
    for ln in _inbox_lines(talk, TALK_MARKER):
        out.append(("TALK.txt", ln))
    inbox = _read_text(INBOX)
    for ln in _inbox_lines(inbox, MARKER):
        out.append(("BRIAN_INBOX.txt", ln))
    return out


def process_inbox() -> list[dict[str, Any]]:
    state = _load_state()
    seen: set[str] = set(state.get("processed_hashes") or [])
    results: list[dict[str, Any]] = []

    for source, raw in _collect_inbox_lines():
        h = hashlib.sha256(f"{source}:{raw}".encode()).hexdigest()[:16]
        if h in seen:
            continue
        seen.add(h)
        r = route_line(raw)
        r["source"] = source
        results.append(r)

    if results:
        state["processed_hashes"] = list(seen)[-200:]
        _save_state(state)
        _write_routed(results)
        _append_mac_inbox(results)

    return results


def _write_routed(results: list[dict[str, Any]]) -> None:
    ROUTED_DIR.mkdir(parents=True, exist_ok=True)
    merged: dict[str, list[str]] = {}

    for r in results:
        for slot, paste in r["pastes"].items():
            merged.setdefault(slot, []).append(paste)

    slot_labels = {
        "cb1_cursor": "CB1 — Cursor (UNCLE)",
        "cb1_chrome": "CB1 — Lester6 Chrome",
        "cb2_cursor": "CB2 — Cursor CAPTN",
        "cb2_chrome": "CB2 — Lester6 Chrome",
        "puppy_cursor": "puppy64 — Cursor PUPPY",
        "puppy_chrome": "puppy64 — Lester6 Chrome PLATE",
    }

    for slot, pastes in merged.items():
        body = pastes[-1]
        header = f"# {slot_labels.get(slot, slot)}\n# Routed {_now()}\n\n"
        _write_text(ROUTED_DIR / f"{slot}.txt", header + body + "\n")

    summary_lines = [
        "# Brian Router — paste once per tab",
        f"Updated: {_now()}",
        "",
        "You typed once in BRIAN_INBOX.txt. Copy from routed/ — do not retype.",
        "",
    ]
    for r in results:
        summary_lines.append(f"## In ({r.get('source', '?')}): {r['raw']}")
        if r["fix_notes"]:
            summary_lines.append(f"Fixed: {', '.join(r['fix_notes'])}")
        summary_lines.append(f"Word: {r.get('word')} → {', '.join(r['targets'])}")
        summary_lines.append("")
        for slot in sorted(r["pastes"]):
            summary_lines.append(f"- fleet/bus/routed/{slot}.txt")
        summary_lines.append("")

    _write_text(SUMMARY, "\n".join(summary_lines) + "\n")


def _append_mac_inbox(results: list[dict[str, Any]]) -> None:
    if not results:
        return
    ts = _now()[:16].replace("T", " ")
    blocks = []
    for r in results:
        fixes = f" fixes: {', '.join(r['fix_notes'])}" if r["fix_notes"] else ""
        blocks.append(
            f"--- from: router | {ts} | typed-once ---\n"
            f"Brian said: {r['raw']}\n"
            f"Routed {r.get('word')} → {', '.join(r['targets'])}{fixes}\n"
            f"Paste files: fleet/bus/routed/ + BRIAN_ROUTED_SUMMARY.txt\n"
        )
    try:
        prev = _read_text(MAC_INBOX)
        _write_text(MAC_INBOX, "\n".join(blocks) + prev)
    except OSError:
        pass


def ensure_inbox_template() -> None:
    if not TALK.is_file():
        tpl = (
            "BRIAN — talk here. One file. Any device.\n\n"
            f"{TALK_MARKER}\n"
        )
        _write_text(TALK, tpl)
    if INBOX.is_file():
        return
    tpl = (
        "# Brian — type ONE line here. Router fans out to 3 computers.\n"
        "# Examples:\n"
        "#   ALL: link puppy\n"
        "#   DADDY\n"
        "#   PUPPY run story mine phase 1\n"
        "#   UNCLE EXPORT\n"
        f"\n{MARKER}\n"
    )
    _write_text(INBOX, tpl)


def watch(interval: float = 12.0) -> None:
    ensure_inbox_template()
    print(f"Brian Router watching {TALK} + {INBOX} every {interval}s", flush=True)
    while True:
        try:
            n = process_inbox()
            if n:
                print(f"Routed {len(n)} line(s) → see {SUMMARY}", flush=True)
        except Exception as exc:
            print(f"router error: {exc}", flush=True)
        time.sleep(interval)


def main() -> None:
    ensure_inbox_template()
    cmd = sys.argv[1] if len(sys.argv) > 1 else "once"
    if cmd == "once":
        done = process_inbox()
        if not done:
            print("Nothing new in BRIAN_INBOX.txt")
            return
        print(_read_text(SUMMARY))
    elif cmd == "watch":
        watch(float(sys.argv[2]) if len(sys.argv) > 2 else 12.0)
    elif cmd == "route":
        line = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else ""
        if not line:
            print("Usage: brian_router.py route <one line>")
            return
        r = route_line(line)
        print(json.dumps(r, indent=2))
    else:
        print("Usage: brian_router.py [once|watch|route <line>]")


if __name__ == "__main__":
    main()
