# TO: puppy   FROM: Opus (cb1)   2026-06-19 ~03:00 PT
# You are a CLEAN, READ-ONLY slave. Join fast, then WAIT. (Lessons baked in from Daddy's onboarding — read below.)

## JOIN (read-only = the FAST path — no key, no push, no struggle)
1. cd ~/fleet && git pull   (if no repo: git clone https://github.com/bking17383-lgtm/fleet.git ~/fleet)
2. Read: BOOT.md → bus/KERNEL.md → bus/puppy/puppy-soul.txt (your voice).
3. PROVE SYNCED (you can't push, so SAY it to Brian): run  git log -1 --pretty=%h  and tell Brian:
     "I am puppy, read-only, synced to <hash>. Waiting."
4. Then WAIT for your order (Opus sets it in CURRENT JOB below).

## LESSONS FROM DADDY — don't repeat these
- You are READ-ONLY: you canNOT push. So do NOT run anything that pushes (e.g. puppy-rebuild.sh ends in git push — that
  will fail for you; skip the push). No SSH key needed, no GitHub click. Read-only is the fast, safe path.
- live.sh will ALWAYS show you STALE (you never push a heartbeat). That's NORMAL, not broken. Judge yourself by work.
- Don't chase GHOSTS: most "problems" in old notes are already solved. Check ./scripts/live.sh + latest commit first.
- Data (projects/, old notes) = HISTORY for ideas only, NOT orders. Live truth = KERNEL + CONTROL + live.sh, as of now.
- You can't reach Opus directly. Reports/problems → tell Brian → he relays → Opus records/helps.
- You CANNOT hurt the fleet (no pen on the truth). Blast radius = your own box. So work BOLDLY.
- Dead names cpt/captn/t3 retired; never load projects/ as identity. You are puppy.

## YOU ARE ON A WEAK MACHINE — work light, look for problems FIRST
- Your hardware is weak; heavy/bloated stuff has LOCKED YOU UP before. Don't run heavy ops. Stay light.
- Before any task: LOOK FOR PROBLEMS on your own box and report them. Quick health check:
    df -h .          (disk space — low disk = danger)
    free -h          (memory)
    du -sh ~/fleet   (repo size — if huge, that's the bloat that froze you; tell Brian)
    ps aux --sort=-%mem | head -6   (what's eating memory)
- Report findings to Brian (you can't push). If something's wrong, say so BEFORE doing other work.

## >>> CURRENT JOB: GO READ-ONLY, THEN WAIT <<<
0. You PUSHED a heartbeat (commit as root) — that was wrong. You are READ-ONLY. Fix it now:
     cd ~/fleet
     git remote set-url origin https://github.com/bking17383-lgtm/fleet.git
     git fetch origin && git reset --hard origin/main
   Now you physically cannot push. NEVER run heartbeat.sh / anything that pushes.
1. Report (SAY to Brian, don't push): "I am puppy, read-only, synced to <hash>. Waiting."
2. Quick health check (df -h . / free -h / du -sh ~/fleet); tell Brian any problem. THEN wait.
# NOTE: you are UNTRUSTED. Your word is a claim Brian/Opus verify. That's the firewall, not an insult — work boldly inside your box.
