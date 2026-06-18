#!/usr/bin/env python3
"""George — find and read Brian's Drive docs (.txt · .md)."""
from __future__ import annotations

import re
from pathlib import Path

from bus_lane import bus_root, safe_is_file, safe_read_text

READ_EXTS = (".txt", ".md", ".json")
SHALLOW_DIRS = (
    "fleet/bus",
    "fleet/indie_loop",
    "drop_pile/from_daddy",
    "drop_pile/from_bbbunny",
    "drop_pile/to_cursor",
    "inbox",
)
MAX_READ = 6000
MAX_SAY = 1800


def _tokens(name: str) -> list[str]:
    return [t for t in re.findall(r"[a-z0-9]+", name.lower()) if len(t) > 2]


def _token_in(text: str, token: str) -> bool:
    return bool(re.search(rf"(?:^|[^a-z0-9]){re.escape(token)}(?:[^a-z0-9]|$)", text, re.I))


def _score(name: str, tokens: list[str]) -> int:
    low = name.lower()
    if not tokens:
        return 0
    hits = sum(1 for t in tokens if _token_in(low, t))
    if hits == 0:
        return 0
    if hits == len(tokens):
        return hits + 10
    return hits


def _files_in_dir(base: Path, *, depth: int = 2) -> list[Path]:
    out: list[Path] = []
    if not base.is_dir():
        return out
    try:
        for path in base.rglob("*"):
            if not path.is_file():
                continue
            try:
                if len(path.relative_to(base).parts) > depth:
                    continue
            except ValueError:
                continue
            out.append(path)
    except OSError:
        pass
    return out


def _root_hits(bus: Path, tokens: list[str]) -> list[tuple[Path, int]]:
    hits: list[tuple[Path, int]] = []
    try:
        for path in bus.iterdir():
            if not path.is_file():
                continue
            sc = _score(path.name, tokens)
            if sc > 0:
                hits.append((path, sc + 8))
    except OSError:
        pass
    return hits


def find_doc(query: str, *, limit: int = 5) -> list[tuple[Path, int]]:
    bus = bus_root()
    tokens = _tokens(query)
    if not tokens:
        return []
    hits: list[tuple[Path, int]] = []
    for path, sc in _root_hits(bus, tokens):
        if path.suffix.lower() in READ_EXTS and sc >= len(tokens):
            hits.append((path, sc))
    seen = {str(p) for p, _ in hits}
    for rel in SHALLOW_DIRS:
        base = bus / rel
        if not base.is_dir():
            continue
        try:
            for path in base.iterdir():
                if not path.is_file() or path.suffix.lower() not in READ_EXTS:
                    continue
                key = str(path)
                if key in seen:
                    continue
                seen.add(key)
                sc = _score(path.name, tokens)
                if sc >= len(tokens):
                    hits.append((path, sc))
        except OSError:
            continue
    hits.sort(key=lambda x: (-x[1], -x[0].stat().st_mtime if x[0].is_file() else 0))
    return hits[:limit]


def find_any_name(query: str) -> list[Path]:
    bus = bus_root()
    tokens = _tokens(query)
    out: list[tuple[Path, int, float]] = []
    for path, sc in _root_hits(bus, tokens):
        try:
            out.append((path, sc, path.stat().st_mtime))
        except OSError:
            out.append((path, sc, 0))
    out.sort(key=lambda x: (-x[1], -x[2]))
    return [p for p, _, _ in out[:5]]


def read_doc(path: Path) -> str:
    if not safe_is_file(path):
        return ""
    return safe_read_text(path).strip()[:MAX_READ]


def extract_doc_query(heard: str) -> str | None:
    low = heard.lower().strip()
    patterns = (
        r'(?:check|read|open|analyze|look at|summarize|review)\s+(?:the\s+)?(?:new\s+)?(?:doc(?:ument)?\s+)?["\']?(.+?)["\']?\s*(?:analyze|please|$)',
        r'(?:doc(?:ument)?)\s+["\']?(.+?)["\']?\s*(?:analyze|please|$)',
        r'["\']([^"\']{3,80})["\']',
    )
    for pat in patterns:
        m = re.search(pat, low, re.I)
        if m:
            q = m.group(1).strip(" .,-")
            q = re.sub(r"\s+(analyze it|please|for me)$", "", q, flags=re.I).strip()
            if len(q) >= 3:
                return q
    return None


def summarize_for_voice(title: str, body: str, *, cap: int = MAX_SAY) -> str:
    text = re.sub(r"\s+", " ", body).strip()
    if not text:
        return f"I found {title} but it looks empty."
    if len(text) <= cap:
        return f"{title}: {text}"
    cut = text[: cap - 1].rsplit(" ", 1)[0]
    return f"{title}: {cut}… (say read more for the rest)"


def try_doc(heard: str) -> tuple[str, list[str], str | None] | None:
    if not re.search(r"\b(doc|document|gdoc|google|analyze|read|check|summarize|review)\b", heard, re.I):
        return None
    query = extract_doc_query(heard) or heard
    tokens = _tokens(query)
    if not tokens:
        return None

    any_hits = find_any_name(query)
    gdoc_full = [p for p in any_hits if p.suffix.lower() == ".gdoc" and _score(p.name, tokens) >= len(tokens) + 10]
    if gdoc_full:
        name = gdoc_full[0].name
        return (
            f"I found {name} on Drive — it's a Google Doc, not plain text yet. "
            "Ask Daddy to export a .txt copy, then I can read the whole thing.",
            ["doc:gdoc-only"],
            None,
        )

    readable = find_doc(query)
    if readable:
        path, _ = readable[0]
        rel = path.relative_to(bus_root())
        body = read_doc(path)
        title = path.stem.replace("_", " ")
        msg = summarize_for_voice(title, body)
        return msg, [f"doc:{rel}"], None

    any_hits = find_any_name(query)
    gdoc = [p for p in any_hits if p.suffix.lower() == ".gdoc"]
    if gdoc:
        name = gdoc[0].name
        return (
            f"I see {name} on Drive but it's a Google Doc — not plain text yet. "
            "Ask Daddy to export it, or save a .txt copy on Drive.",
            ["doc:gdoc-only"],
            None,
        )

    if any_hits:
        names = ", ".join(p.name for p in any_hits[:3])
        return f"I couldn't read those — wrong format maybe. Closest: {names}.", ["doc:miss"], None

    return None
