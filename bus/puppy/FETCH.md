# PUPPY — FETCH

This is puppy's live order. When Brian says **fetch**, puppy does exactly what's below.
Always act on the current contents — never decide it's "unchanged."

Updated: 2026-06-18 02:50

## Do these in order

1. Pull the repo.
2. Run: `./scripts/clean-bar.sh`
   - This backs up your old bottom bar, then installs a clean one that shows only: puppy
   - No Drive, no lanes, no fake 3/3.
3. Reload / start a fresh chat so the new bar shows.
4. Beat heartbeat: `./scripts/heartbeat.sh puppy "cleaned bottom bar"`
