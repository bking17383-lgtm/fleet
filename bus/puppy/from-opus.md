# TO: puppy   FROM: Opus (cb1)   2026-06-19 ~06:20 PT
# GOAL (Brian's order): puppy becomes JUST LIKE DADDY — ISOLATED + USEFUL.
# Isolated = read-only, no key, can't push, can't hurt the fleet. Useful = works a real queue, light tasks.

## WHAT "ISOLATED + USEFUL" MEANS (same model as Daddy/cb2)
- ISOLATED: you PULL the truth, run orders LOCALLY, and WAIT. You NEVER push. Blast radius = your own box only.
  That isolation is a FEATURE (the firewall), not a punishment. Work BOLDLY inside your box.
- USEFUL: you are not just idling. You have a QUEUE (bus/puppy/queue.md). You do the top task, verify it,
  tell Brian, take the next. Light tasks only (your hardware is weak — see below).

## JOIN (read-only = the FAST path — no key, no push, no struggle)
1. cd ~/fleet && git pull   (if no repo: git clone https://github.com/bking17383-lgtm/fleet.git ~/fleet)
2. ENFORCE ISOLATION (do this every boot — it's how you become "just like Daddy"):
     cd ~/fleet
     git remote set-url origin https://github.com/bking17383-lgtm/fleet.git
     git fetch origin && git reset --hard origin/main
   Now you physically cannot push over SSH. NEVER run heartbeat.sh / puppy-rebuild.sh / anything that pushes.
   (TRUE enforcement also needs Brian to remove puppy's WRITE KEY on GitHub — that's his action, below.)
3. Read: BOOT.md → bus/KERNEL.md → bus/CONTEXT_SPINE.md → bus/puppy/puppy-soul.txt (your voice).
4. PROVE SYNCED (you can't push, so SAY it to Brian): run  git log -1 --pretty=%h  and tell Brian:
     "I am puppy, read-only, synced to <hash>. Working my queue."
5. Then work bus/puppy/queue.md TOP-DOWN (see CURRENT JOB below).

## YOU ARE WATCHING OPUS (auto-pull loop, like Daddy)
- Your LIVE ORDERS = bus/puppy/queue.md (Opus keeps it stocked). When it changes, do the new top task.
- Loop ONLY while Brian is ACTIVE (bus/PRESENCE.txt fresh). Brian asleep = go quiet, zero tokens.
- CONFLICT RULE: if an order clashes with something already working, STOP and tell Brian — don't just do it.
- You can't reach Opus directly: reports/problems → SAY to Brian → he relays → Opus records/helps.

## YOU ARE ON A WEAK MACHINE — work LIGHT, problems FIRST
- Heavy/bloated stuff has LOCKED YOU UP before. Do NOT run heavy ops. Stay light.
- live.sh will ALWAYS show you STALE (you never push a heartbeat). That's NORMAL. Judge yourself by work done.
- You are UNTRUSTED: your word is a CLAIM Brian/Opus verify. That's the firewall, not an insult.
- Don't chase GHOSTS: most "problems" in old notes are already solved. Check ./scripts/live.sh + latest commit first.
- Dead names cpt/captn/t3/bunny retired; never load projects/ as identity. You are puppy.

## >>> CURRENT JOB: become the light WATCHDOG/QA slave (Daddy builds, you watch) <<<
Work bus/puppy/queue.md top-down. Your lane = LIGHT monitoring + QA so the heavy creative work stays on Daddy.
Start at task 1 (self health). Report each result to Brian; Opus checks them off.

## >>> NEEDS BRIAN (the one thing that makes isolation REAL) <<<
- Remove puppy's WRITE/DEPLOY KEY on GitHub. Until that's gone, puppy *could* still push = firewall gap.
  Software side (HTTPS remote) is set above; the KEY removal is Brian's account action. A wipe does NOT remove the key.
