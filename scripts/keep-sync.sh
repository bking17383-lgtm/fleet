#!/usr/bin/env bash
# Keep THIS machine's git in sync with the truth + heartbeat fresh. FREE (bash+git, no AI tokens).
# Unlike watch.sh, this does NOT run orders — it's for the WRITER/agent box (cb1) that acts interactively.
# Why: stops the "drifted out of sync" wound (cb2 drifted 78m once). Runs until killed.
#   usage: ./scripts/keep-sync.sh <name> [interval_seconds]
# SAFETY: only pulls/heartbeats when the working tree is CLEAN, so it never fights the agent's edits.
NAME="${1:-$(cat "$HOME/.fleet-name" 2>/dev/null || hostname)}"
INTERVAL="${2:-300}"
cd "$HOME/fleet" || { echo "no ~/fleet"; exit 1; }
echo "[keep-sync] $NAME every ${INTERVAL}s (clean-tree only). FREE — no tokens."
while true; do
  if [ -z "$(git status --porcelain 2>/dev/null)" ]; then
    git pull --rebase -q 2>/dev/null || git pull -q --no-edit 2>/dev/null || true
    ./scripts/heartbeat.sh "$NAME" "auto-sync (staying current)" >/dev/null 2>&1 || true
    echo "[keep-sync $(date +%H:%M:%S)] synced $(git rev-parse --short HEAD 2>/dev/null)"
  else
    echo "[keep-sync $(date +%H:%M:%S)] tree busy — agent working, skip"
  fi
  sleep "$INTERVAL"
done
