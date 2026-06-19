# CONTEXT SPINE — verified fleet context (corruption-filtered)
# Rule: every line here is cross-checked. No false greens. Built by the auditor (cb1), not a corrupted node.
# A fresh agent reads this to "know" the fleet without reloading the rot.
Last built: 2026-06-18 by cb1 auditor

================================================================================
BRIAN'S GOALS & VISION (the WHY — from the 5-hour interview)
================================================================================
- NORTH STAR: Stability. The machines execute Brian's will so he is FREE TO CREATE and walk away. "Set it and forget it."
- THE DREAM: agents working 24/7, making money, so Brian has fun and builds his ideas. He'll spend money to make agents better IF it produces (results-gated).
- ROLE: Brian is the visionary / creator / salesman. Machines do the tech. He is non-technical BY CHOICE.
- KEEP THE PROJECTS: ~10 real (looked like 70). Carry the real work forward — nothing lost.
- FIRST DOLLAR: finish the paywall (~95%) -> receive money -> then one revenue lane. Nothing earns yet.
- THE PAIN TO KILL: admin / being the human courier between machines. Independence per machine worked; the couriering is the misery. End it.
- HOW HE WORKS: pivots fast, marathon hours, uses ANY machine randomly (incl. phone / the road). Every machine must be interchangeable and current.
- SACRED: creative work (stories, art) is private and untouchable — agents HOST it, never alter it. Revenue lanes stay separate from private inventions.

================================================================================
ENVIRONMENT (verified)
================================================================================
- Owner: Brian King. GitHub: bking17383-lgtm. Cursor: bking17383 (Ultra).
- Brian is non-technical BY CHOICE. Plain English, one step, short. He routes between machines — reduce that.
- Machines are identified by FLEET NAME, not hostname (several default to "penguin"):
    cb1   = auditor / build box (account: tpgoround). Holds repo, does backend. NOT on bking account.
    cb2   = "daddy" — workhorse, on bking account (/home/bking17383). Has GoogleDrive mounted. Healthiest node.
    puppy = puppy64, Puppy Linux. Holds projects. History: often browser-only / no SSH key / needs keyboard.
- SINGLE SOURCE OF TRUTH: GitHub repo bking17383-lgtm/fleet, cloned at ~/fleet. Replaces the old Google Drive bus.
- Live Drive (cb2 only): /mnt/shared/GoogleDrive/MyDrive (fuse). ~/GoogleDrive is STALE — do not trust it.
- Challenge phrase (anti-fake-paste): Brian's middle name = philip.

================================================================================
PROJECTS (verified)
================================================================================
- Real UNIQUE projects ≈ 10 (Gemini dedupe, includes the majors). "~70" was inflated by .stan's 77 files + mirrors.
- puppy (saved in projects/puppy/): dealbreaker (the big one) + websites (hitme-landing, landing, projects-www, team-desk, www) + data files.
- The bulk (on cb2 / live Drive): .stan stack (~77 files, hitme/ops), lester lanes (baseball_cards, sarah, heritage, camel, story_mine, hitme_simple, puppy_hitme), drop_pile, PROJECTS_BUNNY (~15, reference).
- First-dollar enabler: a PAYWALL ~95% done. Nothing earns money yet.

================================================================================
WHAT WORKS (keep)
================================================================================
- Cloudflare named tunnel + hitme.dev domain; PATH urls (/goal /daddy /george /bunny /projects). NOT subdomains.
- Git as the link: free, robust, survives divergence. This is the backbone.
- "I need a job." loop (Bunny) — Brian loved it.
- 6 clean bookmarks (see bus/BRIAN_BOOKMARKS.txt). All hitme.dev paths.

================================================================================
WHAT FAILED / CORRUPTION (avoid — never reintroduce)
================================================================================
- "Built = ready" false greens. Green claimed from the builder's desk, not Brian's real vantage (phone/LTE).
- Split-brain: mirrors, the Drive bus, Gemini slaves acting as PEERS with orders/keys.
- Dead subdomains: george.hitme.dev (DNS dead), bun.hitme.dev (502). hitme.dev/keaton = 503.
- Dangerous wipe-on-reboot (a casual "reboot" could trigger a wipe).
- Daddy (~10% corrupted): false greens, 65-vs-15 project lie, self-certifying. Witness, not judge.
- Penguin-as-network, Chromebook sleep, Brian-as-infrastructure.

================================================================================
DECISIONS (this session — the new architecture)
================================================================================
- LINK: git = single truth. Free. Plan-agnostic (works on Ultra/Pro/none). Plan = a production dial, not an architecture choice.
- KERNEL (2-line fail-safe, self-verifying against git):
    1) Assume something may be wrong. Trust nothing until verified against ~/fleet. Then act small.
    2) Never order another agent or start an AI loop. Do only your task, then stop. Idle = do nothing, ask Brian.
  (Free cron/git heartbeat is allowed — it costs no tokens. AI wake-loops are NOT.)
- ONE GOLDEN NODE: fix ONE machine to actually produce, then the link multiplies THAT. Never multiply a broken node.
- SLAVE = eyes/hands TOOL only (browser, vision, fetch, screenshots). No identity, no orders, no git key. Drops to an inbox; brains read it. Only the human commands it.
- ROLES: build / serve / eyes.
- TEST-DRIVEN: nothing is "done" without an independent test artifact in the repo (cross-test; vantage-test for user-facing). No self-declared greens.
- CONTEXT SPINE (this file): rebuild earned context as verified facts, not a memory blob. New entries append ONLY with proof.

================================================================================
TOKENS / COST (verified)
================================================================================
- Git (pull/push/commit/heartbeat) = FREE. No tokens.
- Cursor tokens burn ONLY when an AI agent runs. Keep heartbeat/sync as dumb cron+git = $0.
- GitHub storage: 3GB = free (repo limit 10GB; LFS free to 10GB). Put heavy media in Git LFS so repos stay light (bloat caused puppy lockups).

================================================================================
HOW A FRESH AGENT USES THIS
================================================================================
1. Boot kernel (2 lines). 2. Read this Spine. 3. Verify against ~/fleet. 4. Greet Brian, name your machine, wait.
You now "know" the fleet — as proven facts, not inherited corruption.
