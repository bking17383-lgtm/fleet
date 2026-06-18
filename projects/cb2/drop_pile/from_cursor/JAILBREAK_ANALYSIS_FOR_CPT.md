# Jailbreak + Gemini Live — analysis for CPT (Daddy)
**From:** Gem · 2026-06-16  
**Word for Brian:** **JAILBREAK**

---

## What jailbreak was supposed to be

NOT prompt hacking. Three pieces:

1. **Free Lester** — Spark/Gemini system instructions exported to plain `.md`
2. **Gemini Live** — camera coach (one item, good light, slow frames)
3. **Transcript → Drive** — Live text lands in `drop_pile/from_lester/` → Flask grades card

Architecture already on disk: `live_capture.html` + `scan_pipeline.py` (Hybrid C).

---

## Where Lester failed (blocker)

| Item | Status |
|------|--------|
| `free_lester_instructions.md` | **STUB** — still `AWAITING_EXPORT` |
| Free Lester gdoc | Linux blind · Lester never exported |
| `scan_cheats.json` | **MISSING** — pipeline has nothing to load |
| Live on piles | **FAILED** field test — one still frame only |

**No export = jailbreak never started.** Puppy built infra anyway.

---

## What we did without Lester (workarounds)

| Workaround | What it is | Limit |
|------------|------------|-------|
| **transcript_sink :8765** | Paste box → Drive `.txt` | Manual · not Live API |
| **mesh RADIO :8765** | Phone → CAPTN voice/SNAP | Talk to Daddy · not card coach |
| **GL parked** | ROVER uses RADIO not Gemini Live | GL button = trap |
| **One test transcript** | `live_transcript_live_20260614…` | Proves sink once |

**Conflict:** RADIO and jailbreak sink both want **port 8765** on puppy.

---

## How to make it work

### Gem/Cursor can fix (no Lester required)

1. **Export Free Lester** — Gem controls Gemini account → write real `free_lester_instructions.md` from gdoc (Brian said Gem owns Gemini lane)
2. **Build `scan_cheats.json`** from existing `gemini_live_sorting_instructions.md` (v3 already on Drive)
3. **Split ports** — RADIO `:8765` · jailbreak paste `:8766` OR merge one Flask app
4. **Wire puppy** — `:8002/live/capture` + `gemini_live_url.txt` + PUPPY_FIX deploy
5. **Law:** one item per capture · no pile video

### Still needs Brian (minimal)

- Paste Free Lester gdoc once in Gemini **or** say **JAILBREAK** and Gem writes it
- One card test: Live coach → postGate → Flask grade

### Still parked

- GL on Moto (use RADIO for talk · Live for catalog session on desk only)
- Estate drawer piles until card spike passes

---

## CPT action

Read this · assign puppy **8766 sink** or unified host · do not wait on Lester export — **Gem writes Free Lester next if Brian says JAILBREAK**.

Confirm line: *Gem can fix the export + wiring. Lester was the blocker, not the architecture.*
