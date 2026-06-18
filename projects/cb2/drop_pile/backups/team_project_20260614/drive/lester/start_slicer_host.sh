#!/usr/bin/env bash
# Video Slicer — Flask on :5000 (puppy or penguin). $0/mo.
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"
ENV_FILE="${HOME}/.stan/groq.env"
PIDFILE="/tmp/slicer_server.pid"
LOG="/tmp/slicer_server.log"
PORT="${SLICER_PORT:-5000}"

if [[ -f "$ENV_FILE" ]]; then
  set -a
  # shellcheck disable=SC1090
  source "$ENV_FILE"
  set +a
fi

if [[ -f "$PIDFILE" ]]; then
  old="$(cat "$PIDFILE" 2>/dev/null || true)"
  if [[ -n "$old" ]] && kill -0 "$old" 2>/dev/null; then
    echo "Slicer already running pid=$old"
    exit 0
  fi
fi

fuser -k "${PORT}/tcp" 2>/dev/null || true
sleep 1
cd "$DIR"
nohup python3 app_mobile.py >>"$LOG" 2>&1 &
echo $! >"$PIDFILE"
sleep 2
if curl -sf "http://127.0.0.1:${PORT}/api/status" >/dev/null; then
  echo "OK slicer :${PORT} pid=$(cat "$PIDFILE")"
else
  echo "WARN: slicer may still be starting — tail $LOG"
  exit 1
fi
