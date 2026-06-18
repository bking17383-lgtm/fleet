#!/usr/bin/env bash
# Run this ON puppy64 (not penguin). Installs baseball app and starts on :8002.
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"
PORT=8002
LOG="$DIR/baseball_server.log"
PIDFILE="$DIR/baseball_server.pid"

python3 -c "import flask" 2>/dev/null || python3 -m pip install flask -q

if [[ -f "$PIDFILE" ]] && kill -0 "$(cat "$PIDFILE")" 2>/dev/null; then
  echo "Already running (pid $(cat "$PIDFILE"))."
else
  cd "$DIR"
  nohup python3 app_baseball.py >>"$LOG" 2>&1 &
  echo $! >"$PIDFILE"
  sleep 1
fi

PUPPY_IP="${PUPPY_IP:-192.168.1.4}"
echo "Baseball app: http://${PUPPY_IP}:${PORT}"
echo "Also try: http://puppy:${PORT}  (if hostname resolves on LAN)"
python3 -m pip install qrcode pillow -q 2>/dev/null || true
QR_URL="http://${PUPPY_IP}:${PORT}"
if [[ -f "$HOME/.stan/make_qr.py" ]]; then
  python3 "$HOME/.stan/make_qr.py" -o "$DIR/baseball_qr_puppy.png" --url "$QR_URL" || true
elif [[ -f "$DIR/../../make_qr.py" ]]; then
  python3 "$DIR/../../make_qr.py" -o "$DIR/baseball_qr_puppy.png" --url "$QR_URL" || true
fi
python3 "$HOME/.stan/stan_env.py" note-from puppy "Baseball app running on puppy:${PORT} for phone access." "$DIR" 2>/dev/null || true
