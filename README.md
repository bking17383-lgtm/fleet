# fleet — single source of truth

This repo is the ONE place that is real. Every machine pulls from here and pushes here.
If it isn't in this repo, it isn't true. No mirrors, no Drive bus, no slaves.

## Start here
- **BOOT.md** — read this FIRST. It bootstraps any fresh agent from zero.

## Layout
- `bus/KERNEL.md`        — the prime directive (read first, every session)
- `bus/CONTEXT_SPINE.md` — the world: env, projects, goals, decisions
- `bus/GOALS.md`         — what the fleet is working toward (Brian's will)
- `bus/CONTROL.md`       — live commands to agents (CONTINUE / STOP / REDIRECT)
- `bus/orders.txt`       — per-machine job (scan / preserve / fix / wait)
- `bus/PRESENCE.txt`     — is Brian active? (gates the order-looking loop)
- `bus/status/`          — one heartbeat file per machine
- `bus/<name>/<name>-soul.txt` — each machine's voice/personality (e.g. bus/cb2/cb2-soul.txt)
- `projects/`            — backups of the real work (DATA, not identity)
- `scripts/`             — the plumbing (get-keys, heartbeat, live, order, ...)

## Rules
- Pull before you write. Push after. One writer at a time per file.
- Only the auditor (cb1) writes the truth; other machines are read-only readers.
- Secrets/keys NEVER go in this repo. Keys stay on each machine.
