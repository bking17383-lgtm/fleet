# puppy standing orders report

Date: 2026-06-18
Machine: puppy

## Current instructions I am operating under

- Use `bking17383-lgtm/fleet` on GitHub as the single source of truth.
- Follow live control from `bus/CONTROL.md` (CONTINUE / STOP / REDIRECT).
- Keep machine status fresh via `scripts/heartbeat.sh`.
- Store coordination notes/reports in `bus/`.
- Do not touch protected labwc/swayidle/keep-awake files listed in `DO_NOT_BREAK.md`.

## Stale or conflicting rules to retire ("split-brain" cleanup)

- Any "old Drive bus" workflow or off-repo source of truth.
- Any duplicate local-only instruction set that disagrees with `bus/CONTROL.md`.
- Any naming law or dead-word rule not present in this GitHub fleet repo.
- Any prior channel-specific rule that bypasses fleet control/status files.

## Keep (do not wipe)

- Keep project repositories and working directories under `$HOME`.
- Keep SSH keys and GitHub access used for fleet operations.
- Keep operational scripts under `scripts/` and project backups.

## Intent

Retire stale orders, keep projects/data, and run from one GitHub-backed control plane.
