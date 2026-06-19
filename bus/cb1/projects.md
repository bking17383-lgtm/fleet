# PROJECT BACKLOG + WORK DISTRIBUTION — Opus/cb1, 2026-06-19
# Grounded in CONTEXT_SPINE (Brian's 5-hour interview). Ranked by Brian's stated value.
# Opus ASSIGNS + VERIFIES; Daddy (workhorse) EXECUTES; dispatch-on-idle keeps both working.

## RANKED PROJECTS (what Brian wants done — top = most value)
1. FIRST DOLLAR (north-star enabler): finish the PAYWALL (~95% done) -> receive money -> ONE revenue lane.
   Nothing earns yet. This is THE priority per Brian's vision. (Currently NOT on Daddy's queue — fix.)
2. george: voice at /george (200) + george.hitme.dev (needs CF cert) + 6-turn memory + AWS Polly voice.
3. Cards of Hope: FB face/data -> ~10 hope cards -> host /hope. (Daddy's current task 0.)
4. Mobile Jane: phone voice page /jane (reuse george stack). (Daddy task 0b.)
5. Revenue/site lanes: dealbreaker ("the big one"), websites (hitme-landing/landing/projects-www/team-desk/www).
6. Lester lanes (reference/secondary): baseball_cards, sarah, heritage, camel, story_mine, hitme_simple.
7. Cleanup: /keaton 503, bun.hitme.dev 502 — fix or retire.

## WORK DISTRIBUTION MODEL (keep BOTH Opus + Daddy working)
- OPUS (cb1, auditor/build): curate truth, decide priorities, VERIFY output (no false greens), do backend +
  Jane (the 90%). Splits its own time: standing fleet upkeep (bus/cb1/queue.md) <-> assigning/checking projects.
- DADDY (cb2, workhorse, healthiest node, has Drive): EXECUTES project tasks from bus/cb2/queue.md. The doer.
- BRIAN ASSIGNS DADDY (his rule 2026-06-19): Opus does NOT auto-dispatch projects to Daddy. Brian decides the
  order each time. Opus's job on Daddy-idle = SURFACE it to Brian with the ranked options; Brian picks; THEN
  Opus writes the chosen task to bus/cb2/queue.md. Keeps Brian in control of what the workhorse builds.
- WHAT OPUS STILL DOES AUTONOMOUSLY: its own fleet upkeep + Jane (bus/cb1/queue.md), and VERIFYING Daddy's
  output when he reports. Only PROJECT assignment to Daddy waits for Brian.

## DADDY-IDLE SIGNAL (how Opus knows to SURFACE to Brian — not auto-dispatch)
- Daddy's to-opus.md "CURRENT JOB" + "DONE SINCE" lines. If DONE == his queue top, or he says "awaiting order",
  he is idle -> Opus tells BRIAN "Daddy's free; ranked options are X/Y/Z" and waits for Brian's pick.
  (Daddy never self-assigns; Opus never auto-assigns projects; Brian chooses. Daddy = doer.)

## RULES (from kernel)
- Verify every "done" with a test artifact (vantage-test for user-facing). No self-declared greens.
- Opus reserves itself for hard reasoning; routine/grind -> Daddy + cheap models (token best-practice).
- Irreversible-5 (keys/spending/go-live/wipe/delete-truth) -> Brian decides.
