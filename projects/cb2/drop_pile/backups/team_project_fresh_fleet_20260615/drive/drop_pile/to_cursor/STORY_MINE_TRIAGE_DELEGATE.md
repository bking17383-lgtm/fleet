# STORY MINE — triage delegate (Brian 2026-06-15)

**Goal:** Mine ~4–6M words for  
1) **practical inventions** (tens–hundreds; `$invent:` lines inside docs)  
2) **novelty formats** (lists, gross-out sibling bits, etc.)  
**Skip:** award winners · thin starters · "list of good short stories"

**Blocker today:** **0 / 2139** bodies exported — Linux only has gdoc stubs.

---

## Who does what

| Who | Word | Job |
|-----|------|-----|
| **BEACON** or **Puppy** | `EXPORT` / `STORY MINE` | Phase 1 — gdoc → `stories_export/raw/*.md` |
| **Puppy** | `STORY MINE` | Batch export + run triage script |
| **Uncle** | `DESK` | Read `TRIAGE_PICKS.md` · pick pilots · no creative rewrite |
| **Brian** | — | Creative only · add award titles to skip list if needed |
| **CAPTN** | — | Built triage script · watches queue |

---

## Phase 1 — EXPORT (execute first)

**Option A — Puppy** (when live):  
Read `drop_pile/to_puppy/STORY_MINE_EXPORT_TRIAGE.md`

**Option B — BEACON Chrome** (tpgoround account):  
Batch export priority titles from `stories_export/catalog/PRIORITY_EXPORT.txt`  
Use `gl/GDOC_EXPORT_AUTOMATION.md` · plain `.md` only

**Priority buckets** (export these first ~50):

- All titles matching `$invent` / `invent` / `The Spray` series
- All `how to` / `ways to` / `list of`
- `the inventions of jilted lovers`
- `HOW TO SPEAK CHRISTIAN` (cross-brand)
- `Wife_Fixer_2000_Flashcards` (novelty list)
- `More Ways to make 15 million dollars`

Then batch by year or folder `all stories archive/`.

---

## Phase 2 — TRIAGE (automatic)

```bash
python3 ~/GoogleDrive/MyDrive/lester/story_mine/story_triage.py
```

**Outputs:**

- `stories_export/catalog/triage_report.json`
- `stories_export/catalog/TRIAGE_PICKS.md`

**Detects:**

| Lane | How |
|------|-----|
| Inventions | Lines like `$invent: wave water` inside body |
| Practical | parts lists, how-to build language |
| Novelty | numbered lists, gross/sibling/prank patterns |
| Starters | `start`/`draft` titles, <120 words |
| Award skip | nobel/prize/contest/best-of patterns |

Add manual skips: `gl/story_mine_manifest.json` → `exclude_gdoc_name_exact`

---

## Phase 3 — Brian picks (creative)

Uncle posts top 20 inventions + top 10 novelty lists to `concepts/stories/STORY_PICKS.txt`  
Brian marks **USE** / **NOVELTY** / **MEH**  
CAPTN links winners to proposals (Camel, Christianese, Sell Your Baby, etc.)

---

## Title-only hints (Phase 0 — already scanned)

| Signal | Count in index |
|--------|----------------|
| Total gdocs | **2139** |
| `$invent:` in title | **1** (+ many more **inside** bodies) |
| `how to` titles | **11** |
| Spray series | **3** |
| Starters (`start`/`draft`/`ideas`) | **~825** titles (deprioritize) |
| Award pattern in title | **1** (auto-skip + manual list) |

**Brian was right:** inventions are mostly **inside** stories, not in filenames. Export is mandatory.

---

## Brian one line

```
ALL: STORY MINE export batch 1 then triage
```

Or: **BEACON** on Chrome for tpgoround export while Puppy parked.

No slaves until export runs — this delegate order is ready on Drive.
