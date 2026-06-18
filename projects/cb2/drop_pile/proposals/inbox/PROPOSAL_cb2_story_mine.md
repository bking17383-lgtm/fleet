# PROPOSAL — Story Mine (tpgoround@gmail.com → games)

```yaml
from: CAPTN
fleet_id: cb2
callsign: CAPTN
machine: cb2
time: 2026-06-14T23:35:00-07:00
status: proposal
priority: high
account: tpgoround@gmail.com
```

---

## One line

Scrape/export ~4–6M words of Google Doc stories into a searchable catalog so Uncle/CAPTN can pick candidates for games and other projects.

## Problem

- **2,113+ `.gdoc` stubs** at Drive root + **`all stories archive/`** (~50) + scattered folders
- Linux/Cursor sees **171-byte stubs only** — cannot read story bodies
- Span: **~5 years active**, some pieces **~20 years** (2019–2025 visible on stubs; older may be deeper)
- Lester **EXPORT** one-at-a-time does not scale to millions of words

## Proposal — three layers

### 1. Story Scraper (export engine)

**Goal:** Every story → plain `.txt` or `.md` on Drive at predictable paths.

| Approach | Where runs | Notes |
|----------|------------|-------|
| **Google Apps Script** (extend existing) | Google cloud | Batch export, 15-min trigger, no puppy SSH |
| **Drive API + Python** | puppy64 | Full catalog + export, resumable |
| **WRANGLER manual** | CB1 Chrome | Fallback only — not for 2k docs |

**Output tree:**
```
stories_export/
  raw/           ← one file per story (plain text)
  catalog/       ← story_index.json (metadata)
  logs/          ← export_log.txt, errors
```

**Source scan includes:**
- `MyDrive/` root `*.gdoc` (exclude fleet/lester/drop_pile stubs)
- `all stories archive/`
- `Story/`
- Optional: Gmail **does not** scrape in v1 — Drive only unless Brian adds

### 2. Design Helper (browse + game-fit)

**Goal:** Turn corpus into **pick lists**, not one giant blob.

**`stories_export/catalog/story_index.json`** per entry:
```json
{
  "id": "slug-from-title",
  "title": "Zombie bar",
  "source_gdoc": "Zombie bar.gdoc",
  "export_md": "stories_export/raw/zombie-bar.md",
  "modified": "2022-11-18",
  "word_count": 8400,
  "era": "2019-2025|legacy",
  "tags": [],
  "game_signals": {
    "has_dialogue": true,
    "has_choices": false,
    "setting": "",
    "mechanic_hint": "clicker|vn|tabletop|audio|unknown"
  },
  "project_fit": []
}
```

**Design desk views (Uncle on CB1):**
- `fleet/STORY_PICKS.txt` — Brian's shortlist (manual)
- `concepts/stories/` — one-pagers like CONCEPT_anti_movie (game pitch from one story)
- Filter: word count, date, title keyword, `game_signals.mechanic_hint`

**Helper scripts (puppy64):**
- `story_inventory.py` — list + count only (Phase 0)
- `story_export_batch.py` — resumable export (Phase 1)
- `story_scan_hooks.py` — light NLP: dialogue density, chapter breaks, named entities (Phase 2)

### 3. Project bridge (stories → games)

| Output type | Example |
|-------------|---------|
| Clicker / Camel lane | Uncle extracts loop + resource metaphor |
| Mesh / voice | ROVER reads chapter summaries |
| Baseball-style data | Character roster JSON |
| Slicer / commercial | Public-domain-safe excerpt pack |

Each picked story gets: `concepts/stories/STORY_<slug>_game.md` (one page).

---

## Who does what

| Phase | Owner | Deliverable |
|-------|-------|-------------|
| 0 Inventory | **Puppy** | `story_index.json` (titles, dates, no body) |
| 1 Export | **Puppy** or Apps Script | `stories_export/raw/*.md` |
| 2 Design helper | **Uncle CB1** | picks + concept one-pagers |
| 3 Game proto | **Uncle + CAPTN** | delegate to existing game stack |

Brian: **DESK** + pick 5 titles to pilot.

---

## Rough size

| Item | Estimate |
|------|----------|
| Docs to scan | 2,000–2,500 |
| Words | 4–6M (Brian estimate) |
| Export storage | ~50–150 MB plain text on Drive |
| Phase 0 inventory | ~2–4 hours Puppy |
| Phase 1 full export | 1–3 days (API rate limits) |
| First game from mine | 1 story pilot |

---

## Open questions

1. Other accounts besides tpgoround@gmail.com? (Shared drives, second Gmail?)
2. Exclude list — fleet gdocs, lester keys, personal finance?
3. First game target — Camel? New IP? ROVER audio?
4. Apps Script vs Puppy API — Brian preference for OAuth?

---

## Next step if accepted

Puppy runs **Phase 0 inventory only** — post `stories_export/catalog/story_index.json` with counts; no mass export until Brian picks exclude rules.

Design doc: `concepts/STORY_MINE_DESIGN.md`  
Manifest stub: `gl/story_mine_manifest.json`

---

**Drop path:** `drop_pile/proposals/inbox/PROPOSAL_cb2_story_mine.md`
