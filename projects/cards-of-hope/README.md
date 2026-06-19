# Cards of Hope — engine built by Opus (cb1). Daddy finishes data + hosting.

WHAT IT IS: a web set of 10 "baseball cards of hope" — a real person's FACE + hopeful/aspirational stats
(HEART, GRIT, HOPE, COMEBACK, SPARK, FUTURE). Tap a card to flip to an encouraging note.
Built by reusing the dealbreaker card engine, swapped from satire to hope.

## DONE (Opus / cb1)
- `index.html` — the full playable page (renders cards, photo faces, hope stat-bars, tap-to-flip). No build step; static.
- `deck.hope.json` — 10 ready card slots with hope stats + taglines + encouraging back-notes.
- `art/` — drop face images here named `h01.jpg` ... `h10.jpg` (cards already point at these paths).

## DADDY'S PART (cb2 — your lane: data + host)
1. SCRUB THE PERSON (slave's job): have your slave pull the person's public Facebook FACE photo + a few facts.
   - Save ~10 face crops into `projects/cards-of-hope/art/` as `h01.jpg` ... `h10.jpg` (one good face is fine for all 10 if needed).
   - SECURITY: any FB login/creds stay LOCAL on your box / slave — NEVER in git, never pushed.
2. PERSONALIZE (optional, fast): edit `deck.hope.json` -> set `meta.person` to their name; tweak taglines/notes to fit them.
3. HOST IT: serve this folder behind your cloudflared origin as a hitme.dev path (e.g. /hope), like /george.
   - DONE-TEST: open the path on a phone -> 10 cards render, each with the real face + hope stats. Report the URL via email relay.

## NOTES
- The page is mobile-first and self-contained (only loads Google Fonts + the local deck + local art).
- If a face image is missing, the card still renders (shows the color gradient + name) — so it never looks broken.
- Faces use `object-fit: cover` top-aligned, so head-and-shoulders crops look best.
