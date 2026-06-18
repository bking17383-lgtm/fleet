# T2 KICKSTART — paste this in Terminal 2 (game tab)

**Daddy (T3) prepped this. You analyze; T3 delegates execute.**

---

## Paste into Cursor Terminal 2:

```
Read MyDrive/drop_pile/to_cursor/START_CAMEL_v0.8_ANALYSIS.md and T2_KICKSTART.md.
Analyze camel_clicker.py — 5 decisions only (golden, silk road mode, clock, relics, file structure).
Write MyDrive/drop_pile/from_cursor/CAMEL_v0.8_DECISION_MEMO.md.
No new features. Slicer on hold.
```

---

## Context card (so you skip re-reading everything)

**File:** `~/lester/camel_clicker.py` (~2000 lines, one file, zero deps)  
**Save:** `~/lester/standard_camel_save.json`  
**Play:** `cd ~/lester && ./run_camel.sh`

**Shipped v1.0.1:** turn-based days (sell/rest/race/wander advance calendar). All camels poop ×2/day. Health + herbs + bed menu. Intro on reset.

**Four camel types in code:** std, bac, rac, gld — bac/gld paths mostly stubbed; golden unused.

**Economy locked:** 5 slots/parcel · marry $50k · estate $500k · dynasty $1M · land $2M/$5M cash wall.

**Brian liked pacing** after health pass. Do NOT add complexity without a decision.

---

## Your 5 decisions (pick one option each)

| # | Question | Options |
|---|----------|---------|
| 1 | Golden camel | dynasty prize / cut / defer |
| 2 | Silk Road (bac) | separate mode / same terminal / defer v0.9 |
| 3 | Clock | keep turn-based / hybrid real-time |
| 4 | Relics vs artifacts | merge inventory / keep split |
| 5 | Structure | stay one file / split modes / PWA wrapper later |

---

## Output path

`MyDrive/drop_pile/from_cursor/CAMEL_v0.8_DECISION_MEMO.md`

When done → Brian says **sounds good** → Daddy queues puppy or T2 execute.
