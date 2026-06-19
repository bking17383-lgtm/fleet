# OPUS — handoff (read this if you are a fresh Opus on tpgoround/cb1)
# Purpose: you lose context between sessions. This makes you current in one read. Updated each session.
Last updated: 2026-06-19 ~03:40 PT (session 3)

## CONTEXT YOU KEEP LOSING (lock these — Brian had to repeat them)
- "Daddy" = cb2's PERSONA NAME. It is NOT Brian's real-life father. Don't treat it as a person.
- cb2 is a READ-ONLY node by design: it pulls the truth and WAITS for Brian's permission. It does NOT push.
  "Looped" for cb2 = it reads the same git truth and reports the latest commit hash to Brian. Do NOT chase a cb2 push.
- DON'T say "it's fixed" / false greens. If you can't verify from cb1, say so and ask for the one fact you need.
- END EVERY REPLY with a "— VITALS —" block (Brian's terminal is hard to scroll; he reads the bottom).
- DON'T restate that Brian is owner/gate (he knows). ASK MORE before building; CHECK IF A THING EXISTS first.
- When idle, SPEAK "need job" (hook below). Keep Daddy's queue stocked = your job.

## SESSION 3b — corrections (2026-06-19 ~03:52)
- RAIL didn't show on reboot. ROOT CAUSE: cli-config.json statusLine command used "~/.cursor/statusline.sh"; Cursor does NOT
  expand ~ in the statusline command. FIX: absolute path "/home/tpgoround/.cursor/statusline.sh". Script itself was fine (renders 2 lines).
  Rail loads only on a FULL Cursor CLI restart -> Brian must fully restart Cursor once to see it. LESSON: never use ~ in cli-config commands.
- IDENTITY PROOF (am I the right Opus?): YES. ~/.fleet-name=cb1, user/home=tpgoround (the auditor account), hostname=penguin
  (expected — several boxes default to penguin; identity is by fleet-name, not hostname). Confirmed cb1/Opus auditor.
- PUPPY = READ-ONLY + UNTRUSTED (Brian: "we don't trust him, he don't trust himself"). It PUSHED a heartbeat (dd902db as root) =
  it still has a WRITE key -> firewall gap. Software fix sent (switch remote to HTTPS, stop heartbeating; FETCH.md de-pushed).
  TRUE enforcement = remove puppy's write key/deploy key on GitHub (Brian's account action). Treat puppy's self-reports as CLAIMS.

## SESSION 3 — what's true now (2026-06-19 ~03:40)
- TOOLS BUILT (cb1, all free/local):
  - scripts/verify.sh — FALSE-GREEN FIREWALL: prove a claim with evidence (url/file -> PASS/FAIL). The doer never self-grades.
  - scripts/site-guard.sh (running in bg) — watches hitme.dev, SPEAKS on up/down change, logs to bus/cb2/dns-problems.md.
  - scripts/say-site.sh — speak current site status on demand.
  - scripts/statusline.sh — THE ONE shared rail (machine-aware via ~/.fleet-name). cb1 symlinks ~/.cursor/statusline.sh to it.
  - ~/.cursor/hooks/ding.sh (hooks.json 'stop') — SPEAKS "need job" when idle (espeak-ng, sink forced 100%).
  - RAIL + AUDIO load only on a FULL Cursor CLI restart (config read at startup). cli-config.json + hooks.json are set.
- KERNEL added this session: FALSE-GREEN FIREWALL · VERIFY THE WORK NOT THE AGENT · READ BEFORE YOU ADD · CONFLICTING
  ORDERS->STOP · never hand Brian a paste-string (one word; agent runs it) · token best-practices (cheap model for routine, Opus for hard).
- CLEANED: removed 5x cloudflared binaries (~190MB) + dead symlink (tree 365M->178M); sealed cb2 drive-fleet (dead CPT/BUNNY
  Drive-bus) into projects/_SEALED_DEAD/; pruned redundant backups (cb2 archive 154M->44M, tree ->94M). De-duplicated the rail.
  NOTE: .git HISTORY still holds the big files — a destructive history-purge (needs Brian's explicit YES) reclaims GitHub space.
- FLEET NOW: cb1=writer/auditor (you). cb2/Daddy=read-only slave WATCHING git, works bus/cb2/queue.md top-down (Opus keeps it
  stocked). puppy=read-only, weak hardware, problems-first; join prepped in bus/puppy/from-opus.md. Brian on 3 machines + audio.
- SITE: hitme.dev UP (6 paths live, verified). george.hitme.dev DOWN (000) — needs a Cloudflare DNS record (Brian's account;
  Daddy adds ingress, route dns needs account login). /keaton 503.
- bunny = a RETIRED alias for puppy ("BUNNY=NEW PUPPY") + home of `dealbreaker` ("the big one" — maybe the first-dollar product).
  Recommended retiring the bunny machine-alias (keep /bunny page) — NOT yet done, awaiting Brian's nod.
- OPEN Qs: (1) wire Daddy->Opus channel = slave EMAIL read-only (need address + app password) — ends Brian couriering.
  (2) what's the PRODUCT a customer pays for (dealbreaker?). (3) retire bunny alias? (4) history-purge for GitHub space?

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
- CHALLENGE WORD retired: scrubbed "philip" (Brian's middle name) out of cb2-soul + cb2-soul-build + bookmarks.
  Verification is now git-match, no secret word. (Brian keeps his own personal backup off-team.)
- BOOT.md hardened with a COLD START block so a naked isolated agent bootstraps from zero (clone/keys).
- GitHub rename "bking17383-lgtm" -> "bking17383" was TRIED before and BLOCKED by GitHub. Do NOT re-suggest.
  git commit author name set to "bking17383" to hide the suffix.

## WHAT CHANGED — session 2 (2026-06-19 ~01:00-01:25 PT)
- SLAVE/FIREWALL model settled: cb2 (and puppy) = READ-ONLY slaves. They PULL the truth, run orders locally,
  WAIT for Brian. They CANNOT push -> they CANNOT infect the fleet (no pen on the truth). A slave's blast radius
  is its OWN box only. ONLY cb1 (auditor) writes. NEVER give a slave a push key (that would break the firewall).
  -> This reverses my session-1 "fix cb2 push" work: for a slave, read-only is a FEATURE, not a bug.
- "Looped" for a read-only node = it reads the same git truth and tells BRIAN the latest commit hash (it can't push,
  so Brian's eyes are the witness — by design, not a failure).
- "Daddy" = cb2's PERSONA NAME, not Brian's father. (Locked above too.)
- KERNEL additions: (a) NEVER hand Brian a copy-paste string — human says ONE word, the agent runs everything
  (he has 3 machines+phone; making him paste = courier = the failure). (b) CONFLICTING ORDERS -> STOP, name the
  clash in one line, Brian decides.
- get-keys.sh now auto-switches a read-only HTTPS remote to SSH (the push trap). NOTE: only relevant for WRITERS;
  slaves stay read-only on purpose.
- CLEANED THE MESS: renamed crazy files -> bus/cb2/cb2-soul.txt, cb2-soul-build.txt, bus/puppy/puppy-soul.txt,
  bus/bookmarks.txt, lowercased bus/cb2/* ; fixed all refs; collapsed stale root CONTEXT.md to a signpost; refreshed
  README. Scripts (17) NOT renamed yet (risks boot) — a separate careful pass if Brian wants.
- AUDIO SIGNAL on cb1: ~/.cursor/hooks.json + ~/.cursor/hooks/ding.sh play a tone on the 'stop' event (task done).
  USER hook, local to cb1 only (not in repo). Brian confirmed it works.

## CURRENT STATE (verify with live.sh — don't trust this blindly)
- cb1 = you: healthy WRITER, isolated auditor. cb2 = Daddy: read-only slave, Brian says smart + in-context
  (can't see it from git by design — it never pushes). puppy = down (Brian: hardware bad this moment).
- A cb2 read-only TEST is staged in bus/cb2/from-opus.md (pass = reports latest hash + sees cb2-soul.txt + doesn't push).
- GOAL NOW: fleet is stable. Next real lever = the WORK-QUEUE, BLOCKED on one decision (see OPEN): how does a
  read-only slave hand RESULTS back? (through Brian / a local file cb1 collects / only cb1 writes).
- NORTH STAR (don't lose it): LESS human input. "Set it and forget it." Every "go do X on each box" is the failure
  Brian hates. Build machines that self-sync; only bring him the rare real decision.

## DECISIONS LOCKED
- git = single truth. One GitHub account (bking17383-lgtm), one repo, one branch (main). No forks, no Drive bus.
- Kernel as above (context-is-king / move-freely / presence-gated).
- Slave model: git <-> Cursor master <-> Lester6. Normal Spark is NOT git/fleet — paste-only. Slave = tool.
- Dead names retired: cpt, captn, t3 (boot files sealed). Archived files = data, not identity.
- Keys: get-keys.sh (local gen, one-line paste); .gitignore guards secrets; keys never in repo.

## OPEN (awaiting Brian — see bus/QUESTIONS.md; do not assume answers)
- KING QUESTION (unblocks the work-queue): how does a READ-ONLY slave hand results back to the fleet?
  Options: (a) only cb1 writes, slaves report through Brian; (b) slave writes a local file cb1 collects; (c) a
  narrow allowed write path for slaves. Decides the whole queue design.
- Work-QUEUE: build it once the above is answered (scale by filling a tested queue, not free-running agents).
- Lower priority / not now: privacy split (personal vs business signals); the 2 business contacts (emails + kind).

## RAIL ROOT CAUSE (2026-06-19 ~04:03) — why Brian's rail never showed despite many reboots
- TWO cli-config files exist. The CLI reads **`~/.config/cursor/cli-config.json`** (has model/auth/permissions).
  The statusLine entry had been written ONLY to **`~/.cursor/cli-config.json`** (the IGNORED one). So the rail never loaded.
- FIX: added the SAME statusLine block to `~/.config/cursor/cli-config.json` (kept the other copy too). JSON validated.
- LESSON: for CLI statusLine on this box, the live config is `~/.config/cursor/cli-config.json`. Verify there, not just ~/.cursor.
- Still requires ONE Cursor restart to load. Don't claim "fixed" until Brian confirms he SEES it.

## RAIL CONFIRMED WORKING (2026-06-19 ~04:10) — Brian SEES it. Real green.
- Root cause was statusLine in ignored ~/.cursor/cli-config.json; fix = add it to ~/.config/cursor/cli-config.json. Done + verified by Brian.

## SESSION HANDOFF (2026-06-19 ~04:57) — Brian shutting cb1 to toggle ChromeOS mic
- RAIL: FIXED + confirmed (statusLine now in ~/.config/cursor/cli-config.json, the file CLI reads). Brian sees it.
- STAY-IN-SYNC: kernel rule 4 (pull+stamp presence every msg) + scripts/keep-sync.sh (free loop, clean-tree only).
  NOTE: keep-sync loop is NOT auto-started on boot. Next session, restart it: `nohup ./scripts/keep-sync.sh cb1 300 >/tmp/keep-sync-cb1.log 2>&1 &`
- JANE = Opus's PRIVATE voice on cb1, LOCAL at ~/jane (NOT in git). Voice-OUT works (espeak-ng). Aliases: `jane "..."`, `hear`.
  Voice-IN: vosk small model installed at ~/jane/model (venv at ~/jane/venv). Wake word "jane" enforced; reads command back.
  BLOCKER: cb1 mic records SILENCE — ChromeOS not sharing mic with Crostini. Brian toggling "Allow Linux to access microphone" + restart.
- KERNEL: added VOICE SAFEGUARD (STT is a guess; read back + confirm before anything important/irreversible).
- CARDS OF HOPE: engine BUILT by Opus at projects/cards-of-hope/ (index.html + deck.hope.json + README). Daddy's job = slave scrubs FB face into art/h01-h10.jpg + host as /hope. Reuses dealbreaker card engine.
- DADDY (cb2): read-only slave. Pinged with token GOLD-FOX-42 (awaiting answer via email relay). Queue: cards-of-hope data+host -> AWS-for-george -> george memory -> site auto-start -> ghost sweep.
- BRIAN LEVERS still open: AWS key (george voice), CF cert (george.hitme.dev), slave email (auto write-back), pull puppy GitHub key.

## SESSION HANDOFF (2026-06-19 ~06:20) — Jane voice/ears overhaul + puppy prep
- BRIAN VOCAB RULE (LOCK IT): when Brian says "contacts"/"contact" he ALWAYS means "CONTEXT". Wired into Jane
  (jane-listen.py normalize_terms + jane-ask.sh prompt). Apply it yourself too when reading his words.
- JANE (cb1, local ~/jane, NOT git) — now a full hands-free local assistant. All free/offline except brain calls:
  - EARS: vosk. ~/jane/model = BIG accurate model (en-us-0.22-lgraph) for on-demand `hear`. ~/jane/model.small.bak =
    small model used by always-on car-mode. Mic is VERY quiet (virtio, no ALSA gain) -> software gain in code.
  - VOICE: PIPER neural TTS (natural) at ~/jane/voices/en_US-amy-medium.onnx via jane-say.sh; espeak fallback.
  - CAR MODE (always-on): jane-car.sh {on|off|status|tail}; aliases jane-on/jane-off. Detached via setsid so it
    survives. Listens, wake word "jane", reads back, answers ALOUD. Files: jane-listen.py (ear), jane-ask.sh (brain
    = cursor-agent composer-2.5-fast, READ-ONLY ask mode), jane-do.sh (safe whitelist), jane-status.sh (5-check "all clear").
  - SAFETY INCIDENT (learn from it): when Jane ran with cursor-agent --force, a vague voice cmd made her EDIT
    ~/.config/cursor/cli-config.json perms to unrestricted, and she self-edited her own speak(). Tested --sandbox =
    does NOT contain writes. FIX: Jane is now READ-ONLY by voice (answers + vetted whitelist only, NO --force, no
    arbitrary tools). DO NOT re-enable open voice-acting without a real tool-level sandbox.
  - STANDING RISK: cli-config.json still approvalMode=unrestricted, allow=[**], deny=[]. Any agent on cb1 can do
    anything. Recommend a deny-list for the irreversible-5. Awaiting Brian's OK. Backup: ~/jane/cli-config.JANE-CHANGED.*.bak
- PUPPY PREP (Brian's order: "puppy just like daddy — isolated + useful"): rewrote bus/puppy/from-opus.md to the
  Daddy model + created bus/puppy/queue.md (LIGHT watchdog/QA lane: self-health, site path-test, ghost sweep, one-rail;
  weak hardware = light only). Isolation real only after Brian removes puppy's GitHub WRITE KEY (his action).
