# fleet — single source of truth

This repo is the ONE place that is real. Every machine pulls from here and pushes here.
If it isn't in this repo, it isn't true. No mirrors, no Drive bus, no Gemini slaves.

## Layout
- `bus/GOALS.md`   — what the fleet is working toward (Brian's will). Edit to change direction.
- `bus/CONTROL.md` — live commands to running agents (CONTINUE / STOP / REDIRECT).
- `bus/status/`    — one heartbeat file per machine (who's alive, what they're doing).
- `projects/`      — backups of the real work.

## Rules
- Pull before you write. Push after. One writer at a time per file.
- Secrets NEVER go in this repo. Keys stay on each machine.
