#!/usr/bin/env bash
# One command: Video Slicer host + tunnel ($0). Named if token set; else quick tunnel for dev.
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"
DRIVE="${HOME}/GoogleDrive/MyDrive"
[[ -d "/mnt/shared/GoogleDrive/MyDrive" ]] && DRIVE="/mnt/shared/GoogleDrive/MyDrive"
ENV_FILE="${HOME}/.stan/groq.env"
CF="${CLOUDFLARED:-/tmp/cloudflared}"
PORT="${SLICER_PORT:-5000}"
LOG_CF="/tmp/cf_slicer.log"
URL_FILE="${DRIVE}/SLICER_PHONE_URL.txt"

[[ -f "$ENV_FILE" ]] && set -a && source "$ENV_FILE" && set +a

bash "$DIR/start_slicer_host.sh"

if [[ -n "${CLOUDFLARE_TUNNEL_TOKEN:-}" ]]; then
  bash "$DIR/start_slicer_tunnel_named.sh"
  echo "Named tunnel — set fixed URL in $URL_FILE from Cloudflare dashboard"
  exit 0
fi

# Dev fallback: quick tunnel (URL rotates on restart — not for paying customers)
if [[ ! -x "$CF" ]]; then
  curl -sL -o "$CF" https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64
  chmod +x "$CF"
fi
pkill -f "cloudflared tunnel" 2>/dev/null || true
sleep 1
rm -f "$LOG_CF"
nohup "$CF" tunnel --protocol http2 --url "http://127.0.0.1:${PORT}" >>"$LOG_CF" 2>&1 &
echo $! >/tmp/cf_slicer.pid

PUBLIC=""
for _ in $(seq 1 30); do
  sleep 2
  PUBLIC="$(grep -oE 'https://[a-z0-9-]+\.trycloudflare\.com' "$LOG_CF" 2>/dev/null | head -1 || true)"
  [[ -n "$PUBLIC" ]] && break
done

if [[ -n "$PUBLIC" && -d "$DRIVE" ]]; then
  printf '%s\n' "$PUBLIC" >"$URL_FILE"
  cp -f "$URL_FILE" "$DRIVE/lester/SLICER_PHONE_URL.txt" 2>/dev/null || true
  {
    echo ""
    echo "# Slicer $(date -Iseconds) hostname=$(hostname)"
    echo "status: RUNNING"
    echo "url: $PUBLIC"
    echo "mode: quick_tunnel_dev"
    echo "note: Set CLOUDFLARE_TUNNEL_TOKEN for fixed \$0 URL on puppy"
  } >>"$DRIVE/puppy_outbox.txt"
  echo "Phone URL (dev): $PUBLIC"
  echo "Written: $URL_FILE"
else
  echo "WARN: tunnel URL not ready — tail $LOG_CF"
  exit 1
fi
