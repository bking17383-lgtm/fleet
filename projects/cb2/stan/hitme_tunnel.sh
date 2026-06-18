#!/usr/bin/env bash
# hitme.dev — fleet board tunnel (CB2). Quick URL works even when DNS dead.
set -euo pipefail
STAN="${HOME}/.stan"
for DRIVE in /mnt/shared/GoogleDrive/MyDrive "$HOME/GoogleDrive/MyDrive"; do
  [[ -d "$DRIVE/fleet" ]] && break
done
CF="${STAN}/cloudflared"
ENV="${STAN}/cloudflare.env"
PORT=8770
LOG="${STAN}/hitme_tunnel.log"
QUICK_LOG="${STAN}/hitme_quick_tunnel.log"
URL_FILE="${DRIVE}/fleet/bus/PUPPY_FLEET_URL.txt"
STATUS="${DRIVE}/fleet/HITME_STATUS.txt"

[[ -x "$CF" ]] || { echo "missing $CF"; exit 1; }

# Fleet server first
if ! curl -sf "http://127.0.0.1:${PORT}/health" >/dev/null 2>&1; then
  echo "starting hitme_who:${PORT}…"
  nohup python3 "${STAN}/hitme_who_server.py" >>"${STAN}/hitme_who.log" 2>&1 &
  sleep 2
fi
curl -sf "http://127.0.0.1:${PORT}/health" >/dev/null || { echo "FAIL hitme_who"; exit 1; }

# Named tunnel (hitme.dev when DNS + hostnames live)
if [[ -f "$ENV" ]]; then
  # shellcheck source=/dev/null
  source "$ENV"
  if [[ -n "${CLOUDFLARE_TUNNEL_TOKEN:-}" ]] && ! pgrep -f "cloudflared tunnel run --token" >/dev/null 2>&1; then
    nohup "$CF" tunnel run --token "$CLOUDFLARE_TUNNEL_TOKEN" >>"$LOG" 2>&1 &
    sleep 2
  fi
fi

# Quick tunnel — url_keeper owns this; avoid duplicate processes
bash "${STAN}/url_keeper.sh" >>"$LOG" 2>&1 || true
QUICK="$(grep -oE 'https://[a-z0-9-]+\.trycloudflare\.com' "${STAN}/logs/url_keeper_tunnel.log" 2>/dev/null | tail -1 || true)"
if [[ -z "$QUICK" ]] && [[ -f "${DRIVE}/fleet/LIVE_URL.txt" ]]; then
  QUICK="$(grep -oE 'https://[a-z0-9-]+\.trycloudflare\.com' "${DRIVE}/fleet/LIVE_URL.txt" 2>/dev/null | head -1 || true)"
fi

TS_IP="$(hostname -I 2>/dev/null | tr ' ' '\n' | grep '^100\.' | head -1 || true)"
LAN_IP="$(hostname -I 2>/dev/null | tr ' ' '\n' | grep '^192\.168\.' | head -1 || true)"
NOW="$(date -Iseconds 2>/dev/null || date)"

DNS_OK="NO"
if python3 -c "import socket; socket.gethostbyname('hitme.dev')" 2>/dev/null; then
  DNS_OK="YES"
fi

mkdir -p "${DRIVE}/fleet/bus"
cat >"$URL_FILE" <<EOF
PUPPY — ${NOW}
OPEN (works now): ${QUICK:-http://127.0.0.1:${PORT}/puppy}/puppy
TEAM: ${QUICK:-http://127.0.0.1:${PORT}/goal}/goal
CHECKIN: ${QUICK:-http://127.0.0.1:${PORT}/checkin}/checkin

Also: fleet/HITME_LIVE_URL.txt · fleet/bus/WORKING_URL.txt

One command (puppy keyboard):
  bash ~/GoogleDrive/MyDrive/lester/PUPPY_JAILBREAK.sh

hitme.dev: DNS not wired — use QUICK url above
EOF

cat >"$STATUS" <<EOF
hitme.dev STATUS — ${NOW}
hostname: $(hostname -s)

SERVICES
  fleet board :8770  UP
  quick tunnel      ${QUICK:-pending}
  named tunnel      $(pgrep -f 'cloudflared tunnel run' >/dev/null && echo UP || echo DOWN)
  hitme.dev DNS     ${DNS_OK}

PUPPY: open fleet/bus/PUPPY_FLEET_URL.txt · run lester/PUPPY_HITME.sh on puppy
EOF

echo "Fleet board UP :${PORT}"
[[ -n "$QUICK" ]] && echo "LIVE: ${QUICK}/goal"
echo "Wrote: $URL_FILE · fleet/HITME_LIVE_URL.txt"
if [[ -n "$QUICK" ]]; then
  cat >"${DRIVE}/fleet/HITME_LIVE_URL.txt" <<EOF
HITME LIVE URL — ${NOW}
${QUICK}/goal
${QUICK}/checkin
${QUICK}/puppy
Local: http://127.0.0.1:${PORT}/goal
EOF
  echo "${QUICK}/goal" > "${DRIVE}/fleet/bus/WORKING_URL.txt"
fi
