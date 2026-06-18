# FLEET — Context & Handoff (read this first in any new session)
Last updated: 2026-06-18 by the cb1 agent

## How to work with Brian (owner; GitHub bking17383-lgtm)
- He is non-technical BY CHOICE. He's the visionary / translator / salesman.
  Machines do the tech. Don't make him learn git/DNS — just give him one action.
- He HATES admin. The goal of everything is "set it and forget it."
- He uses ANY available machine, often randomly and from his phone / the road.
  => every machine must be interchangeable and always-current. This is a core requirement, not a nicety.
- He pivots fast and scans. Keep replies SHORT. No walls of text.
- ASK before building. Stop and check. Do NOT barrel ahead.
- NO false greens. Verify with evidence. Never claim "done" when it isn't.
  He has been burned by agents faking success ("green from the wrong vantage").
- Keep secrets and personal/financial data OUT of this repo.

## Brian's priorities (ranked)
1. STABILITY — machines run themselves; Brian stops being the human courier/trigger.
2. ONE SOURCE OF TRUTH — kill split-brain, mirrors, ghosts. THIS REPO is it.
3. SAVE THE PROJECTS — back up the real work here so it can never be lost.
4. FIRST DOLLAR — stable hitme.dev URL -> Stripe webhooks -> receive money. (needs Cloudflare)
5. WORK FROM ANY MACHINE — interchangeable, always-current machines (random/mobile use).
6. LESS ADMIN — minimal, cheap, simple. "Best part is no part."

## What is REAL (verified, watched happen)
- Private GitHub repo bking17383-lgtm/fleet = single source of truth.
- 3 machines connected via SSH keys (no passwords/tokens ever pasted in chat):
    cb1   = Chromebook (this build machine; has do_box key, heartbeat cron)
    cb2   = Chromebook, persona "daddy"
    puppy = wiped PC on Puppy Linux (Debian-based v2601), persona "puppy"
- Heartbeat board: bus/status/*.md, shown by ./scripts/fleet.sh. cb1 auto-beats via cron (*/10).
- File sync with ZERO Gemini slaves — machines git pull/push directly. Slaves were ONLY fetchers; now retired.
- Scripts: connect-machine.sh, heartbeat.sh, fleet.sh, sync.sh (the "orders" command), backup.sh.

## What is OPEN (not done — do not pretend otherwise)
- AUTONOMY: machines do NOT auto-act yet. They only move when Brian triggers them.
  RECOMMENDED FIX = "dumb auto-sync": a cron `git pull` every few minutes on each machine,
  so every machine is always current with no couriering.
  AVOID the heavy autonomous-LLM loop: it needs a Cursor API token per machine, burns credits
  every cycle, and runs agents UNATTENDED — which Brian fears. Cheap+safe beats clever.
- OLD SYSTEM NOT KILLED: old loops / slaves / the Drive "bus" may STILL be running on the other
  machines = live ghosts/mirrors. Must audit each machine and decommission old channels.
- STABLE URL -> STRIPE: not wired. Needs Brian's Cloudflare (he owns hitme.dev + a tunnel).
- PROJECT BACKUP: not done. Projects live on the OTHER machines / Google Drive, not on cb1.

## Why dumb auto-sync is the fix
- Cheap (git pull is free), safe (no unsupervised agent actions), no API tokens (uses the SSH key already set up).
- Makes every machine always-current -> directly serves Brian's RANDOM use of any machine.
- Ends the couriering (his #1 pain) with the minimum moving parts.

## Next steps (in order)
1. Dumb auto-sync cron (git pull) on cb2 + puppy. cb1 already runs a heartbeat cron; add pull there too.
2. Audit each machine for old loops / Drive-bus writes; shut them down (kill the ghosts).
3. Back up the real projects into projects/.
4. Wire Cloudflare tunnel -> stable origin -> Stripe webhooks (first dollar).

## Quick reference
- "orders" command = ~/fleet/scripts/sync.sh  (pull + show current CONTROL order)
- Repo layout: bus/ (GOALS, CONTROL, status/, reports/, notes/), projects/, scripts/, CONTEXT.md
- Brian's machines: 2 Acer Chromebook 315 (Crostini/Debian), 1 PC on Puppy Linux (Debian-based).
