# Standard Camel — 24 art slots → game map
# CAPTN game architect · Puppy fills `out/` · Brian is source of truth
Updated: 2026-06-15

Legal art/sound: **PASSED** (Brian).  
Gemini transcript: **IGNORED**. Puppy orders + Brian eye = truth.

---

## How to use

| Col | Meaning |
|-----|---------|
| **slot** | `graphics/out/NN_name.png` suggested filename |
| **game surface** | where player sees it (now or v0.9 PWA) |
| **mode** | home · stable · race · silk · menu |
| **priority** | P0 must ship feel · P1 v0.8 · P2 polish |

Brian: rename slots to match your actual 24 — this is architect draft.

---

## P0 — identity (6)

| slot | game surface | mode | notes |
|------|--------------|------|-------|
| 01_shop_exterior | Gorgeous Ali's Discount Camel Store — yard backdrop | home | Pollnivneach trader energy |
| 02_shop_sign | title / marquee text treatment | home | weird not stock |
| 03_ali_portrait | shopkeeper presence (dialogue frame) | home | not friendly corporate |
| 04_yard_day | main loop — dung click yard | home | ASCII_CAMEL replacement target |
| 05_yard_night | optional day/night mood | home | P2 if one yard enough |
| 06_ui_frame | menu border / chapter plate | all | shared chrome |

---

## P0 — camels (4)

| slot | game surface | mode | notes |
|------|--------------|------|-------|
| 07_camel_std | Standard 1-hump | stable | CAMEL_LABELS std |
| 08_camel_bac | Bactrian 2-hump | stable | unlocks Silk Road fiction |
| 09_camel_rac | Al Kharid Racer | stable / race | circuit register |
| 10_camel_gld | Golden — **??? reveal deferred** | stable / race | v0.8 memo: mystery asset |

---

## P1 — life sim (6)

| slot | game surface | mode | notes |
|------|--------------|------|-------|
| 11_marriage_hall | marry / divorce | menu | one wife rule |
| 12_wife_fatima | Fatima the Fierce (title wife) | home | WIVES title |
| 13_wife_kind | Layla kind path | home | WIVES kind |
| 14_home_portrait | portrait_menu snapshot frame | home / silk | frozen on Silk Road |
| 15_stable_interior | stable_menu backdrop | stable | 5 slots pivot herd |
| 16_land_parcel | grow land — grazing | stable | 5 camels per parcel |

---

## P1 — road & risk (4)

| slot | game surface | mode | notes |
|------|--------------|------|-------|
| 17_race_track | race circuit | race | pots / redeem dead racer |
| 18_holy_wander | wilderness relic find | wander | menu H |
| 19_estate_broker | oil / tourism / decoy fork | menu | $500k threshold |
| 20_silk_road_map | Silk Road expedition (v0.8) | silk | ~20 node-days |

---

## P2 — flavor (4)

| slot | game surface | mode | notes |
|------|--------------|------|-------|
| 21_victory_dynasty | win $1M fortune gate | victory | dynasty end |
| 22_failure_broke | 5 days at 0 health | fail | total failure |
| 23_artifact_odd | oddball artifact vignette | event | ODDBALL_ARTIFACTS tone |
| 24_book_study | library / book pop | menu B | unread books alert |

---

## Puppy clone lane

Read Brian refs → produce `graphics/out/01..24_*.png` (or report why not).  
Match **PALETTE.md** when Brian locks colors — not Gemini slop.

---

## Architect next (code — not now unless Brian says)

- v0.8 Silk Road mode loop (`CAMEL_v0.8_DECISION_MEMO.md`)
- v0.9: optional `display_art(slot_id)` hook in terminal or PWA
- Sound already legal-passed — separate from 24 stills

---

## Cross-ref

- Code: `lester/camel_clicker.py`
- Puppy order: `drop_pile/to_puppy/CAMEL_ARTIST_CLONE_NOW.md`
- CAPTN sprint: `fleet/CAPTAIN_CAMEL_SPRINT.txt`
