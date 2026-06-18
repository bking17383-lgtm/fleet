#!/usr/bin/env python3
"""
Fleet Convert — drop RTF / Keep export / HTML → plain .md + .txt on Drive.

Inbox:  MyDrive/convert_inbox/
Out:     MyDrive/convert_outbox/
Work:    MyDrive/convert_work/   (optional RTF rebuild scratch)

Usage:
  python3 ~/.stan/fleet_convert.py once
  python3 ~/.stan/fleet_convert.py watch
  python3 ~/.stan/fleet_convert.py convert path/to/file.rtf
"""

from __future__ import annotations

import hashlib
import json
import re
import shutil
import sys
import time
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

try:
    from striprtf.striprtf import rtf_to_text as _rtf_to_text
except ImportError:

    def _rtf_to_text(raw: str) -> str:
        t = re.sub(r"\\par[d]?\s*", "\n", raw)
        t = re.sub(r"\\line\s*", "\n", t)
        t = re.sub(r"\\tab\s*", "\t", t)
        t = re.sub(r"\\'[0-9a-fA-F]{2}", lambda m: bytes.fromhex(m.group(0)[2:]).decode("latin-1", "replace"), t)
        t = re.sub(r"\\[a-z]+-?\d*\s?", "", t)
        t = re.sub(r"[{}]", "", t)
        return re.sub(r"\n{3,}", "\n\n", t).strip()


DRIVE = Path("/mnt/shared/GoogleDrive/MyDrive")
if not DRIVE.is_dir():
    alt = Path.home() / "GoogleDrive/MyDrive"
    if alt.is_dir():
        DRIVE = alt

INBOX = DRIVE / "convert_inbox"
OUTBOX = DRIVE / "convert_outbox"
WORK = DRIVE / "convert_work"
STATE = DRIVE / "convert_inbox" / ".fleet_convert_state.json"
GDOC_STUB_MAX = 512
SUPPORTED = {".rtf", ".html", ".htm", ".json", ".txt", ".md", ".zip"}
SKIP_NAMES = {".fleet_convert_state.json", "CONVERT_LOG.txt", "README.txt"}


def _should_skip(path: Path) -> bool:
    if path.name.startswith("."):
        return True
    if path.name in SKIP_NAMES:
        return True
    suffix = path.suffix.lower()
    if suffix not in SUPPORTED and not path.name.lower().endswith(".gdoc"):
        return True
    return False


class _HTMLText(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        s = data.strip()
        if s:
            self.parts.append(s)

    def text(self) -> str:
        return "\n".join(self.parts)


def _now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def _slug(name: str, n: int = 48) -> str:
    s = re.sub(r"[^a-zA-Z0-9_-]+", "-", name.strip().lower()).strip("-")
    return (s or "note")[:n]


def _is_gdoc_stub(path: Path) -> bool:
    if path.suffix.lower() != ".gdoc":
        return False
    try:
        return path.stat().st_size <= GDOC_STUB_MAX
    except OSError:
        return False


def _load_state() -> dict[str, Any]:
    if not STATE.is_file():
        return {"done": {}}
    try:
        return json.loads(STATE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {"done": {}}


def _save_state(state: dict[str, Any]) -> None:
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(state, indent=2), encoding="utf-8")


def _file_hash(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()[:20]


def text_to_rtf(plain: str, title: str = "") -> str:
    """Rebuild minimal RTF — portable intermediate."""
    esc = plain.replace("\\", "\\\\").replace("{", "\\{").replace("}", "\\}")
    esc = esc.replace("\n", "\\par\n")
    head = f"{{\\rtf1\\ansi {title}\\par\\par " if title else "{\\rtf1\\ansi "
    return head + esc + "}"


def parse_rtf(raw: str) -> str:
    return _rtf_to_text(raw).strip()


def parse_html(raw: str) -> str:
    p = _HTMLText()
    p.feed(raw)
    return p.text()


def parse_keep_json(data: Any) -> list[dict[str, str]]:
    notes: list[dict[str, str]] = []

    def one(obj: dict[str, Any]) -> None:
        title = (obj.get("title") or obj.get("name") or "").strip()
        body = (obj.get("textContent") or obj.get("text") or obj.get("content") or "").strip()
        if not body and isinstance(obj.get("listContent"), list):
            lines = []
            for item in obj["listContent"]:
                if isinstance(item, dict):
                    t = (item.get("text") or "").strip()
                    ck = item.get("isChecked")
                    lines.append(f"[{'x' if ck else ' '}] {t}")
            body = "\n".join(lines)
        if title or body:
            notes.append({"title": title or "keep note", "body": body})

    if isinstance(data, dict):
        if "notes" in data and isinstance(data["notes"], list):
            for n in data["notes"]:
                if isinstance(n, dict):
                    one(n)
        elif "textContent" in data or "title" in data:
            one(data)
        else:
            for v in data.values():
                if isinstance(v, dict):
                    one(v)
                elif isinstance(v, list):
                    for item in v:
                        if isinstance(item, dict):
                            one(item)
    elif isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                one(item)
    return notes


def parse_json(raw: str) -> list[dict[str, str]]:
    data = json.loads(raw)
    return parse_keep_json(data)


def extract_from_zip(path: Path, dest: Path) -> list[Path]:
    import zipfile

    dest.mkdir(parents=True, exist_ok=True)
    found: list[Path] = []
    with zipfile.ZipFile(path, "r") as zf:
        for name in zf.namelist():
            low = name.lower()
            if not any(low.endswith(ext) for ext in (".json", ".html", ".htm", ".rtf", ".txt")):
                continue
            if "__MACOSX" in name:
                continue
            target = dest / Path(name).name
            target.write_bytes(zf.read(name))
            found.append(target)
    return found


def convert_file(path: Path) -> dict[str, Any]:
    result: dict[str, Any] = {
        "source": str(path),
        "ok": False,
        "outputs": [],
        "error": None,
    }
    suffix = path.suffix.lower()

    if _is_gdoc_stub(path):
        result["error"] = (
            "Google Doc stub (.gdoc) — Linux cannot read body. "
            "In Chrome: File → Download → Rich Text (.rtf) → drop in convert_inbox/"
        )
        return result

    try:
        if suffix == ".zip":
            tmp = WORK / f"zip_{_slug(path.stem)}"
            if tmp.exists():
                shutil.rmtree(tmp)
            extracted = extract_from_zip(path, tmp)
            all_out: list[str] = []
            for f in extracted:
                sub = convert_file(f)
                all_out.extend(sub.get("outputs", []))
            result["outputs"] = all_out
            result["ok"] = bool(all_out)
            return result

        raw = path.read_text(encoding="utf-8", errors="replace")
        notes: list[dict[str, str]] = []

        if suffix == ".rtf":
            plain = parse_rtf(raw)
            notes = [{"title": path.stem, "body": plain}]
        elif suffix in (".html", ".htm"):
            plain = parse_html(raw)
            notes = [{"title": path.stem, "body": plain}]
        elif suffix == ".json":
            notes = parse_json(raw)
        elif suffix in (".txt", ".md"):
            notes = [{"title": path.stem, "body": raw.strip()}]
        else:
            result["error"] = f"unsupported type: {suffix}"
            return result

        OUTBOX.mkdir(parents=True, exist_ok=True)
        WORK.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")

        for i, note in enumerate(notes):
            title = note["title"]
            body = note["body"]
            if not body:
                continue
            slug = _slug(title)
            base = f"{ts}_{slug}" if len(notes) == 1 else f"{ts}_{i+1}_{slug}"

            # Rebuild RTF intermediate (utility core)
            rtf_path = WORK / f"{base}.rtf"
            rtf_path.write_text(text_to_rtf(body, title), encoding="utf-8")

            md_path = OUTBOX / f"{base}.md"
            md = f"# {title}\n\nconverted: {_now()}\nsource: {path.name}\n\n{body}\n"
            md_path.write_text(md, encoding="utf-8")

            txt_path = OUTBOX / f"{base}.txt"
            txt_path.write_text(body + "\n", encoding="utf-8")

            result["outputs"].extend([str(rtf_path.relative_to(DRIVE)), str(md_path.relative_to(DRIVE)), str(txt_path.relative_to(DRIVE))])

            # Fleet routing by filename hint
            low = path.name.lower()
            if low.startswith("idea") or "idea" in low or "keep" in low:
                ideas = DRIVE / "fleet" / "bus" / "IDEAS.txt"
                ideas.parent.mkdir(parents=True, exist_ok=True)
                line = f"[{_now()[:16]} convert] {body.splitlines()[0][:200]}\n"
                if ideas.is_file():
                    prev = ideas.read_text(encoding="utf-8", errors="replace")
                else:
                    prev = "# IDEAS BUS → CAPTN (newest on top)\n\n"
                ideas.write_text(prev.rstrip() + "\n" + line, encoding="utf-8")
                result.setdefault("routed", []).append("fleet/bus/IDEAS.txt")

            if low.startswith("talk") or low.startswith("captn") or "fleet" in low:
                talk = DRIVE / "TALK.txt"
                if talk.is_file():
                    prev = talk.read_text(encoding="utf-8", errors="replace")
                else:
                    prev = "--- type below ---\n"
                talk.write_text(prev.rstrip() + f"\n\n[{_now()[:16]} convert] {body.splitlines()[0][:300]}\n", encoding="utf-8")
                result.setdefault("routed", []).append("TALK.txt")

        result["ok"] = bool(result["outputs"])
        if not result["ok"] and not result["error"]:
            result["error"] = "no text extracted"
    except Exception as exc:
        result["error"] = str(exc)
    return result


def process_inbox() -> list[dict[str, Any]]:
    INBOX.mkdir(parents=True, exist_ok=True)
    state = _load_state()
    done: dict[str, str] = state.setdefault("done", {})
    results: list[dict[str, Any]] = []

    for path in sorted(INBOX.iterdir()):
        if not path.is_file() or _should_skip(path):
            continue
        fh = _file_hash(path)
        if done.get(path.name) == fh:
            continue
        r = convert_file(path)
        r["file"] = path.name
        results.append(r)
        if r.get("ok") or r.get("error"):
            done[path.name] = fh

    state["updated"] = _now()
    _save_state(state)

    log = INBOX / "CONVERT_LOG.txt"
    if results:
        lines = [f"\n--- {_now()} ---"]
        for r in results:
            if r.get("ok"):
                lines.append(f"OK  {r['file']} → {', '.join(r.get('outputs', [])[:2])}…")
                for route in r.get("routed", []):
                    lines.append(f"    routed → {route}")
            else:
                lines.append(f"FAIL {r['file']}: {r.get('error', '?')}")
        with log.open("a", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
    return results


def watch(interval: float = 15.0) -> None:
    print(f"Fleet Convert watching {INBOX}", flush=True)
    while True:
        try:
            n = process_inbox()
            if n:
                print(f"Converted {sum(1 for x in n if x.get('ok'))} file(s)", flush=True)
        except Exception as exc:
            print(f"convert error: {exc}", flush=True)
        time.sleep(interval)


def main() -> None:
    cmd = sys.argv[1] if len(sys.argv) > 1 else "once"
    if cmd == "once":
        done = process_inbox()
        if not done:
            print(f"Nothing new in {INBOX}")
            return
        for r in done:
            print(json.dumps(r, indent=2))
    elif cmd == "watch":
        watch(float(sys.argv[2]) if len(sys.argv) > 2 else 15.0)
    elif cmd == "convert" and len(sys.argv) > 2:
        p = Path(sys.argv[2])
        print(json.dumps(convert_file(p), indent=2))
    else:
        print("Usage: fleet_convert.py [once|watch|convert <file>]")


if __name__ == "__main__":
    main()
