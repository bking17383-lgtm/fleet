# Hardware reality ladder — ideas → touchable / measurable / probable

**From:** Uncle (new CB1)  
**Time:** 2026-06-15  
**Status:** thought experiment → test pack v1  

Software ships in git. Hardware ships in **hands**. This ladder is how we climb without losing the tactile thread.

---

## Three rungs (every physical project)

| Rung | Question | Drive artifact | Who captures |
|------|----------|----------------|--------------|
| **Touchable** | Can we point at it, hold it, or photograph it? | `photos/`, `bom.csv` (`in_hand` column), `build_log.md` | Brian + WRANGLER (SHOW) |
| **Measurable** | Can we put a number on it? | `measurements.md`, `test_results.md` | Brian measures · Puppy calc · Uncle locks |
| **Probable** | What will likely happen if we run the test? | `risk_memo.md`, `decisions.md` | Uncle + Brian · Lester6 voice brainstorm |

**Rule:** no rung is done in chat only. File on Drive or it did not happen.

---

## Promotion gate (idea → reality)

```
IDEA (napkin)
  ↓  brief.md — one paragraph goal + constraints
TOUCHABLE v0
  ↓  photo OR parts list with in_hand=yes OR mockup sketch scan
MEASURABLE v0
  ↓  ≥3 numbers (dims, weight, temp, pressure, time, cost)
PROBABLE v0
  ↓  risk_memo — top 3 failure modes + mitigations + human-only steps
BUILD v1
  ↓  build_log dated steps
TEST v1
  ↓  test_results + post_mortem photo
DECISION
  ↓  Uncle decisions.md — ship v2, park, or kill
```

---

## Example (illustrative only — battery container)

Not a build order. Shows how the ladder works.

| Stage | Touchable | Measurable | Probable |
|-------|-----------|------------|----------|
| v0 | Photo of tote + lid | 12×8×6 in interior | Vent undersized → pressure spike |
| v1 | Sand fill base in place | 2 in vent hole, 4 lb sand | Single-cell test OK; batch needs baffle |
| v2 | — | — | Uncle: ship v2 before >3 cells |

---

## Brian words (hardware)

| Say | Action |
|-----|--------|
| **SHOW** | Lester6 Live — describe what you're holding |
| **SHOP** | Append one line to `build_log.md` |
| **MEASURE** | One number → `measurements.md` |
| **RISK** | Uncle drafts `risk_memo.md` from voice notes |
| **v1 SHIP** | Lock decisions — build allowed |

---

## Agent split (no agent holds the wrench)

| Agent | Hardware lane |
|-------|----------------|
| **WRANGLER** | Eyes, voice, gdoc export, SHOW transcripts |
| **Uncle** | decisions.md, risk_memo.md, promotion gates |
| **Daddy** | brief normalization, queue calc jobs to Puppy |
| **Puppy** | spreadsheets, vent math, cut lists, sourcing |

---

## Test pack v1 (this week)

1. Copy `projects/HARDWARE_PROJECT_TEMPLATE/` → `projects/<your_project>/`
2. Fill `brief.md` with one real or toy project
3. Complete **Touchable v0** only — one photo or one `in_hand=yes` BOM row
4. WRANGLER logs completion in `wrangler_hardware_loop.md`

Success = one project folder with `brief.md` + one touchable proof.

---

## Uncle notes

- Fleet scripts still **off** — manual Drive only
- New Uncle — do not merge with old CB1 `~/.stan` state
- Probable ≠ guaranteed — we document likelihood and **who must be in the room**
