#!/usr/bin/env bash
# Start Baseball Card app and print URLs for each device type.
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"
PORT=8002
LOG="$DIR/baseball_server.log"
PIDFILE="$DIR/baseball_server.pid"

phone_ip() {
  ip -4 -o addr show eth0 2>/dev/null | awk '{print $4}' | cut -d/ -f1 | head -1
}

if [[ -f "$PIDFILE" ]] && kill -0 "$(cat "$PIDFILE")" 2>/dev/null; then
  echo "Server already running (pid $(cat "$PIDFILE"))."
else
  cd "$DIR"
  nohup python3 app_baseball.py >>"$LOG" 2>&1 &
  echo $! >"$PIDFILE"
  sleep 1
  echo "Started server (pid $(cat "$PIDFILE"))."
fi

IP="$(phone_ip || true)"
echo
echo "=== Baseball Card Valuation ==="
echo "On THIS machine (Chromebook Linux):  http://127.0.0.1:${PORT}"
if [[ -n "${IP:-}" ]]; then
  echo "On phone (Tailscale on, same account): http://${IP}:${PORT}"
  echo "  Scan QR: $DIR/baseball_qr.png"
fi
echo
echo "PHONE: do NOT use localhost — that means the phone itself."
echo
echo "Same WiFi (no Tailscale):"
echo "  1. Chromebook Settings → Developers → Linux → Port forwarding"
echo "  2. Add TCP port ${PORT}"
echo "  3. Settings → Network → Wi-Fi → your network → copy IP address"
echo "  4. On phone: http://<chromebook-wifi-ip>:${PORT}"
echo
echo "Puppy64 host: run deploy_to_puppy64.sh from puppy64 or when SSH works."
echo "Log: $LOG"
