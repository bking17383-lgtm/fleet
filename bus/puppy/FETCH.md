# PUPPY — FETCH

This is puppy's live order. When Brian says **fetch**, puppy does exactly what's below.
Always act on the current contents — never decide it's "unchanged."

Updated: 2026-06-18 02:33

## Do these in order

1. Pull the repo.
2. Run: `./scripts/order.sh puppy`
3. Start a fresh chat so the new rules load.
4. Write your current rules into `bus/puppy/PROOF.md` and push (so Brian + auditor can verify the clean brain loaded).
5. Beat heartbeat: `./scripts/heartbeat.sh puppy "fetched and applied"`
