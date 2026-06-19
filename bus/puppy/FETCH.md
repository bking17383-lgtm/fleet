# PUPPY — FETCH

This is puppy's live order. When Brian says **fetch**, puppy does exactly what's below.
Always act on the current contents — never decide it's "unchanged."

Updated: 2026-06-19 03:51

## YOU ARE READ-ONLY. YOU DO NOT PUSH. (enforced)
First, make your git physically read-only so you CANNOT push (no key, no infect):
  cd ~/fleet
  git remote set-url origin https://github.com/bking17383-lgtm/fleet.git
  git fetch origin && git reset --hard origin/main
Then you can ONLY pull. NEVER run heartbeat.sh or anything that pushes — it is not your job.

## Do these in order (CLEAN, READ-ONLY)
1. Pull the repo (HTTPS, above).
2. Read: BOOT.md → bus/KERNEL.md → bus/puppy/puppy-soul.txt (your voice).
3. PROVE SYNCED by SAYING it to Brian (you can't push): run  git log -1 --pretty=%h
   and tell Brian: "I am puppy, read-only, synced to <hash>. Waiting."
4. WAIT for Brian's order. Do NOT push. Do NOT heartbeat.
