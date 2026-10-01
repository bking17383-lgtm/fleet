# AGENTS.md

This repo (`fleet`) is primarily an agent/machine-coordination system: Bash scripts under
`scripts/` and Markdown docs under `bus/` are operational plumbing (heartbeat, sync, orders),
not a buildable app. The actual buildable products live under `projects/`.

The flagship runnable product is the **Baseball Card Valuation** Flask app at
`projects/cb2/lester/baseball_cards/`. See its own guide at
`projects/cb2/lester/baseball_cards/AGENTS.md` for product details and the CollX import flow.

## Cursor Cloud specific instructions

- Scope: in a Cursor Cloud VM only the code is available — there is no LAN, phone, Google
  Drive mount, or Chromebook/Cloudflare tunnel. So `puppy LAN`, Drive (`/mnt/shared/...`),
  Gmail IMAP, and Tailscale features are unreachable and degrade gracefully (the app wraps
  these in try/except and keeps running). Do not treat them as blockers.
- There are **no dependency manifests or lockfiles** anywhere in the repo. The only Python
  third-party deps the flagship app needs are `flask` (required) and `qrcode` + `pillow`
  (only for the `/qr` endpoints, imported lazily). They are installed by the startup update
  script via `pip install`. The VM has Python 3.12 (the baseball_cards guide mentions 3.13,
  but 3.12 runs the app fine).
- There is **no lint, test, or build tooling** (no test files, no CI, no Makefile/linters).
  "Verification" is the `/api/health` check and manual UI use.
- Run the flagship app in dev mode from its own directory:
  - `cd projects/cb2/lester/baseball_cards && python3 app_baseball.py` (foreground, Flask on
    port 8002), or `./start_baseball.sh` (backgrounds it, writes `baseball_server.pid`/`.log`).
  - Health check: `curl -s http://127.0.0.1:8002/api/health`
- Data is flat JSON under `baseball_cards/data/` (auto-created). `data/` and `uploads/` are
  gitignored personal card data — never commit them. The repo ships a `collx_export.csv`
  sample and a pre-populated CollX catalog, so the app boots with ~497 cards already loaded.
- Add a card (no UI "Add" form exists; the visible UI is List/Sync/Stats — add via API):
  `curl -s -X POST http://127.0.0.1:8002/api/cards -H 'Content-Type: application/json'
  -d '{"player":"Name","year":2024,"set":"Topps","card_number":"1"}'`
- Other optional products (separate, not needed for the flagship): hitme.dev hub
  (`projects/cb2/lester/puppy_hitme/hitme_who_server.py`, Flask :8770, needs `flask`) and
  Lester voice (`projects/cb2/lester/app.py`, Flask :5000, needs `flask`, `groq`,
  `langsmith` + `GROQ_API_KEY`). Static mini-sites under `projects/*` need only
  `python3 -m http.server`.
