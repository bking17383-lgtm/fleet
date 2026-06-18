# Puppy known orders for auditor

Date: 2026-06-18
Machine: puppy
Purpose: single list of currently known active orders and guardrails.

## GitHub fleet orders (source of truth)

- Run `./scripts/order.sh <your-name>` after pulling latest repo.
- Follow only the task assigned in `bus/orders.txt`.
- `puppy` assignment is `preserve`.
- `preserve` means copy projects into repo; do not move or delete machine sources.
- After acting, run `./scripts/heartbeat.sh <name> "what I did"`.
- Resume and wait for next order.

## Local trust orders in `~/.cursor/rules/puppy-agent.mdc`

- Preserve projects. Do not move or delete projects unless explicitly ordered.
- Trust GitHub orders as live source of truth.
- On direct reboot instruction (`reboot`, `puppy reboot`, `restart the machine`, `restart puppy`), run:
  - `/root/puppy-server/bin/puppy-reboot.sh`
  - `/root/puppy-server/bin/puppy-clean-reboot.sh` (wipe + no agents)
- Never edit/delete paths listed in `/mnt/home/lester6/DO_NOT_BREAK.md`.

## Conflict handling rule

- If any local/old instruction conflicts with GitHub fleet orders, GitHub orders win.
