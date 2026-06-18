#!/usr/bin/env bash
# Start Bunny/puppy slave — one command on Bunny box
set -euo pipefail
D="${HOME}/GoogleDrive/MyDrive"
[[ -d /mnt/shared/GoogleDrive/MyDrive/fleet ]] && D="/mnt/shared/GoogleDrive/MyDrive"
PY="${D}/fleet/bootstrap/box_slave_loop.py"
LOG="${HOME}/bbuny_loop.log"
PID="${HOME}/.bunny_slave.pid"
if [[ -f "$PID" ]] && kill -0 "$(cat "$PID")" 2>/dev/null; then exit 0; fi
if [[ -f "${D}/lester/bbunny_loop.sh" ]]; then
  nohup bash "${D}/lester/bbunny_loop.sh" >>"$LOG" 2>&1 &
  echo $! >"$PID"
  exit 0
fi
nohup python3 "$PY" bunny >>"$LOG" 2>&1 &
echo $! >"$PID"
