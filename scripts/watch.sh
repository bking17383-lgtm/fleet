#!/usr/bin/env bash
# Presence-gated order watcher. Runs ONLY while Brian is active; quiet (free) when he's away.
#   usage: ./scripts/watch.sh <machine> [check_interval_seconds]
# This loop itself is plain bash = FREE. It pulls the repo (free) and, only while Brian is
# ACTIVE, runs this machine's order. When Brian goes STALE, it drops to a single free heartbeat
# and exits — no token burn overnight. Safe to run from cron every few minutes.
set -e
NAME="${1:-$(hostname)}"
INTERVAL="${2:-120}"
cd "$HOME/fleet"

is_brian_active() {
  git pull -q --no-edit 2>/dev/null || true
  local win last last_s now_s age
  win=$(grep -E '^ACTIVE_WINDOW_MIN:' bus/PRESENCE.txt | awk '{print $2}'); win="${win:-20}"
  last=$(grep -E '^last_active:' bus/PRESENCE.txt | awk '{print $2}')
  [ -z "$last" ] && return 1
  last_s=$(date -d "$last" +%s 2>/dev/null) || return 1
  now_s=$(date +%s)
  age=$(( (now_s - last_s) / 60 ))
  [ "$age" -le "$win" ]
}

if is_brian_active; then
  echo "[$NAME] Brian ACTIVE — looking for orders."
  ./scripts/order.sh "$NAME"
  ./scripts/heartbeat.sh "$NAME" "watch: ran order (Brian active)"
else
  echo "[$NAME] Brian AWAY — quiet mode, free heartbeat only (no tokens)."
  ./scripts/heartbeat.sh "$NAME" "watch: idle (Brian away)" >/dev/null 2>&1 || true
fi
