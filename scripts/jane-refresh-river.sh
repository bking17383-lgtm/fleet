#!/usr/bin/env bash
# Pull Jane river into local Jane context. FREE — bash+git, no AI tokens.
# Matches jane-refresh interval (180s). Clean-tree only (never fight edits).
#   ./scripts/jane-refresh-river.sh [interval_seconds]
# If ~/jane exists, copies HEAD into jane-context.txt + live-context.txt.
set -e
ROOT="${FLEET_ROOT:-$HOME/fleet}"
if [ ! -d "$ROOT/.git" ]; then
  ROOT="$(cd "$(dirname "$0")/.." && pwd)"
fi
INTERVAL="${1:-180}"
cd "$ROOT"
echo "[jane-river] refresh every ${INTERVAL}s from $ROOT (clean-tree only). FREE — no tokens."
while true; do
  if [ -z "$(git status --porcelain 2>/dev/null)" ]; then
    git pull --rebase -q 2>/dev/null || git pull -q --no-edit 2>/dev/null || true
    if [ -f bus/jane/river/HEAD.md ] && [ -d "$HOME/jane" ]; then
      cp -f bus/jane/river/HEAD.md "$HOME/jane/jane-context.txt"
      cp -f bus/jane/river/HEAD.md "$HOME/jane/live-context.txt"
    fi
    echo "[jane-river $(date +%H:%M:%S)] head $(git rev-parse --short HEAD 2>/dev/null) $(grep '^stamp:' bus/jane/river/HEAD.md 2>/dev/null | head -1)"
  else
    echo "[jane-river $(date +%H:%M:%S)] tree busy — skip"
  fi
  sleep "$INTERVAL"
done
