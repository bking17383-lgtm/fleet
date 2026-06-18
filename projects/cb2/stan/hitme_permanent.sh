#!/usr/bin/env bash
# hitme.dev PERMANENT — named tunnel only · no trycloudflare
set -euo pipefail
STAN="${HOME}/.stan"
CF="${STAN}/cloudflared"
CFG="${HOME}/.cloudflared/config.yml"
CRED="${HOME}/.cloudflared/11431ecb-5cbd-40a5-b635-cec2aff9de03.json"
ENV="${STAN}/cloudflare.env"
PORT=8770
TUNNEL_NAME="cb2-daddy"
for DRIVE in /mnt/shared/GoogleDrive/MyDrive "$HOME/GoogleDrive/MyDrive"; do
  [[ -d "$DRIVE/fleet" ]] && break
done
LOG="${STAN}/logs/hitme_permanent.log"

log() { echo "$(date -Iseconds) $*" | tee -a "$LOG"; }

mkdir -p "${STAN}/logs" "${DRIVE}/fleet"

# Kill ALL quick / temp tunnels
pkill -f 'cloudflared tunnel --config /tmp/cf-empty.yml' 2>/dev/null || true
pkill -f 'cloudflared tunnel --url http://127.0.0.1:' 2>/dev/null || true
rm -f "${STAN}/url_keeper_tunnel.pid" 2>/dev/null || true
log "quick tunnels killed"

# Fleet server
if ! curl -sf "http://127.0.0.1:${PORT}/health" >/dev/null 2>&1; then
  pkill -f hitme_who_server.py 2>/dev/null || true
  sleep 1
  nohup python3 "${STAN}/hitme_who_server.py" >>"${STAN}/logs/hitme_who.log" 2>&1 &
  sleep 2
fi

# Named tunnel — prefer config.yml ingress (8770 landing)
if [[ -f "$CFG" && -f "$CRED" ]]; then
  n="$(pgrep -f 'cloudflared tunnel.*run' 2>/dev/null | wc -l | tr -d ' ')"
  if [[ "${n:-0}" != "1" ]]; then
    pkill -f 'cloudflared tunnel' 2>/dev/null || true
    sleep 2
    nohup "$CF" tunnel --config "$CFG" run >>"${STAN}/logs/hitme_tunnel.log" 2>&1 &
    sleep 3
    log "named tunnel started (config.yml)"
  fi
elif [[ -f "$ENV" ]]; then
  # shellcheck source=/dev/null
  source "$ENV"
  if [[ -n "${CLOUDFLARE_TUNNEL_TOKEN:-}" ]]; then
    n="$(pgrep -f 'cloudflared tunnel run --token' 2>/dev/null | wc -l | tr -d ' ')"
    if [[ "${n:-0}" != "1" ]]; then
      pkill -f 'cloudflared tunnel' 2>/dev/null || true
      sleep 2
      nohup "$CF" tunnel run --token "$CLOUDFLARE_TUNNEL_TOKEN" >>"${STAN}/logs/hitme_tunnel.log" 2>&1 &
      sleep 3
      log "named tunnel started (token)"
    fi
  fi
fi

# DNS route if origin cert exists (one-time login)
if [[ -f "${HOME}/.cloudflared/cert.pem" ]]; then
  for h in hitme.dev who.hitme.dev george.hitme.dev fleet.hitme.dev; do
    if "$CF" tunnel --config "$CFG" route dns -f "$TUNNEL_NAME" "$h" >>"$LOG" 2>&1; then
      log "dns route OK $h"
    fi
  done
fi

# API provision if token has zone+tunnel perms
if [[ -f "${STAN}/cloudflare_api.env" ]]; then
  bash "${STAN}/hitme_cf_provision.sh" >>"$LOG" 2>&1 || log "API provision failed — see log"
fi

# Status
DNS="NO"
python3 -c "import socket; socket.gethostbyname('hitme.dev')" 2>/dev/null && DNS="YES" || true
PUBLIC="000"
if [[ "$DNS" == "YES" ]]; then
  code="$(curl -s -o /dev/null -w '%{http_code}' --connect-timeout 8 https://hitme.dev/health 2>/dev/null || echo 000)"
  PUBLIC="$code"
fi
TUN="$(pgrep -f 'cloudflared tunnel.*run' >/dev/null && echo UP || echo DOWN)"
NOW="$(date -Iseconds)"

cat >"${DRIVE}/fleet/LIVE_URL.txt" <<EOF
hitme.dev ONLY — ${NOW}
tunnel=${TUN} · dns=${DNS} · public_health=${PUBLIC}

LANDING (permanent):
  https://hitme.dev/landing

CHECKOUT:
  https://hitme.dev/checkout

If dns=NO: one dashboard pass → fleet/HITME_FIX_NOW.txt
NO trycloudflare — disabled.
EOF

cat >"${DRIVE}/fleet/LANDING_URL.txt" <<EOF
LANDING — ${NOW}
https://hitme.dev/landing
EOF

cat >"${DRIVE}/fleet/bus/WORKING_URL.txt" <<EOF
WORKING URL — ${NOW}
https://hitme.dev/landing
EOF

cat >"${DRIVE}/fleet/HITME_STATUS.txt" <<EOF
hitme.dev PERMANENT — ${NOW}
who:${PORT}=UP · tunnel=${TUN} · dns=${DNS} · public=${PUBLIC}

URL: https://hitme.dev/landing
EOF

log "dns=${DNS} public=${PUBLIC}"
if [[ "$PUBLIC" == "200" ]]; then
  log "GREEN hitme.dev"
  exit 0
fi
log "waiting DNS — see fleet/HITME_FIX_NOW.txt"
exit 0
