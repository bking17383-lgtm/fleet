#!/usr/bin/env bash
# Keep mesh radio alive on CB2 while Brian on drive
LOG="${HOME}/.stan/keep_awake.log"
while true; do
  echo "$(date -Iseconds) ping" >>"$LOG"
  pgrep -f mesh_radio.py >/dev/null || "${HOME}/.stan/start_mesh_radio.sh" >>"$LOG" 2>&1
  sleep 120
done
