DROP PILE — delivery that actually lands (no Gemini blank check)
================================================================

PROBLEM
  Gemini / Spark writes to Google Docs (.gdoc). Linux agents CANNOT read .gdoc
  stubs from Drive mount — 30TB useless if the file never arrives as plain text.

RULE — every handoff is PLAIN TEXT on Drive
  ✅ .txt  .md  .json  .csv  .mp4  .tar.gz
  ❌ .gdoc alone (export/download required)

FOLDERS (drop here; agents poll these paths)
  COMMON_INSTRUCTIONS.md   → ALL agents read first (Daddy = Terminal 3)
  drop_pile/to_cursor/     → Terminal 2 / execute tabs read
  drop_pile/to_puppy/      → puppy64 executes (Daddy writes orders here)
  drop_pile/to_lester/     → Lester 6 reads (Chrome voice)
  drop_pile/from_lester/   → Lester exports land here (e.g. free_lester_instructions.md)
  drop_pile/proposals/     → PROJECT proposals from any box/slave/phone (see README)
  drop_pile/done/          → move after processed (optional)

ALSO WORKS (existing)
  brian_queue.json         → machine queue
  BRIAN_STATUS.txt         → plain English for Brian
  puppy_outbox.txt         → puppy posts phone URL
  Hello from Puppy.txt     → puppy → penguin ping
  collx_inbox/             → CSV drops

GEMINI INSTRUCTION FOR SPARK/LESTER 6
  When Brian says "drop it in the pile":
  1. Write .md or .txt to drop_pile/from_lester/ (or lester/*.md)
  2. Never .gdoc-only for anything Cursor or puppy must execute
  3. One file = one job; filename says what it is

SLICER ZERO-COST HOST
  See: lester/SLICER_ZERO_COST.md
  Puppy runs app + named Cloudflare tunnel ($0/mo)
