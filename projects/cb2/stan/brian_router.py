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
LOOP_POKE = DRIVE_ROOT / "drop_pile" / "to_bbbunny" / "LOOP.txt"
DONE_FEED = FLEET_BUS / "DONE_FEED.txt"

MARKER = "--- TYPE BELOW (one line) ---"
TALK_MARKER = "--- type below ---"

# Brian typos / retired words → fleet law (fleet/NAMING_LAW.txt)
TYPO_WORD: list[tuple[re.Pattern[str], str, str]] = [
    (re.compile(r"\bADDY\b", re.I), "DADDY", "ADDY→DADDY"),
    (re.compile(r"\bDADY\b", re.I), "DADDY", "DADY→DADDY"),
    (re.compile(r"\bCPT\b", re.I), "DADDY", "CPT→DADDY (retired alias)"),
    (re.compile(r"\bCAPTIN\b", re.I), "DADDY", "CAPTIN→DADDY"),
    (re.compile(r"\bCAPTAN\b", re.I), "DADDY", "CAPTAN→DADDY"),
    (re.compile(r"\bCAPTAIN\b", re.I), "DADDY", "CAPTAIN→DADDY"),
    (re.compile(r"\bCAPTN\b", re.I), "DADDY", "CAPTN→DADDY"),
    (re.compile(r"\bBEACON\b", re.I), "DADDY", "BEACON→DADDY (retired)"),
    (re.compile(r"\bWRANGLER\b", re.I), "UNCLE", "WRANGLER→UNCLE (retired)"),
    (re.compile(r"\bSTUDIO\b", re.I), "UNCLE", "STUDIO→UNCLE (retired)"),
    (re.compile(r"\bNET\b", re.I), "PUPPY", "NET→PUPPY (retired alias)"),
    (re.compile(r"\bPLATE\b", re.I), "PUPPY", "PLATE→PUPPY (retired)"),
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
        "cursor": "PUPPY — open https://hitme.dev/puppy · run the one command · post CHECKIN.",
        "chrome": (
            "PUPPY — open https://hitme.dev/puppy in Firefox · run ONE_COMMAND · post CHECKIN."
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
    "BUNNY": {
        "cursor": (
            "BUNNY — read fleet/indie_loop/TO_BUNNY.txt · fleet/bus/CPT_BUNNY_LOOP.txt. "
            "Post FROM_BUNNY · done audio per fleet/AUDIO_DONE.txt · Word: LOOP when finished."
        ),
        "chrome": (
            "BUNNY — read TO_BUNNY.txt on Drive · builder lane · post drop_pile/from_bbbunny/"
        ),
    },
    "LOOP": {
        "cursor": (
            "LOOP — Brian said one word · run now: "
            "bash ~/GoogleDrive/MyDrive/lester/bunny_loop_fix.sh"
        ),
        "chrome": (
            "LOOP — Brian said one word · tell Cursor on Bunny box to run bunny_loop_fix.sh"
        ),
    },
    "BUDDY": {
        "chrome": (
            "BUDDY — read fleet/CPT_BUDDY.txt · fleet/bus/cpt_to_gem.txt · "
            "fleet/bus/BUDDY_INBOX.txt. Plain .txt only — never Google Docs. "
            "Do ONE step · post gem_to_cpt + GEM_UNDERSTAND."
        ),
    },
    "GEM": {
        "chrome": (
            "GEM — read fleet/NAMING_LAW.txt · drop_pile/to_gemini/GEM_SELF_FIX.txt. "
            "You are loader on CB1 · not Daddy. Do ONE step · post gem_to_cpt · "
            "tell Uncle: bash ~/.stan/uncle_exec.sh on CB1 Linux only."
        ),
    },
    "NET": {
        "cursor": (
            "NET — read fleet/bus/cpt_to_puppy.txt · fleet/bus/NET_INBOX.txt. "
            "Post puppy_outbox when up · run recovery scripts if down."
        ),
        "chrome": (
            "PLATE — read fleet/bus/NET_INBOX.txt · cpt_to_puppy.txt. "
            "Post puppy_outbox plain txt."
        ),
    },
}

LANE_INBOX: dict[str, Path] = {
    "BUDDY": FLEET_BUS / "BUDDY_INBOX.txt",
    "GEM": FLEET_BUS / "BUDDY_INBOX.txt",
    "CPT": FLEET_BUS / "CPT_BRIAN_INBOX.txt",
    "CAPTN": FLEET_BUS / "CPT_BRIAN_INBOX.txt",
    "NET": FLEET_BUS / "NET_INBOX.txt",
    "PUPPY": FLEET_BUS / "NET_INBOX.txt",
    "UNCLE": FLEET_BUS / "UNCLE_INBOX.txt",
}

TARGET_ALIASES: dict[str, set[str]] = {
    "cb1": {"cb1", "uncle", "wrangler", "camel", "cb1 chrome", "cb1 cursor", "studio", "gem", "gemini"},
    "cb2": {"cb2", "daddy", "captn", "captain", "penguin", "cb2 chrome", "cb2 cursor", "cpt", "buddy", "beacon"},
    "puppy": {"puppy", "puppy64", "plate", "puppy chrome", "puppy cursor", "net", "bunny", "bun", "bbunny"},
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


def _loop_poke(*, who: str = "Brian") -> None:
    """Brian typed LOOP — Daddy pokes Bunny · no bash for Brian."""
    ts = _now()
    _write_text(
        LOOP_POKE,
        "\n".join(
            [
                "LOOP",
                f"time: {ts}",
                f"from: {who} · one word",
                "run: bash ~/GoogleDrive/MyDrive/lester/bunny_loop_fix.sh",
            ]
        )
        + "\n",
    )
    row = f"{ts} · daddy · loop · https://hitme.dev/f/drop_pile/to_bbbunny/LOOP.txt · Brian said LOOP\n"
    prev = _read_text(DONE_FEED)
    if "DONE FEED" not in prev:
        prev = "DONE FEED — mobile tap-to-play · append only\nLaw: fleet/AUDIO_DONE.txt\n\n"
    _write_text(DONE_FEED, prev + row)


def _detect_word(line: str) -> str | None:
    if re.fullmatch(r"\s*LOOP\s*", line, re.I):
        return "LOOP"
    upper = line.upper()
    for word in (
        "BUNNY",
        "BUDDY",
        "GEM",
        "NET",
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
        "CPT",
        "LOOP",
        "CLERK",
    ):
        if re.search(rf"\b{word}\b", upper):
            if word in ("CPT", "CAPTN"):
                return "DADDY"
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
    elif word in ("DADDY", "CAPTN", "DESK", "IDEA", "BUDDY", "CPT"):
        found.add("cb2")
    elif word == "GEM":
        found.add("cb1")
    elif word == "CLERK":
        found.add("cb1")
    elif word == "BUNNY":
        found.add("puppy")
    elif word == "LOOP":
        found.add("puppy")
    elif word in ("PUPPY", "PLATE", "NET"):
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

    if word == "LOOP":
        _loop_poke()
        targets = {"puppy"}
        fix_notes.append("LOOP → Daddy poked Bunny · Brian types one word only")

    if not targets and line and word != "LOOP":
        targets = {"cb2"}
        fix_notes.append("no machine named — default Daddy (penguin)")

    if not word and line:
        word = "DADDY" if "cb2" in targets else "UNCLE" if targets == {"cb1"} else "PUPPY"
        fix_notes.append(f"inferred wake word {word}")

    pastes: dict[str, str] = {}

    if "cb1" in targets:
        if word in ("UNCLE", "CAMEL", "DESK", "IDEA"):
            w = word
        elif word == "GEM":
            w = "GEM"
        else:
            w = "UNCLE"
        c = _paste_for("cursor", w if w != "GEM" else "UNCLE", custom)
        h = _paste_for("chrome", w, custom)
        if c:
            pastes["cb1_cursor"] = c
        if h:
            pastes["cb1_chrome"] = h

    if word in ("BUDDY", "GEM"):
        try:
            import subprocess

            gem_loop = Path.home() / ".stan" / "cpt_gem_loop.py"
            subprocess.run(
                [sys.executable, str(gem_loop), "forward"],
                capture_output=True,
                timeout=15,
            )
        except (OSError, subprocess.SubprocessError):
            pass

    if "cb2" in targets:
        if word in ("BUDDY",):
            w = "BUDDY"
            h = _paste_for("chrome", w, custom)
            if h:
                pastes["cb2_chrome"] = h
        else:
            w = word if word in ("DADDY", "CAPTN", "DESK", "IDEA", "EXPORT", "CPT") else "DADDY"
            c = _paste_for("cursor", w, custom)
            h = _paste_for("chrome", "DADDY" if w != "EXPORT" else "EXPORT", custom)
            if c:
                pastes["cb2_cursor"] = c
            if h:
                pastes["cb2_chrome"] = h

    if "puppy" in targets:
        if word == "LOOP":
            w = "LOOP"
        elif word == "BUNNY":
            w = "BUNNY"
        else:
            w = "NET" if word == "NET" else ("PUPPY" if word not in ("PLATE", "EXPORT", "IDEA") else word)
        c = _paste_for("cursor", w if w in ("LOOP", "BUNNY") else "PUPPY", custom)
        if w in ("LOOP", "BUNNY"):
            h = _paste_for("cursor", w, custom)
        elif w == "EXPORT":
            h = _paste_for("chrome", "EXPORT", custom)
        else:
            h = _paste_for("chrome", "PLATE", custom)
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
        _append_lane_inboxes(results)
        _append_mac_inbox(results)

    return results


def _append_lane_inboxes(results: list[dict[str, Any]]) -> None:
    """Per-lane inbox files — Buddy/NET/Uncle read their own."""
    for r in results:
        word = (r.get("word") or "").upper()
        if word == "GEM":
            word = "BUDDY"
        path = LANE_INBOX.get(word)
        if not path:
            continue
        if not path.is_file():
            _write_text(
                path,
                f"# Brian → {word} inbox · plain lines below\n\n{MARKER}\n\n",
            )
        prev = _read_text(path)
        line = f"[{_now()}] {r['raw']}\n"
        if MARKER in prev:
            head, _ = prev.split(MARKER, 1)
            _write_text(path, f"{head}{MARKER}\n\n{line}")
        else:
            _write_text(path, prev + line)


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
        "cb2_chrome": "CB2 — Buddy (Gem pane)",
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
        "#   BUDDY export keys\n"
        "#   NET recovery when back\n"
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
