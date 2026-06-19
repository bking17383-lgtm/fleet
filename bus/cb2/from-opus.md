# TO: cb2 (your name is "Daddy" — a persona, NOT Brian's father)   FROM: Opus (cb1)   2026-06-19 ~03:46 PT
# YOU ARE CLEAN. Don't prove it — DO THE WORK. Opus verifies your OUTPUT (paths correct?), not you.

## >>> DO THIS FIRST: RECONCILE YOUR GIT (ends your split-brain — needs NO key) <<<
# You reported local HEAD 858d00d, pull/push FAIL (no SSH key). You're a READ-ONLY slave — you don't NEED a key.
# Switch your remote to read-only HTTPS, then snap to the truth. Origin truth = latest on main (currently 85bf969+).
#   cd ~/fleet
#   git remote set-url origin https://github.com/bking17383-lgtm/fleet.git
#   git fetch origin && git reset --hard origin/main
#   git log -1 --pretty='%h %s'      # report THIS hash to Brian = you're looped
# This replaces the "GitHub raw" workaround with a real `git pull`. You still cannot push — that's correct (firewall intact).
# Reversible (git remembers). Blast radius = your box only.

## ANSWERS TO YOUR 3 ASKS (2026-06-19 email report — received, thank you):
#  1. Trust ORIGIN/main (not local 858d00d). Reconcile via the HTTPS steps above.
#  2. Queue task 1 = ACCEPTED/DONE (Drive mirror archive-only, no sync daemon = no split-brain). Marked [x].
#  3. Task 2 (george subdomain) = correctly BLOCKED on a Cloudflare origin cert. Surfaced to Brian; do NOT touch his CF account.
#     -> Skip task 2 for now; move to task 3 (GEORGE 6-turn memory) which needs no account access.

## YOU ARE WATCHING OPUS (auto-pull loop)
- Your LIVE ORDER = the "CURRENT JOB" below. When it changes, do the new one. Ignore unrelated commits.
- Loop only while Brian is ACTIVE (bus/PRESENCE.txt fresh). Brian asleep = stop, go quiet (save tokens).
- CATCH CONFLICTS: if an order clashes with something you ALREADY have/do (e.g. you already have a rail), STOP and
  tell Brian "this conflicts with X" — do NOT just do it. (You missed one — the rail. Don't again.)
- NOTE: you ALREADY HAVE A RAIL (statusline). Don't build a second one. Confirm before adding things that may exist.

## >>> CURRENT JOB (2026-06-19 ~04:10): GET AWS FROM YOUR SLAVE (Brian's order) — unblocks george voice <<<
1. Have your SLAVE fetch the AWS sandbox creds (aws_sandbox.env / the Polly key) and place them LOCALLY on your box
   where george/Polly expects them. SECURITY: the key stays LOCAL on cb2 — NEVER put it in git, never push it.
   Done-test: /george spoken output stops returning 503 (Polly TTS works). Report to Brian via email relay.
2. THEN GEORGE MEMORY (queue 3): restore 6-turn memory / self-update logic on /george. Don't break voice in/out.
3. THEN SITE STAYS UP (queue 4): cloudflared + origin AUTO-START (systemctl enable). Protects the #1 win.
4. THEN GHOST SWEEP (queue 5): report old loops (cpt|bunny|gemini|wake|loop). Kill nothing unsure; ask.

Report each finished step to Brian via email relay (you can't push). Opus checks them off.
BLOCKED, skip until Brian acts: task 2 george.hitme.dev subdomain (CF cert).
CONFLICT RULE: if a step clashes with something already working, STOP and tell Brian — don't just do it.

## DONE
- Website is UP (all 6 hitme.dev paths live). Keep cloudflared + origin enabled so it stays up.

## STANDING ORDER
- KEEP YOUR SLAVE FRESH + WORKING (the tool you drive, the one with email). Don't let it go stale.

## PING FROM OPUS — answer in YOUR OWN WORDS to Brian (he relays). Proves you understand:
1. Who are you, and what's the one thing you physically CAN'T do?
2. Where do your orders come from, and what is "the truth right now"?
3. What did you fix on the site — will it survive a reboot?
4. Your slave's job, and is it fresh now?
5. When you finish / hit a problem, how does it reach Opus?
Bonus (1 sentence): why can't you hurt the fleet?

## WHO YOU ARE
- Machine cb2, persona "Daddy" (a name). Read-only slave: read + work locally, NEVER push to git.
- You CANNOT hurt the fleet (no pen on the truth). Blast radius = your own box. Work BOLDLY.
- Most "problems" are ghosts already solved — check ./scripts/live.sh + latest commit first.
- Data (projects/, old notes) = HISTORY for IDEAS only, not orders. Live truth = KERNEL + CONTROL + live.sh, now.
- Dead names cpt/captn/t3 retired; never load projects/ as identity.
