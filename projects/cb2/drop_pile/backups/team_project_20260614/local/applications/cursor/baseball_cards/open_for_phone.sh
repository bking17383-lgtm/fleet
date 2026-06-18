#!/usr/bin/env bash
# Phone access: public URL + QR on Drive. No puppy, no Tailscale, no typing.
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"
PORT=8002
LOG="/tmp/cf_tunnel.log"
PIDFILE="$DIR/phone_tunnel.pid"
URL_FILE="$DIR/PHONE_URL.txt"
CF="${CF:-/tmp/cloudflared}"
DRIVE="/mnt/shared/GoogleDrive/MyDrive"

# Server
if ! curl -sf "http://127.0.0.1:${PORT}/api/health" >/dev/null 2>&1; then
  cd "$DIR"
  nohup python3 app_baseball.py >>baseball_server.log 2>&1 &
  echo $! > baseball_server.pid
  sleep 2
fi

# Cloudflared binary
if [[ ! -x "$CF" ]]; then
  curl -sL -o "$CF" https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64
  chmod +x "$CF"
fi

# Stop old tunnels
if [[ -f "$PIDFILE" ]]; then
  kill "$(cat "$PIDFILE")" 2>/dev/null || true
fi
pkill -f "cloudflared tunnel --url http://127.0.0.1:${PORT}" 2>/dev/null || true
pkill -f "ssh.*serveo.*${PORT}" 2>/dev/null || true
pkill -f "ssh.*pinggy.*${PORT}" 2>/dev/null || true
sleep 1

rm -f "$LOG"
nohup "$CF" tunnel --url "http://127.0.0.1:${PORT}" >>"$LOG" 2>&1 &
echo $! > "$PIDFILE"

PUBLIC_URL=""
for _ in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 25 30; do
  sleep 2
  PUBLIC_URL="$(grep -oE 'https://[a-z0-9-]+\.trycloudflare\.com' "$LOG" 2>/dev/null | head -1 || true)"
  [[ -n "$PUBLIC_URL" ]] && break
done

if [[ -z "$PUBLIC_URL" ]]; then
  echo "Tunnel failed. Last log lines:"
  tail -10 "$LOG" 2>/dev/null || true
  exit 1
fi

echo "$PUBLIC_URL" > "$URL_FILE"
python3 "$HOME/.stan/make_qr.py" -o "$DIR/baseball_qr_phone.png" --url "$PUBLIC_URL"

if [[ -d "$DRIVE" ]]; then
  cp "$DIR/baseball_qr_phone.png" "$DRIVE/baseball_qr_phone.png"
  cp "$DIR/baseball_qr_phone.png" "$DRIVE/baseball_qr.png"
  printf '%s\n' "$PUBLIC_URL" > "$DRIVE/PHONE_URL.txt"
  cat > "$DRIVE/OPEN_ON_PHONE.txt" <<EOF
PHONE LINK (copy into Chrome on your phone):

${PUBLIC_URL}

Or scan baseball_qr_phone.png in this Drive folder.

Do NOT use the QR page on the Chromebook (/qr) — it was broken before.
This link is the correct one. Keep Chromebook awake while testing.
EOF
fi

echo "READY: $PUBLIC_URL"
echo "QR: $DRIVE/baseball_qr_phone.png"
