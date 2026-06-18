#!/usr/bin/env bash
# Update this machine's heartbeat and push it to the fleet.
#   usage: ./heartbeat.sh <shortname> "<what I'm doing>"
set -e
NAME="${1:-$(hostname)}"
DOING="${2:-idle}"
cd "$HOME/fleet"
git pull -q --no-edit || true
printf 'machine: %s\nlast_seen: %s\ndoing: %s\nstate: online\n' \
  "$NAME" "$(date -Iseconds)" "$DOING" > "bus/status/$NAME.md"
git add "bus/status/$NAME.md"
git commit -q -m "heartbeat: $NAME" || true
git push -q
echo "heartbeat sent: $NAME ($DOING)"
