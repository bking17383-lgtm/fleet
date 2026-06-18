# CAMEL v0.8 — decision memo

**From:** Uncle (Terminal 2)  
**To:** Brian + Daddy  
**Date:** 2026-06-14  
**Code:** `~/lester/camel_clicker.py` v1.0.1 · ~2000 lines · zero deps

---

## Recommendation

**Stay one terminal file for v0.8.** Add Silk Road as a **separate in-game mode** (menu branch + `on_silk_road` state already stubbed), not a second app or PWA yet. Split modules only after Silk Road ships and Brian still wants more paths — a wrapper can wait until a mode exists worth wrapping.

---

## Five decisions

| # | Question | Pick | Why |
|---|----------|------|-----|
| 1 | **Golden camel** | **Defer reveal** — keep buyable/raceable, no dynasty hook yet | `gld` already races faster than `rac` but has no unique fantasy. Mystery is the design asset; tying it to dynasty before the hook is defined adds complexity without pacing payoff. Show "???" flavor text until Brian picks the reveal beat. |
| 2 | **Silk Road (bac 2h)** | **Separate mini-mode** — same terminal, different screen loop | v0.7 design: ~20 days, geography nodes, home frozen via `home_snapshot`. Code already has `on_silk_road`, `silk_road_days_left`, portrait menu. Same screen for home+racing would bury the expedition; a dedicated mode keeps homesteader pacing intact. |
| 3 | **Clock** | **Keep turn-based days** | Brian liked v1.0.1 pacing. Sell/rest/race/wander advance calendar; click does not. Hybrid real-time would fight health/herb/bed tuning. Silk Road days consume the same `advance_day` contract. |
| 4 | **Relics vs artifacts** | **Keep split** — holy relics (H menu, buffs) vs oddball artifacts (race pots, sell/keep) | Different verbs and fiction: relics = spiritual/wander; artifacts = desert junk economy. Merge later only if inventory UI feels cluttered in playtest. |
| 5 | **Structure** | **Stay one file through v0.8** | Silk Road is ~300–500 lines (node table + mode loop + return). Extract `silk_road.py` in v0.9 if file crosses ~2500 lines or Brian wants PWA. |

---

## If Brian says sounds good — execute plan

**Max 3 files:**

1. `~/lester/camel_clicker.py` — Silk Road mode loop + node table + return cargo
2. `~/lester/standard_camel_save.json` — schema already has silk fields; no breaking change expected
3. `MyDrive/drop_pile/done/CAMEL_v0.8_shipped.md` — ship note for Daddy/Lester

**Acceptance checks:**

- [ ] Bactrian owner can enter Silk Road; home days freeze (`advance_day` skips while `on_silk_road`)
- [ ] Portrait shows frozen `home_snapshot` during expedition
- [ ] ~20 node-days with geography text; return resolves cargo + family state
- [ ] Homesteader path unchanged — no bac required to win
- [ ] Turn-based pacing unchanged on home screen

**Out of scope for v0.8:** golden reveal, PWA, merged inventory, cash land repricing changes.

---

## Uncle note for Daddy

Camel analysis lane only. No queue edits, no puppy nudges. Ready for execute when Brian approves.
