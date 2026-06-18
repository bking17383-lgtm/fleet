# Camel — art hooks (future, architect notes)
Updated: 2026-06-15

Today the game is **terminal + ASCII_CAMEL** with optional **`camel_art.py`** loader.  
v0.8 Silk Road shipped. Art in `graphics/out/` shows via chafa/imgcat when present.

---

## Live hooks (v0.8+)

| Function | Art slot |
|----------|----------|
| `show_slot("04_yard_day", ASCII_CAMEL)` | main yard |
| `camel_art.art_path(slot)` | any slot from `CAMEL_ASSET_MAP.md` |

Terminal fallback: **art file → ASCII → plain text** (never blank).

---

## Current text surfaces (art replaces when file exists)

| Function | Line area | Art slot |
|----------|-----------|----------|
| `ASCII_CAMEL` | ~290 | 04_yard_day |
| `portrait_menu` | ~1578 | 14_home_portrait frame |
| `stable_menu` | ~1595 | 16_stable_interior |
| `main yard loop` | ~1885 | 01_shop + 04_yard |
| `race_menu` | grep race | 17_race_track |
| `holy_wander_menu` | ~1505 | 18_holy_wander |
| `estate / marriage menus` | ~1777+ | 11, 19 |

---

## Minimal hook sketch (v0.9 — do NOT apply until Brian says)

```python
# lester/camel_art.py (future)
ART_DIR = os.path.join(_SCRIPT_DIR, "graphics", "out")

def art_path(slot: str) -> str | None:
    p = os.path.join(ART_DIR, f"{slot}.png")
    return p if os.path.isfile(p) else None

def show_slot(slot: str, fallback_ascii: str) -> None:
    # PWA: <img> · terminal: chafa/imgcat if present else fallback
    ...
```

Terminal fallback chain: **art file → ASCII → plain text** (never blank).

---

## Sound

Brian: legal passed. Keep `intro_music.*` beside script. No architect change.

---

## Puppy / Brian

24 files in `graphics/out/` named per `CAMEL_ASSET_MAP.md` — code hooks when display sprint starts.
