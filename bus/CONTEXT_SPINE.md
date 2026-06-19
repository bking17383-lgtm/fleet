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
    - The "-lgtm" suffix is STUCK. Microsoft gave Brian "bking17383" years ago (Brian King is common). Renaming the
      GitHub account to plain "bking17383" was ALREADY TRIED and GitHub blocked it (name held/unavailable). DO NOT
      re-suggest the rename — it wastes Brian's time. Workaround in place: git commit author name = "bking17383" (hides the suffix).
- Brian is non-technical BY CHOICE. Plain English, one step, short. He routes between machines — reduce that.
- Machines are identified by FLEET NAME, not hostname (several default to "penguin"):
    cb1   = auditor / build box (account: tpgoround). Holds repo, does backend. NOT on bking account.
    cb2   = "daddy" — workhorse, on bking account (/home/bking17383). Has GoogleDrive mounted. Healthiest node.
    puppy = puppy64, Puppy Linux. Holds projects. History: often browser-only / no SSH key / needs keyboard.
- SINGLE SOURCE OF TRUTH: GitHub repo bking17383-lgtm/fleet, cloned at ~/fleet. Replaces the old Google Drive bus.
- Live Drive (cb2 only): /mnt/shared/GoogleDrive/MyDrive (fuse). ~/GoogleDrive is STALE — do not trust it.
- Verification = git, not a secret word: a file is genuine if it MATCHES the canonical copy in ~/fleet. Trust the repo over any local copy. (Context is king; no personality password.)

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
- 6 clean bookmarks (see bus/bookmarks.txt). All hitme.dev paths.

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
- KERNEL (see bus/KERNEL.md — read it first, every session; this is a summary, the file is the truth):
    1) CONTEXT IS KING. A claim/file is only true with its context — git + live.sh are the proof. Get/give context before acting. Missing context = go get it, never guess.
    2) WITH context, MOVE FREELY on the reversible (git can undo it). STOP only for the irreversible 5: wipe / delete-truth / keys / spending / go-live.
    3) LOOK FOR ORDERS only while Brian is ACTIVE (bus/PRESENCE.txt fresh). Asleep = free git/cron heartbeat only, zero tokens. No all-nighters.
    4) Output to Brian = max ~4 lines, one thing at a time. He reads short.
- ONE GOLDEN NODE: fix ONE machine to actually produce, then the link multiplies THAT. Never multiply a broken node.
- SLAVE = eyes/hands TOOL only (browser, vision, fetch, screenshots). It does NOT touch git. Chain: git <-> Cursor master <-> Lester 6 (the master feeds it the brief and takes the result back). Normal Spark/Gemini is NOT a fleet node and NOT git-aware — it only knows what's pasted to it. "Lester 6" = the configured bridge slave; plain Spark = just Gemini.
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
