# Human testers — how to invite

**Updated:** 2026-06-14 — **Brian human testing ON HOLD** (`drop_pile/HOLD_HUMAN_TEST.md`)  
**Active track:** stranger phones on LTE — `lester/STRANGER_PHONE_READINESS.md`

**Goal:** strangers/friends on cellular or home Wi-Fi test without Brian relaying.

---

## Tester-ready checklist (per project)

### Baseball cards (stranger LTE — prep)

| Need | Status | Fix |
|------|--------|-----|
| Stable HTTPS URL | ❌ pending | puppy64 **named** Cloudflare → :8002 |
| Always-on :8002 | ❌ | commercial install + `STRANGER_PHONE_PREP.md` |
| Commercial empty data | ✅ packaged | `releases/baseball_cards_v1.0.0` |
| Stranger script | pending | Lester `stranger_invite.txt` |
| Public link file | pending | `STRANGER_TESTER_LINK.txt` |

**Brian human test:** HOLD — do not use Sarah checklist on Brian until lift.

**NEVER:** mine Gmail/Contacts/Drive for tester names (`fleet/TESTERS_NO_GOOGLE_MINING.txt`). Brian picks 12 manually for Play.

**Stranger script (when URL live):**

1. Open URL from `STRANGER_TESTER_LINK.txt` (LTE OK)
2. Tabs: List · Stats · Sync
3. Stats: loads without error (demo or empty + import hint)
4. Reply: works / broken → `drop_pile/from_tester/feedback.txt` (optional)

### Baseball cards (home Wi-Fi — legacy)

| Need | Status | Fix |
|------|--------|-----|
| Stable HTTPS URL | ⚠️ tunnel rotates | puppy LAN **or** named Cloudflare token on puppy |
| Always-on :8002 | ❌ puppy not serving | `puppy_qa.md` on puppy64 |
| One-page test script | missing | see below |
| QR / link for phone | `BRIAN_PHONE.txt` on Drive | update when puppy posts |

**Tester script (send link + this list):**

1. Open URL from `BRIAN_PHONE.txt` (same Wi-Fi for LAN; LTE needs fixed tunnel)
2. Tabs: Add → List → Stats → CollX
3. Stats: expect **~497 cards**, **~$2,092**
4. List: sort expensive/cheap, search one player name
5. Reply: "works" / "broken: ___" → text Brian or `drop_pile/from_tester/feedback.txt`

### Camel (later)

- Local play only for now: `cd ~/lester && ./run_camel.sh`
- PWA/web wrapper = separate milestone after T2 decision memo

### Slicer

**ON HOLD** — do not recruit testers until Brian unblocks.

---

## Where to post invites

- Fixed URL in `BRIAN_PHONE.txt` (Drive — all agents read)
- Optional: `TESTER_LINK.txt` on Drive root with expiry date
- Lester may **read** status to Brian; Lester does **not** move files

---

## Daddy (T3) adds testers by

1. Ensuring puppy serves stable URL
2. Writing `TESTER_SCRIPT_<project>.md` to `drop_pile/`
3. Queue `refresh_status` after URL is live
