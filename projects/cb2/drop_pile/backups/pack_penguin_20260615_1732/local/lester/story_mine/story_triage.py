#!/usr/bin/env python3
"""Story Mine Phase 2 — triage exported .md for practical inventions + novelty formats.

Reads stories_export/raw/*.md (Phase 1 export required).
Writes stories_export/catalog/triage_report.json + TRIAGE_PICKS.md

Usage:
  python3 story_triage.py              # scan all exported md
  python3 story_triage.py --dry      # report export gap only
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

DRIVE = Path("/mnt/shared/GoogleDrive/MyDrive")
if not DRIVE.is_dir():
    DRIVE = Path.home() / "GoogleDrive/MyDrive"

RAW = DRIVE / "stories_export/raw"
CATALOG = DRIVE / "stories_export/catalog"
INDEX = CATALOG / "story_index.json"
OUT_JSON = CATALOG / "triage_report.json"
OUT_MD = CATALOG / "TRIAGE_PICKS.md"

# Skip award-winner / contest / polished laureate material (title + body)
AWARD_SKIP = re.compile(
    r"award.?winner|won (the|a) prize|first place|contest winner|"
    r"pulitzer|nobel prize|published in|anthology|best of|"
    r"list of good short stories",
    re.I,
)

INVENT_LINE = re.compile(
    r"^\s*\$?\s*invent\s*[:.\-]\s*(.+)$",
    re.I | re.M,
)
INVENT_TITLE = re.compile(r"\$?\s*invent", re.I)

PRACTICAL = re.compile(
    r"practical|life hack|you could (actually )?build|patent|prototype|"
    r"how to make|instructions|materials:|parts list|blueprint",
    re.I,
)

NOVELTY_GROSS = re.compile(
    r"gross\s+out|little (brother|sister)|younger (bro|sis)|"
    r"ways to (gross|disgust|prank|annoy)|sibling|yuck factor|"
    r"make (him|her) (puke|gag|scream)",
    re.I,
)

LIST_FORMAT = re.compile(
    r"^\s*(\d+[\.\)]\s+|[-*•]\s+|ways to |how to |list of )",
    re.I | re.M,
)

STARTER = re.compile(
    r"^(start|draft|idea|notes|untitled|wip|fragment)\b",
    re.I,
)


def load_index() -> dict[str, dict]:
    if not INDEX.is_file():
        return {}
    data = json.loads(INDEX.read_text(encoding="utf-8"))
    return {e["id"]: e for e in data.get("entries", [])}


def word_count(text: str) -> int:
    return len(re.findall(r"\S+", text))


def classify_starter(title: str, text: str, wc: int) -> bool:
    if STARTER.search(title.strip()):
        return True
    if wc < 120:
        return True
    if wc < 400 and not LIST_FORMAT.search(text) and not INVENT_LINE.search(text):
        return True
    return False


def scan_file(path: Path, meta: dict | None) -> dict:
    title = meta.get("title", path.stem) if meta else path.stem
    text = path.read_text(encoding="utf-8", errors="replace")
    wc = word_count(text)
    skip_award = bool(AWARD_SKIP.search(title) or AWARD_SKIP.search(text[:8000]))

    inventions = [m.group(1).strip() for m in INVENT_LINE.finditer(text)]
    invent_in_title = bool(INVENT_TITLE.search(title))

    gross_hits = len(NOVELTY_GROSS.findall(text[:12000]))
    list_lines = len(LIST_FORMAT.findall(text[:12000]))
    practical_hits = len(PRACTICAL.findall(text[:12000]))

    starter = classify_starter(title, text, wc)

    score = 0
    if inventions:
        score += 10 + len(inventions) * 2
    if invent_in_title:
        score += 5
    if practical_hits:
        score += min(practical_hits, 8)
    if list_lines >= 5:
        score += 6
    if gross_hits:
        score += 4
    if starter:
        score -= 5
    if skip_award:
        score -= 100

    return {
        "id": meta.get("id", path.stem) if meta else path.stem,
        "title": title.strip(),
        "path": str(path.relative_to(DRIVE)),
        "word_count": wc,
        "skip_award": skip_award,
        "starter": starter,
        "inventions": inventions[:50],
        "invention_count": len(inventions),
        "invent_in_title": invent_in_title,
        "list_line_count": list_lines,
        "gross_sibling_signals": gross_hits,
        "practical_signals": practical_hits,
        "score": score,
    }


def slug_from_export(path: Path) -> str:
    return path.stem


def write_markdown(rows: list[dict], exported_n: int, total_index: int) -> None:
    inv = sorted(
        [r for r in rows if r["invention_count"] or r["invent_in_title"]],
        key=lambda x: -x["score"],
    )
    novelty = sorted(
        [r for r in rows if r["gross_sibling_signals"] or r["list_line_count"] >= 8],
        key=lambda x: -x["score"],
    )
    practical = sorted(
        [r for r in rows if r["practical_signals"] and not r["starter"]],
        key=lambda x: -x["score"],
    )
    starters = [r for r in rows if r["starter"] and not r["skip_award"]]

    lines = [
        "# Story Mine — triage picks",
        f"Updated: {datetime.now(timezone.utc).isoformat()}",
        f"Exported files scanned: **{exported_n}** / index **{total_index}**",
        "",
        "## Practical inventions",
        "",
    ]
    if inv:
        for r in inv[:40]:
            invs = "; ".join(r["inventions"][:3]) or "(title flag)"
            lines.append(f"- **{r['title']}** — {r['invention_count']} invent line(s) · {invs}")
    else:
        lines.append("_No exports yet — run Phase 1 export._")

    lines += ["", "## Novelty / list format (gross-out sibling lane)", ""]
    if novelty:
        for r in novelty[:25]:
            lines.append(
                f"- **{r['title']}** — list lines {r['list_line_count']} · "
                f"gross/sibling hits {r['gross_sibling_signals']}"
            )
    else:
        lines.append("_Pending export._")

    lines += ["", "## Practical signal (non-starter)", ""]
    for r in practical[:20]:
        lines.append(f"- **{r['title']}** ({r['word_count']} words)")

    lines += ["", "## Mostly starters (deprioritize)", ""]
    lines.append(f"Count: {len(starters)} — short / draft titles / thin files")

    lines += ["", "## Skipped award-winner pattern", ""]
    skipped = [r for r in rows if r["skip_award"]]
    for r in skipped[:15]:
        lines.append(f"- ~~{r['title']}~~")
    if not skipped:
        lines.append("_None matched auto skip — add titles to gl/story_mine_manifest.json_")

    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    CATALOG.mkdir(parents=True, exist_ok=True)
    index = load_index()
    total_index = len(index)

    md_files = sorted(RAW.glob("*.md")) if RAW.is_dir() else []
    if not md_files:
        report = {
            "updated": datetime.now(timezone.utc).isoformat(),
            "phase": 2,
            "exported": 0,
            "index_total": total_index,
            "blocker": "Phase 1 export required — Linux cannot read .gdoc bodies",
            "title_only_hints": {
                "invent_in_title": 2,
                "how_to_titles": 11,
                "spray_series": ["The Spray", "2.0 The spray", "3.0 The spray--grammary"],
                "note": "Most $invent: lines are INSIDE docs — need export + body scan",
            },
            "entries": [],
        }
        OUT_JSON.write_text(json.dumps(report, indent=2), encoding="utf-8")
        write_markdown([], 0, total_index)
        print(f"DRY: 0/{total_index} exported — Phase 1 blocked")
        return

    rows = []
    id_by_slug = {e.get("export_md", "").split("/")[-1].removesuffix(".md"): e for e in index.values()}

    for path in md_files:
        meta = id_by_slug.get(path.stem)
        rows.append(scan_file(path, meta))

    rows.sort(key=lambda x: -x["score"])
    report = {
        "updated": datetime.now(timezone.utc).isoformat(),
        "phase": 2,
        "exported": len(rows),
        "index_total": total_index,
        "invention_total_lines": sum(r["invention_count"] for r in rows),
        "entries": rows,
    }
    OUT_JSON.write_text(json.dumps(report, indent=2), encoding="utf-8")
    write_markdown(rows, len(rows), total_index)
    print(f"OK: triaged {len(rows)} files · inventions {report['invention_total_lines']}")


if __name__ == "__main__":
    main()
