#!/usr/bin/env bash
# Working public URL when hitme.dev DNS missing · quick tunnel to :8770
set -euo pipefail
STAN="${HOME}/.stan"
CF="${STAN}/cloudflared"
PORT=8770
LOG="${STAN}/logs/hitme_quick_tunnel.log"
for D in /mnt/shared/GoogleDrive/MyDrive "$HOME/GoogleDrive/MyDrive"; do
  [[ -d "$D/fleet" ]] && DRIVE="$D" && break
done

mkdir -p "${STAN}/logs" "${DRIVE}/fleet/bus"

if ! curl -sf "http://127.0.0.1:${PORT}/health" >/dev/null 2>&1; then
  pkill -f hitme_who_server.py 2>/dev/null || true
  sleep 1
  nohup python3 "${STAN}/hitme_who_server.py" >>"${STAN}/logs/hitme_who.log" 2>&1 &
  sleep 2
fi

# Named tunnel (hitme.dev) — keep if running
if [[ -f "${STAN}/cloudflare.env" ]]; then
  # shellcheck source=/dev/null
  source "${STAN}/cloudflare.env"
  if [[ -n "${CLOUDFLARE_TUNNEL_TOKEN:-}" ]] && ! pgrep -f 'cloudflared tunnel run --token' >/dev/null; then
    nohup "$CF" tunnel run --token "$CLOUDFLARE_TUNNEL_TOKEN" >>"${STAN}/hitme_tunnel.log" 2>&1 &
    sleep 2
  fi
fi

# Quick tunnel — always gives a working HTTPS URL today
if ! pgrep -f "cloudflared tunnel --url http://127.0.0.1:${PORT}" >/dev/null; then
  pkill -f "cloudflared tunnel --url http://127.0.0.1:${PORT}" 2>/dev/null || true
  sleep 1
  : >"$LOG"
  nohup "$CF" tunnel --url "http://127.0.0.1:${PORT}" >>"$LOG" 2>&1 &
fi

URL=""
for _ in $(seq 1 25); do
  URL="$(grep -oE 'https://[a-z0-9-]+\.trycloudflare\.com' "$LOG" 2>/dev/null | tail -1 || true)"
  [[ -n "$URL" ]] && curl -sf "${URL}/goal" >/dev/null 2>&1 && break
  sleep 1
done

NOW="$(date -Iseconds)"
TS_IP="$(hostname -I 2>/dev/null | awk '{print $1}')"

if [[ -n "$URL" ]] && curl -sf "${URL}/goal" >/dev/null 2>&1; then
  PUBLIC_OK="$URL"
else
  PUBLIC_OK="(quick tunnel starting — retry in 10s)"
  URL="${URL:-}"
fi

cat >"${DRIVE}/fleet/HITME_LIVE_URL.txt" <<EOF
HITME LIVE URL — ${NOW}
from: Daddy on $(hostname)

USE THIS NOW (works from phone · puppy · anywhere):
  ${PUBLIC_OK}/goal
  ${PUBLIC_OK}/checkin
  ${PUBLIC_OK}/wake
  ${PUBLIC_OK}/puppy

Local same keyboard:
  http://127.0.0.1:${PORT}/wake

Tailscale (if on tailnet):
  http://${TS_IP}:${PORT}/wake

hitme.dev: DNS not wired yet (no CNAME) — tunnel UP but public 530
Fix permanent: paste API token in ~/.stan/cloudflare_api.env → bash ~/.stan/hitme_cf_provision.sh
EOF

cat >"${DRIVE}/fleet/bus/WORKING_URL.txt" <<EOF
WORKING URL — ${NOW}
${PUBLIC_OK}/goal
EOF

echo "LIVE: ${PUBLIC_OK}/goal"
echo "→ ${DRIVE}/fleet/HITME_LIVE_URL.txt"
