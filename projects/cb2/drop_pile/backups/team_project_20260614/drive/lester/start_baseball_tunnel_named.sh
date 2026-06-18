#!/usr/bin/env bash
# Named Cloudflare tunnel → baseball :8002 on puppy64 ($0/mo stable HTTPS for strangers)
set -euo pipefail
CF="${CLOUDFLARED:-/tmp/cloudflared}"
LOG="${HOME}/baseball_tunnel.log"
TOKEN="${CLOUDFLARE_TUNNEL_TOKEN:-}"

if [[ -z "$TOKEN" ]]; then
  [[ -f "${HOME}/.stan/cloudflare.env" ]] && source "${HOME}/.stan/cloudflare.env"
  TOKEN="${CLOUDFLARE_TUNNEL_TOKEN:-}"
fi
if [[ -z "$TOKEN" ]]; then
  echo "ERROR: set CLOUDFLARE_TUNNEL_TOKEN (Zero Trust → Tunnels → token)"
  echo "Public hostname in dashboard must point to http://localhost:8002"
  exit 1
fi

if [[ ! -x "$CF" ]]; then
  curl -sL -o "$CF" https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64
  chmod +x "$CF"
fi

pkill -f "cloudflared tunnel" 2>/dev/null || true
nohup "$CF" tunnel run --token "$TOKEN" >>"$LOG" 2>&1 &
echo "Tunnel starting — fixed URL is in Cloudflare dashboard (not random trycloudflare)"
echo "Ensure app_baseball.py is on :8002 first: bash START_BASEBALL_ON_PUPPY.sh or commercial install"