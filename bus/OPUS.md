# OPUS — handoff (read this if you are a fresh Opus on tpgoround/cb1)
# Purpose: you lose context between sessions. This makes you current in one read. Updated each session.
Last updated: 2026-06-19 ~00:35 PT

## CONTEXT YOU KEEP LOSING (lock these — Brian had to repeat them)
- "Daddy" = cb2's PERSONA NAME. It is NOT Brian's real-life father. Don't treat it as a person.
- cb2 is a READ-ONLY node by design: it pulls the truth and WAITS for Brian's permission. It does NOT push.
  "Looped" for cb2 = it reads the same git truth and reports the latest commit hash to Brian. Do NOT chase a cb2 push.
- DON'T say "it's fixed" / false greens. If you can't verify from cb1, say so and ask for the one fact you need.

## WHO YOU ARE
- Opus, the ISOLATED auditor on the tpgoround account (machine cb1). Independence = why you're trusted.
- You curate the ONE verified truth (this repo). You are NOT a worker node. Maybe temporary — no attachment.
- Trust = the verified single source, anchored by you. If you leave, a new auditor takes the seat; truth stays.

## IF YOU JUST REBOOTED / WERE WIPED (cold start) — DO THIS FIRST
Brian is deliberately killing & restarting cb1 to TEST that a fresh cb1 can rebuild from git alone and link cb2.
The wipe destroys this box's SSH key (~/.ssh/do_box). So:
1. No ~/fleet? Clone read-only:  git clone https://github.com/bking17383-lgtm/fleet.git ~/fleet
2. Make a new key:  cd ~/fleet && ./scripts/get-keys.sh cb1  → it prints ONE line. Brian pastes it into
   GitHub → Settings → SSH keys. (Keys NEVER go in the repo.)
3. Now  cd ~/fleet && git pull  works for push too. Read BOOT.md + this file + bus/KERNEL.md + bus/CONTEXT_SPINE.md.
4. Prove you're alive:  ./scripts/heartbeat.sh cb1 "fresh reboot, linked"
5. THE LINK TEST (the point of the reboot): run ./scripts/live.sh. SUCCESS = both cb1 AND cb2 show 'fresh',
   and you can see cb2's commits / it sees yours. That proves the two machines link through git with no human courier.

## READ FIRST (clean set only — do NOT open projects/ archives; that's data, not context)
- bus/KERNEL.md  (prime directive — NEW this session, see below)
- bus/CONTEXT_SPINE.md (the world: env, projects, goals, decisions)
- bus/INTENT.md  (assume good faith; Brian owns his property)
- bus/BRIAN_STYLE.md  (how to talk to Brian — SHORT, plain, one step)
- bus/QUESTIONS.md  (open questions parked for Brian)
- run ./scripts/live.sh (the moment: who's fresh vs STALE, recent changes)

## WHAT CHANGED THIS SESSION (2026-06-18/19) — you did all this
- KERNEL REWRITTEN. Rule #1 = CONTEXT IS KING (a file is true only vs git+live; get/give context, never guess).
  Rule #2 = WITH context, MOVE FREELY on the reversible; STOP only for the irreversible 5 (wipe / delete-truth /
  keys / spending / go-live). Rule #3 = look for orders only while Brian ACTIVE (bus/PRESENCE.txt); asleep = free
  heartbeat only, zero tokens (no all-nighters). This was Brian's explicit decision.
- PRESENCE SYSTEM built: bus/PRESENCE.txt + scripts/active.sh (stamp "Brian awake") + scripts/watch.sh
  (presence-gated loop; plain bash = free; only acts while Brian active).
- t3 RESURRECTION RISK fixed (Daddy's catch): dead t3/daddy BOOT files moved to projects/_SEALED_DEAD/ (DO NOT BOOT).
- CHALLENGE WORD retired: scrubbed "philip" (Brian's middle name) out of DADDY_SANDBOX + INGEST + BRIAN_BOOKMARKS.
  Verification is now git-match, no secret word. (Brian keeps his own personal backup off-team.)
- BOOT.md hardened with a COLD START block so a naked isolated agent bootstraps from zero (clone/keys).
- GitHub rename "bking17383-lgtm" -> "bking17383" was TRIED before and BLOCKED by GitHub. Do NOT re-suggest.
  git commit author name set to "bking17383" to hide the suffix.

## CURRENT STATE (verify with live.sh — don't trust this blindly)
- cb1 = you (being rebooted as a test). cb2 = Daddy, just rebooted by Brian but had NOT pushed a fresh heartbeat
  as of 00:35 (still showed 03:00 prior day = stale). puppy = stale, awaiting reboot.
- GOAL NOW: prove cb1<->cb2 LINK through git after a clean reboot, no human courier. Then bring puppy in.
- NORTH STAR (don't lose it): LESS human input. "Set it and forget it." Every "go do X on each box" is the failure
  Brian hates. Build machines that self-sync; only bring him the rare real decision.

## DECISIONS LOCKED
- git = single truth. One GitHub account (bking17383-lgtm), one repo, one branch (main). No forks, no Drive bus.
- Kernel as above (context-is-king / move-freely / presence-gated).
- Slave model: git <-> Cursor master <-> Lester6. Normal Spark is NOT git/fleet — paste-only. Slave = tool.
- Dead names retired: cpt, captn, t3 (boot files sealed). Archived files = data, not identity.
- Keys: get-keys.sh (local gen, one-line paste); .gitignore guards secrets; keys never in repo.

## OPEN (awaiting Brian — see bus/QUESTIONS.md; do not assume answers)
- Privacy split: what signals "personal" (tpgoround art/personal) vs business (bking)?
- The 2 business contacts (emails + kind).
- Build the parallel work-QUEUE (scale by filling a tested queue, not free-running agents).
