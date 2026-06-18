#!/usr/bin/env bash
# Named Cloudflare tunnel → stable HTTPS URL ($0/mo). Requires CLOUDFLARE_TUNNEL_TOKEN.
set -euo pipefail
PORT="${SLICER_PORT:-5000}"
CF="${CLOUDFLARED:-/tmp/cloudflared}"
LOG="/tmp/cf_slicer_named.log"
PIDFILE="/tmp/cf_slicer_named.pid"
ENV_FILE="${HOME}/.stan/groq.env"

[[ -f "$ENV_FILE" ]] && set -a && source "$ENV_FILE" && set +a

if [[ -z "${CLOUDFLARE_TUNNEL_TOKEN:-}" ]]; then
  echo "ERROR: set CLOUDFLARE_TUNNEL_TOKEN (Cloudflare Zero Trust → Tunnels → token)"
  echo "See MyDrive/lester/SLICER_ZERO_COST.md"
  exit 1
fi

if [[ ! -x "$CF" ]]; then
  curl -sL -o "$CF" https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64
  chmod +x "$CF"
fi

pkill -f "cloudflared tunnel" 2>/dev/null || true
sleep 1
rm -f "$LOG"

# Named tunnel — URL is fixed in Cloudflare dashboard (not random trycloudflare)
nohup "$CF" tunnel run --token "$CLOUDFLARE_TUNNEL_TOKEN" >>"$LOG" 2>&1 &
echo $! >"$PIDFILE"
sleep 3
echo "Named tunnel started pid=$(cat "$PIDFILE")"
echo "Fixed URL is in Cloudflare dashboard → Public Hostname (write to SLICER_PHONE_URL.txt)"
echo "Local backend must be up: bash start_slicer_host.sh (:${PORT})"
tail -5 "$LOG" 2>/dev/null || true
