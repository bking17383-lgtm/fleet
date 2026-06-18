# CAMEL v0.8 — shipped

**Date:** 2026-06-15  
**From:** CAPTN (game architect)  
**Code:** `lester/camel_clicker.py` **v0.8.0**

---

## Shipped

| Item | Status |
|------|--------|
| Silk Road expedition mode | **LIVE** — menu **T** (needs Bactrian) |
| Home calendar freeze while away | **LIVE** — `advance_day` skips; portrait frozen |
| ~20 road-days / geography nodes | **LIVE** — Pollnivneach → Samarkand |
| Return cargo + homecoming events | **LIVE** |
| Golden camel ??? flavor | **LIVE** — reveal still deferred |
| `run_camel.sh` launcher | **LIVE** |
| `camel_art.py` optional hooks | **LIVE** — chafa/imgcat if art in `graphics/out/` |
| `--selftest` smoke test | **LIVE** |

---

## Play

```bash
cd /mnt/shared/GoogleDrive/MyDrive/lester && ./run_camel.sh
# or
python3 camel_clicker.py --selftest
```

---

## Not in v0.8 (by design)

- PWA / phone / Play URL (fleet HOLD)
- Full 24-art replace (Puppy → `graphics/out/` → v0.9)
- Golden camel dynasty reveal

---

## Uncle acceptance (Brian delegate = go)

- [x] Bactrian owner can enter Silk Road; home days freeze
- [x] Portrait shows frozen `home_snapshot` during expedition
- [x] ~20 node-days with geography text; return resolves cargo + family state
- [x] Homesteader path unchanged — no bac required to win
- [x] Turn-based pacing unchanged on home screen
