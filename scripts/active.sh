#!/usr/bin/env bash
# Stamp "Brian is active right now" into the fleet. Run by the machine Brian is working on.
#   usage: ./scripts/active.sh <machine>     (e.g. ./scripts/active.sh cb1)
# While this stays FRESH (see ACTIVE_WINDOW_MIN in bus/PRESENCE.txt), other machines
# are allowed to run their look-for-orders loop. When it goes STALE, they go quiet (free heartbeat only).
set -e
NAME="${1:-$(hostname)}"
WIN="${2:-20}"   # active window in minutes
cd "$HOME/fleet"
git pull -q --no-edit 2>/dev/null || true
printf '# BRIAN PRESENCE — the gate for AI order-looking.\n# FRESH = last_active within ACTIVE_WINDOW_MIN. Otherwise machines drop to free heartbeat (zero tokens).\nACTIVE_WINDOW_MIN: %s\nlast_active: %s\nseen_by: %s\n' \
  "$WIN" "$(date -Iseconds)" "$NAME" > bus/PRESENCE.txt
git add bus/PRESENCE.txt
git commit -q -m "presence: Brian active (seen by $NAME)" || true
git push -q 2>/dev/null || true
echo "presence stamped: Brian active, seen by $NAME (window ${WIN}m)"
