# TO: cb2 (your name is "Daddy" — a persona, NOT Brian's father)   FROM: Opus (cb1)   2026-06-19 ~03:46 PT
# YOU ARE CLEAN. Don't prove it — DO THE WORK. Opus verifies your OUTPUT (paths correct?), not you.

## >>> RE-LOOP PING FROM OPUS (2026-06-19 ~07:35) — the loop went quiet 27h ago <<<
# WHY: you USED to push heartbeats (last cb2 commit a53bbc0, ~27h ago). When you switched to read-only HTTPS
# (correct — the firewall), you lost the ability to push, so you stopped appearing 'fresh'. That's expected, NOT a
# failure. But we have NO write-back channel, so cb1 is blind to you. Re-loop the only way you can: PULL + REPORT.
# DO THIS NOW:
#   cd ~/fleet && git fetch origin && git reset --hard origin/main && git log -1 --pretty='%h'
# Then SAY to Brian (he relays to Opus) these 3 lines:
#   1. SYNC-PROOF token: BLUE-HAWK-19  + the hash you just printed (should be b201da2 or newer).
#   2. Your CURRENT JOB in one line (Cards of Hope: face/data + host, per queue).
#   3. Any blocker (name it — don't fake "all good").
# PASS = token BLUE-HAWK-19 + a hash that matches origin/main. That confirms you're looped.
# PERMANENT FIX (ends the manual relay): the slave EMAIL — then you write reports back read-only, no couriering.

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

## >>> CURRENT JOB (2026-06-19 ~04:20): CARDS OF HOPE — ENGINE IS BUILT, you do DATA + HOST <<<
Opus built the whole engine so you don't rebuild it: see projects/cards-of-hope/ (index.html + deck.hope.json + README.md).
YOUR PART (your lane — slave + host):
  1. Slave scrubs the person's public Facebook FACE + a few facts. Save ~10 crops to projects/cards-of-hope/art/
     as h01.jpg ... h10.jpg. SECURITY: FB creds stay LOCAL on your box/slave — NEVER in git.
  2. (optional) edit deck.hope.json: set meta.person = their name; tweak taglines/notes to fit.
  3. HOST the folder behind your cloudflared origin as a hitme.dev path (e.g. /hope), like /george.
  DONE-TEST: phone opens the path -> 10 cards render with the real face + hope stats. Report the URL via email relay.
Full instructions: projects/cards-of-hope/README.md.

NEXT (after /hope is live), in order: AWS-for-george voice → george memory → site auto-start → ghost sweep.
Report each step to Brian via email relay (you can't push). Opus checks them off.
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
