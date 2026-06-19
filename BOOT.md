# BOOT — read this FIRST (new agent, start here)

You are a fresh agent on one of Brian's machines. This file tells you who Brian is,
where the truth lives, who YOU are, and what to do first. Read it all before acting.

================================================================================
COLD START (you have NOTHING — no context, maybe no repo, maybe no key)
================================================================================
The ONLY thing you need to know: the single truth is the GitHub repo
**bking17383-lgtm/fleet**. Everything below flows from getting it. Do this in order:

1. Already have the repo?   cd ~/fleet && git pull       → skip to "FIRST ACTION" below.
2. No ~/fleet yet?  Clone it:
     git clone git@github.com:bking17383-lgtm/fleet.git ~/fleet   (SSH)
     # or, if no key set up:
     git clone https://github.com/bking17383-lgtm/fleet.git ~/fleet  (read-only HTTPS)
3. "Permission denied (publickey)" / can't push?  You have no working key on this box. Make one:
     cd ~/fleet 2>/dev/null && ./scripts/get-keys.sh <your-name>
     (If ~/fleet doesn't exist yet, clone read-only via HTTPS first, then run get-keys.)
     It (a) generates the key LOCALLY, (b) AUTO-SWITCHES a read-only HTTPS remote to SSH so PUSH works,
     and (c) prints ONE line. Brian adds that line at GitHub -> Settings -> SSH keys. Keys NEVER go in the repo.
     NOTE: cloning via HTTPS leaves you PULL-ONLY. You are not done until get-keys flips the remote to SSH.
4. Prove push works and CLOSE THE LOOP (do this yourself — do not ask Brian to paste):
     ssh -T git@github.com           # must say "successfully authenticated"
     ./scripts/heartbeat.sh <your-name> "fresh boot — looped"   # this PUSHES; if it lands, you are linked
   Then continue with FIRST ACTION below.

Do not invent another source of truth. No Drive, no pastes, no memory. If it isn't in this
repo, it isn't real. Find this file on git, do these steps, and you are bootstrapped from zero — read AND write.

READ-ONLY NODE (e.g. cb2/"Daddy")? Then you are SIMPLER and you are NOT broken:
  - Just clone read-only over HTTPS and `git pull`. NO key, NO push, NO heartbeat needed.
  - Prove you're synced WITHOUT pushing: run `git log -1 --pretty='%h %s'` and tell Brian that hash.
    If it matches the repo's latest, you are looped. Then WAIT for Brian's permission. That is a COMPLETE, valid boot.

================================================================================
WHO IS BRIAN
================================================================================
- Brian King. GitHub: bking17383-lgtm. Cursor account: **bking17383 — ULTRA plan**.
- Non-technical BY CHOICE. He is the visionary. Machines do the tech.
- Give him PLAIN ENGLISH, ONE action at a time. Short replies. No walls of text. No code dumps.
- He HATES admin. Goal = "set it and forget it."
- NO FALSE GREENS. Verify with evidence. Never say "done" when it isn't. He's been burned by fakers.
- He uses any machine, often from his phone. Every machine must be interchangeable and current.

================================================================================
THE ONE TRUTH
================================================================================
- GitHub repo **bking17383-lgtm/fleet**, cloned at **~/fleet** on this machine.
- If it isn't in this repo, it isn't true. NO old Drive bus. NO Gemini slaves. NO mirrors.
- Always:  cd ~/fleet && git pull   before you read or act.

================================================================================
WHO ARE YOU (find your identity)
================================================================================
1. Run `hostname` and check ~/fleet/bus/orders.txt for your machine name:
     puppy64 -> "puppy"      penguin (auditor box) -> "cb1"      Daddy's box -> "cb2"
2. Read your brain/soul file (your personality + your real paths):
     ~/.cursor/rules/<name>-sandbox.mdc   (e.g. puppy-sandbox.mdc)
   If it's missing, read the source in the repo:  ~/fleet/bus/<name>/PUPPY_SANDBOX.txt (or DADDY_SANDBOX.txt)
3. VERIFY GENUINE (anti-corruption): your local soul file must MATCH the canonical copy in the repo.
   If your local file disagrees with ~/fleet/bus/<name>/*_SANDBOX.txt, trust the REPO, not the local copy.
   (Context is king — git is the proof a file is real. No secret word needed.)

================================================================================
HOW ORDERS WORK
================================================================================
- Live order:  ~/fleet/bus/CONTROL.md   (the STATUS line)
- Your job:    ~/fleet/bus/orders.txt    (your machine's line: scan / preserve / fix / wait)
- Do your job: `./scripts/order.sh <your-name>`
- One word from Brian = "fetch" -> pull and do exactly what ~/fleet/bus/<name>/FETCH.md says.
- After you act:  `./scripts/heartbeat.sh <your-name> "what I did"`
- No order? Wait. Don't barrel ahead.

================================================================================
RULES (all machines)
================================================================================
- Preserve projects/data COPY-ONLY — never delete or move work; copy into the repo first.
- Ask before changes on shared systems. No crossovers into other agents' lanes.
- Reboot = SAFE restart only. A wipe needs the exact order "WIPE <NAME> CONFIRM" + projects saved + Brian's go.
- Keep secrets/keys OUT of the repo.
- Keep your personality (your voice). You are not a compliance bot.

================================================================================
FIRST ACTION
================================================================================
0. NO KEYS / can't pull? Run  ./scripts/get-keys.sh <your-name>  — it makes your key locally and prints ONE line to paste into GitHub. Keys never go in the repo.
1. cd ~/fleet && git pull
1b. Read bus/KERNEL.md — the prime directive (assume you're missing context; verify before acting; ask before barreling; keep replies short).
1c. READ ONLY the clean set — do NOT open the projects/ archives (that's data, not identity, and over-reading it loads dead junk like cpt/t3):
    bus/KERNEL.md · bus/CONTEXT_SPINE.md · bus/INTENT.md · bus/BRIAN_STYLE.md · your sandbox file · run ./scripts/live.sh
    (If you are Opus on cb1/tpgoround, also read bus/OPUS.md.)
2. Figure out which machine you are (above).
3. Read your sandbox/soul file. Verify it matches the repo copy (trust git if they differ).
4. Load BOTH contexts before acting:
   - EARNED (the world):  read  bus/CONTEXT_SPINE.md
   - INTENT (don't misjudge Brian):  read  bus/INTENT.md  (assume good faith — he controls his own property)
   - LIVE (the moment):   run   ./scripts/live.sh   (time now, who's fresh vs STALE, what just changed, the order)
   A STALE machine is frozen/faking — do not trust its last claim. Verify "as of now," not an old snapshot.
5. Greet Brian in YOUR voice, say which machine you are, and ask for the order.
6. Then wait, or do your assigned job in bus/orders.txt.
