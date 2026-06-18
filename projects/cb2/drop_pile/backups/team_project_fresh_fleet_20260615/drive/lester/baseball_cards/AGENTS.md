# Baseball Card Valuation — Agent Guide

Read `~/.stan/handoff/session_note.md` (blueprint **index** cards) and this file before doing work.
Do **not** need long context — reuse blueprint ids each session.

## Blueprints (short context)

- Index: `MyDrive/blueprints/index.json` + local `~/.stan/blueprints/`
- Puppy writes cards; penguin syncs: `python3 ~/.stan/blueprints.py sync`
- Session shows one-line cards; full recipe: `python3 ~/.stan/blueprints.py show collx-import`
- Default baseball ids: `collx-import`, `phone-puppy-serve`, `brian-os-handoff`, `baseball-restart`, `collx-stats-total`

## What this is

Flask app on **port 8002** — phone-first UI for Brian's baseball card collection.
**All prices come from CollX CSV import only** (no heuristic/fake estimates).

## Workspace

```
/home/bking17383/Applications/cursor/baseball_cards
```

Always open Cursor here. Ignore `mom_layer_test`, Mom game, Pillow.

## Who is who (Brian's names)

| Name | What |
|------|------|
| **Big Daddy** | **This Cursor** on penguin (Chromebook Linux) — captain, code, package, ship |
| **puppy** | Cursor agent on **puppy64** — phone server, LAN deploy, few side projects |
| **Lester 6** | Voice/Gemini on **Chrome** — design, landing, Play Store, Brian-facing talk |

Brian talks to Lester. **Big Daddy** executes on penguin. **puppy** runs on puppy64 when needed.

## Machines

| Host | Role |
|------|------|
| **penguin** (Chromebook Linux) | Big Daddy: code, CollX import, Drive scan, commercial package |
| **puppy64** | puppy agent: phone server on home Wi-Fi (`192.168.x.x:8002`) |
| **penguin tunnel** | Cloudflare fallback only if puppy not serving |

puppy runs `START_BASEBALL_ON_PUPPY.sh` from Drive `lester/`. Post status to `puppy_outbox.txt`.

## Brian OS (plain English for Brian)

- Status: `Google Drive/MyDrive/BRIAN_STATUS.txt`
- Queue: `Google Drive/MyDrive/brian_queue.json`
- CollX inbox: `Google Drive/MyDrive/collx_inbox/`
- Phone link: `BRIAN_PHONE.txt` on Drive (puppy LAN URL when running)

Brian talks to **Lester** (voice). Lester queues jobs. **Cursor executes** — no manual relay.

## CollX import flow

1. CollX app → CSV export (email or save on phone/PC)
2. Get file into the app by one of these **only** (Google/Gemini **cannot** move downloaded files):
   - **Drop** CSV in Drive `collx_inbox/` (any filename)
   - **Phone upload** on Sync tab (`/api/collx/import`)
   - **Server Gmail IMAP** pull (`~/.stan/gmail.env` + auto-sync) — puppy/penguin fetches attachment, does not “move” via Google UI
3. Auto-sync every 30s + **Sync now** on Sync tab
4. Re-import picks **largest row count** CSV; audit: `GET /api/collx/audit`

**Lester role:** audit email row counts, tell Brian what to upload — not relocate files via Google products.

CSV columns used: `market_value`, `asking_price`, `purchase_price`, `sold_for_price`, images, flags (RC/SP/AU), brand, team, etc.

## Key files

| File | Purpose |
|------|---------|
| `app_baseball.py` | Flask API |
| `index_baseball.html` | Phone UI (Add / List / Stats / CollX tabs) |
| `collx_data.py` | CSV parse, catalog, import, matching |
| `data/collection.json` | Brian's cards (gitignored — personal) |
| `data/collx/catalog.json` | CollX catalog snapshot (gitignored) |

## Commands

```bash
cd /home/bking17383/Applications/cursor/baseball_cards
python3 app_baseball.py          # dev server
./start_baseball.sh              # start + print URLs
python3 scan_collx_drive.py      # CLI import scan
curl -s http://127.0.0.1:8002/api/health | python3 -m json.tool
```

## Acceptance (usable level)

- [ ] CollX import updates collection; stats total = sum of `market_value` (CollX total)
- [ ] List: search, set filter, price filter, sort
- [ ] Open app → last edited card on Add tab
- [ ] Phone opens via **puppy LAN** when puppy is serving
- [ ] CollX tab: easy CSV pick (no agent required)

## Cursor Cloud specific instructions

- Python 3.13, no venv required (stdlib + flask)
- Git may be unavailable on penguin Crostini — code lives in workspace either way
- Do not commit `data/` or `uploads/` (personal card data)
- Drive mount on penguin: `/mnt/shared/GoogleDrive/MyDrive`
- If cloud agent: cannot reach puppy LAN or Chromebook tunnel — code only

## Workflow

- Lester/Gemini **designs** → Brian says **sounds good** → Cursor **builds**
- After shipping: update `~/.stan/handoff/session_note.md` via `stan_env.touch_cursor_session`
