#!/usr/bin/env bash
# Start Daddy/Captain slave — one command on CB2/penguin
set -euo pipefail
D="${HOME}/GoogleDrive/MyDrive"
[[ -d /mnt/shared/GoogleDrive/MyDrive/fleet ]] && D="/mnt/shared/GoogleDrive/MyDrive"
PY="${D}/fleet/bootstrap/box_slave_loop.py"
LOG="${HOME}/.stan/logs/cb2_slave.log"
PID="${HOME}/.stan/cb2_slave.pid"
mkdir -p "${HOME}/.stan/logs"
echo f770e0dc > "${HOME}/.stan/slave.key"
chmod 600 "${HOME}/.stan/slave.key"
if [[ -f "$PID" ]] && kill -0 "$(cat "$PID")" 2>/dev/null; then exit 0; fi
nohup python3 "$PY" daddy >>"$LOG" 2>&1 &
echo $! >"$PID"
