# START — Lester jailbreak (Gemini Live camera + transcript scrape)

**From:** Daddy (T3)  
**Priority:** #1 (Brian current)  
**Slicer / Camel:** on hold

---

## What “jailbreak” means here (from past notes)

NOT prompt hacking. Means:

1. **Free Lester / Lester Jr.** — Spark-written **system instructions** so Gemini Live acts as **camera coach / catalog slave**, not general chat
2. **Camera** — Live sees phone/webcam frames for card or estate item
3. **Transcript scrape** — capture Live **text output** back into Drive/stack (structured rows, not chat lost in air)

---

## Past ideas already on disk

| Artifact | Status | Notes |
|----------|--------|-------|
| `Free Lester (Lester Jr.) System Instructions.gdoc` | **BLOCKED** | Linux cannot read `.gdoc` |
| `lester/free_lester_instructions.md` | **STUB only** | `AWAITING_EXPORT` |
| `Gemini Live Sorting Instructions.gdoc` (+ v3) | **BLOCKED** | same gdoc problem |
| `baseball_cards/scan_pipeline.py` | **Built** | Hybrid C: Live = gate, Flask = grade |
| `baseball_cards/live_capture.html` | **Built** | `BaseballScan.postGate/postGrade` bridge |
| `IDEA_estate_drawer_catalog.md` | **Analysis** | Live **failed** on piles — use **one item / still frame**, not heap video |
| `scan_cheats.json` | **Missing** | Referenced paths empty |

**Brian field truth:** slow frames, needs lighting, cannot count piles. $500 WTP if **mechanical pacing** works (one item at a time).

---

## Architecture (recommended)

```text
Gemini Live (Chrome or phone)
  ← system_instruction from free_lester_instructions.md
  ← camera frames
  → transcript / structured lines

Transcript sink (NEW — puppy or Chrome helper page)
  → drop_pile/from_lester/live_transcript_<timestamp>.txt
  → optional parser → catalog_row.json

Flask (baseball scan_pipeline OR estate schema later)
  → grade / route / CollX math (already exists for cards)
```

**Do NOT** rely on Live alone to count drawer piles. **One item per capture** until singulation exists.

---

## Phase 0 — UNBLOCK (Brian + Lester/Chrome, today)

Lester must export gdoc to plain text:

1. Open `Free Lester (Lester Jr.) System Instructions.gdoc`
2. Also export `Gemini Live Sorting Instructions` (v3 if latest)
3. Save as:
   - `MyDrive/lester/free_lester_instructions.md` (replace stub)
   - `MyDrive/lester/gemini_live_sorting_instructions.md` (new)
4. Say **"Free Lester exported"**

**No export = jailbreak cannot start.** T3/puppy are blind.

---

## Phase 1 — Transcript scrape spike (puppy64)

Build minimal **sink** — does not need perfect Live API:

| Option | Effort | Notes |
|--------|--------|-------|
| A. Paste box page on puppy | Low | Brian copies Live caption → POST → Drive file |
| B. Chrome extension / bookmarklet | Med | Scrape visible Live transcript DOM |
| C. Periodic screen OCR | High | last resort |

**Deliverable:** any Live session → one `.txt` in `drop_pile/from_lester/` within 60s.

---

## Phase 2 — Wire instructions (puppy + T3 after Phase 0)

1. Parse `free_lester_instructions.md` → `scan_cheats.json` global_prompt
2. Host `live_capture.html` or puppy Live URL in `gemini_live_url.txt`
3. Test **one baseball card** end-to-end: Live coach → postGate → Flask grade

---

## Phase 3 — Estate catalog (only after card spike works)

Shoebox test: 20 oddball items, light box, one still each — see `IDEA_estate_drawer_catalog.md`.

---

## Assignments

| Who | Job |
|-----|-----|
| **Lester/Chrome** | Phase 0 export (blocker) |
| **puppy** | Phase 1 transcript sink + Phase 2 host |
| **T3** | Review exports, queue phases, no penguin execute |
| **T2** | on hold |

---

## Avoid

- Medical photos in camera roll (Brian note 2026-06-12)
- `.gdoc`-only handoffs
- 24/7 Live stream over piles
- Batch transcribe 180 cloud videos (session note)

---

## Done when (jailbreak v0)

- [ ] `free_lester_instructions.md` has real body (not stub)
- [ ] One Live session produces `drop_pile/from_lester/live_transcript_*.txt`
- [ ] One card runs Hybrid C: Live gate → Flask grade with CollX price
