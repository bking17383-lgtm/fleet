# Gdoc export — automate the Lester problem

**Updated:** 2026-06-14 · Daddy T3  
**Problem:** Linux/Cursor sees `.gdoc` as 171-byte stubs. Only Chrome can read the body. Manual **EXPORT** word + Lester6 action keeps failing.

---

## Short answer

| Approach | Fully automatic? | Setup | Best for |
|----------|------------------|-------|----------|
| **A — Stop using gdocs** | Yes (no export step) | Zero | **Recommended** — edit `.md` only |
| **B — Google Apps Script** | Yes | One-time ~10 min | Keep gdocs as draft, auto-sync to `.md` |
| **C — Cursor /loop nudge** | No (reminder only) | T3 arms loop | Until B is set up |
| **D — Lester6 every session** | Semi | Already wired | Fallback if A+B not done |
| **E — Playwright on puppy** | Fragile | High | Not recommended |

**There is no way for Linux alone to read gdocs** without Google API credentials or Apps Script in your Google account.

---

## A — Best fix: plain `.md` is source of truth (no export)

Stop editing brain in Google Docs. Edit on Drive as plain text:

| Use this | Not this |
|----------|----------|
| `gl/instructions for AI.md` | `instructions for AI (general).gdoc` |
| `lester/free_lester_instructions.md` | Free Lester gdoc |
| `lester/gemini_live_sorting_instructions.md` | Sorting gdoc v3 |

**Rule:** If Linux must read it → it lives in `.md`. Gdocs become optional drafts only.

Zero Lester export loop. Zero EXPORT word for those files.

---

## B — True automation: Apps Script (one-time setup)

Files on Drive:

| File | Purpose |
|------|---------|
| `gl/gdoc_export_manifest.json` | What to export → where |
| `gl/apps_script_auto_export.gs` | Copy-paste into Google Apps Script |
| `gl/export_log.txt` | Created after first run |

### Setup (Brian, once)

1. Open [script.google.com](https://script.google.com) → **New project**
2. Delete default code → paste all of `gl/apps_script_auto_export.gs`
3. **Run** `setup` once → authorize Google Drive access
4. **Triggers** (clock icon) → **Add trigger**
   - Function: `exportStaleGdocs`
   - Event: Time-driven → **Every 15 minutes** (or 5 if impatient)
5. Check `gl/export_log.txt` on Drive after first run

### What it does

- Reads manifest JSON
- Finds each source gdoc by name
- If gdoc is **newer** than target `.md` → exports plain text to target path
- Skips if `.md` already up to date
- For `instructions for AI` → **`.md` is master** (won't overwrite newer md with stale gdoc)

### Add new exports

Edit `gl/gdoc_export_manifest.json` — add an entry. Script picks it up next run.

No Lester. No EXPORT word. No Terminal 3 loop required.

---

## C — Partial: T3 loop (reminder until B works)

Cursor `/loop 15m` on Terminal 3 can:

1. Read manifest + check if target `.md` is missing or older than stub mtime
2. Write `drop_pile/to_lester/EXPORT_STALE_NUDGE.md`
3. Queue `execute_brief` for BEACON

**Still needs Lester6 Chrome** to actually export — this only automates the *nag*, not the export.

Use only as bridge until Apps Script is live.

---

## D — Current fleet fallback (manual)

| Step | Who |
|------|-----|
| Brian says **EXPORT** | Chrome Lester6 |
| Read `gl/gdoc_export_manifest.json` or `EXPORT_NOW.txt` | BEACON / WRANGLER |
| File → Download → Markdown OR paste → `.md` | Chrome |
| Say *"exported"* | Lester6 |

Wired in: `gl/instructions for AI.md` session checklist, slave configs, `ONE_WORD.txt`.

---

## E — Not recommended

- **Playwright headless Chrome** on puppy — login/session breaks, Crostini pain
- **Gemini API** reading gdocs — still needs doc IDs + API key; doesn't fix Drive mount
- **Website bots** — fleet rule: BEACON exports only, no scraper bots

---

## Recommendation for Brian

1. **Today:** Treat `gl/instructions for AI.md` and other `.md` files as master — open those at session start
2. **This week:** Run Apps Script setup once (section B) — then gdocs auto-sync every 15 min
3. **Retire:** Stop saying EXPORT for manifest files once `gl/export_log.txt` shows OK runs

---

## Words

| Word | Meaning |
|------|---------|
| **EXPORT** | Manual Lester6 export (until Apps Script live) |
| **GL** | Hub — `gl/INDEX.md` |
| **READY** | Check `LESTER6_SLAVE_SCORECARD.txt` + `gl/export_log.txt` |
