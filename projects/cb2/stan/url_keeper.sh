#!/usr/bin/env bash
# ONE keeper — hitme :8770 + single HTTPS tunnel + honest LIVE_URL on Drive
set -uo pipefail
STAN="${HOME}/.stan"
CF="${STAN}/cloudflared"
PORT=8770
EMPTY=/tmp/cf-empty.yml
LOG="${STAN}/logs/url_keeper.log"
PIDFILE="${STAN}/url_keeper_tunnel.pid"
for DRIVE in /mnt/shared/GoogleDrive/MyDrive "$HOME/GoogleDrive/MyDrive"; do
  [[ -d "$DRIVE/fleet" ]] && break
done
LIVE="${DRIVE}/fleet/LIVE_URL.txt"
STABLE="${DRIVE}/fleet/STABLE_URL.txt"
ENV="${STAN}/cloudflare.env"

log() { echo "$(date -Iseconds) $*" >>"$LOG"; }

echo "tunnel: none" >"$EMPTY"

# --- hitme ---
if ! curl -sf "http://127.0.0.1:${PORT}/health" >/dev/null 2>&1; then
  log "restart hitme"
  pkill -f hitme_who_server.py 2>/dev/null || true
  sleep 1
  nohup python3 "${STAN}/hitme_who_server.py" >>"${STAN}/logs/hitme_who.log" 2>&1 &
  sleep 3
fi

# --- named tunnel (hitme.dev when DNS exists) — exactly one ---
if [[ -f "$ENV" ]]; then
  # shellcheck source=/dev/null
  source "$ENV"
  if [[ -n "${CLOUDFLARE_TUNNEL_TOKEN:-}" ]]; then
    n="$(pgrep -f 'cloudflared tunnel run --token' 2>/dev/null | wc -l | tr -d ' ')"
    if [[ "${n:-0}" != "1" ]]; then
      log "dedupe named tunnel (${n})"
      pkill -f 'cloudflared tunnel run' 2>/dev/null || true
      sleep 2
      nohup "$CF" tunnel run --token "$CLOUDFLARE_TUNNEL_TOKEN" >>"${STAN}/logs/hitme_tunnel.log" 2>&1 &
      sleep 2
    fi
  fi
fi

# --- kill duplicate quick tunnels (root cause of 502/404 chaos) ---
keeper_pid=""
[[ -f "$PIDFILE" ]] && keeper_pid="$(cat "$PIDFILE" 2>/dev/null || true)"
for pid in $(pgrep -f "127.0.0.1:${PORT}" 2>/dev/null || true); do
  args="$(ps -p "$pid" -o args= 2>/dev/null || true)"
  [[ "$args" == *cloudflared*tunnel* ]] || continue
  [[ "$args" == *"tunnel run"* ]] && continue
  if [[ -n "$keeper_pid" && "$pid" == "$keeper_pid" ]] && kill -0 "$pid" 2>/dev/null; then
    continue
  fi
  log "kill stray quick tunnel pid=$pid"
  kill "$pid" 2>/dev/null || true
done
sleep 1

# --- PERMANENT MODE: no trycloudflare ---
if [[ "${HITME_NO_QUICK:-1}" == "1" ]]; then
  log "quick tunnel disabled (hitme.dev permanent)"
  if [[ -f "$PIDFILE" ]]; then
    kill "$(cat "$PIDFILE")" 2>/dev/null || true
    rm -f "$PIDFILE"
  fi
  pkill -f "cloudflared tunnel --config ${EMPTY}" 2>/dev/null || true
  PUBLIC_OK=""
  if python3 -c "import socket; socket.gethostbyname('hitme.dev')" 2>/dev/null; then
    if curl -sf -m 10 "https://hitme.dev/health" | grep -q '"ok"'; then
      PUBLIC_OK="https://hitme.dev"
      log "hitme.dev GREEN"
    fi
  fi
  NOW="$(date -Iseconds)"
  if [[ -n "$PUBLIC_OK" ]]; then
    cat >"$LIVE" <<EOF
hitme.dev LIVE — ${NOW}

https://hitme.dev/landing
https://hitme.dev/checkout
EOF
  else
    cat >"$LIVE" <<EOF
hitme.dev PENDING DNS — ${NOW}
See fleet/HITME_FIX_NOW.txt
Target: https://hitme.dev/landing
NO trycloudflare.
EOF
  fi
  exit 0
fi

# --- one quick tunnel (empty config — no 404 catch-all) ---
need_quick=1
if [[ -f "$PIDFILE" ]]; then
  opid="$(cat "$PIDFILE" 2>/dev/null || true)"
  if [[ -n "$opid" ]] && kill -0 "$opid" 2>/dev/null; then
    need_quick=0
  fi
fi
if [[ "$need_quick" -eq 1 ]]; then
  log "start quick tunnel"
  nohup "$CF" tunnel --config "$EMPTY" --url "http://127.0.0.1:${PORT}" \
    >>"${STAN}/logs/url_keeper_tunnel.log" 2>&1 &
  echo $! >"$PIDFILE"
  sleep 8
fi

# --- find URL that actually works ---
PUBLIC_OK=""
PERMANENT=""

if python3 -c "import socket; socket.gethostbyname('hitme.dev')" 2>/dev/null; then
  if curl -sf -m 10 "https://hitme.dev/health" | grep -q '"ok"'; then
    PUBLIC_OK="https://hitme.dev"
    PERMANENT="https://hitme.dev"
    log "hitme.dev GREEN"
  fi
fi

if [[ -z "$PUBLIC_OK" ]]; then
  URL="$(grep -oE 'https://[a-z0-9-]+\.trycloudflare\.com' "${STAN}/logs/url_keeper_tunnel.log" 2>/dev/null | tail -1 || true)"
  if [[ -n "$URL" ]] && curl -sf -m 12 "${URL}/health" | grep -q '"ok"'; then
    PUBLIC_OK="$URL"
    log "quick tunnel OK $URL"
  else
    log "quick tunnel FAIL — recycle"
    [[ -f "$PIDFILE" ]] && kill "$(cat "$PIDFILE")" 2>/dev/null || true
    rm -f "$PIDFILE"
    pkill -f "cloudflared tunnel --config ${EMPTY}" 2>/dev/null || true
    sleep 2
    nohup "$CF" tunnel --config "$EMPTY" --url "http://127.0.0.1:${PORT}" \
      >>"${STAN}/logs/url_keeper_tunnel.log" 2>&1 &
    echo $! >"$PIDFILE"
    sleep 10
    URL="$(grep -oE 'https://[a-z0-9-]+\.trycloudflare\.com' "${STAN}/logs/url_keeper_tunnel.log" 2>/dev/null | tail -1 || true)"
    if [[ -n "$URL" ]] && curl -sf -m 12 "${URL}/health" | grep -q '"ok"'; then
      PUBLIC_OK="$URL"
      log "quick tunnel recovered $URL"
    fi
  fi
fi

NOW="$(date -Iseconds)"
TS_IP="$(hostname -I 2>/dev/null | tr ' ' '\n' | grep '^100\.' | head -1 || true)"

cat >"$STABLE" <<EOF
PERMANENT (wire once — never changes):
  https://hitme.dev/dirt-strong

Why not live yet: hitme.dev DNS not pointed at tunnel.
One-time fix (5 min):
  Cloudflare → Tunnels → cb2-daddy → Public Hostname → hitme.dev → http://localhost:8770
  Or paste API token in ~/.stan/cloudflare_api.env → bash ~/.stan/hitme_cf_provision.sh

See: fleet/HITME_TUNNEL_HOSTNAMES.txt
EOF

if [[ -n "$PUBLIC_OK" ]]; then
  cat >"$LIVE" <<EOF
LIVE URL — verified ${NOW}
keeper: ~/.stan/url_keeper.sh (cron every 2 min)

ONE LINK (landing — send testers):
  ${PUBLIC_OK}/landing

Permanent (when DNS wired):
  https://hitme.dev/landing

Paywall checkout:
  ${PUBLIC_OK}/checkout

Also:
  ${PUBLIC_OK}/studio
  ${PUBLIC_OK}/cards/sell

Status: AWAKE
EOF
  cat >"${DRIVE}/fleet/bus/WORKING_URL.txt" <<EOF
WORKING URL — ${NOW}
${PUBLIC_OK}/landing
EOF
  cat >"${DRIVE}/fleet/LANDING_URL.txt" <<EOF
LANDING — ${NOW}
${PUBLIC_OK}/landing
https://hitme.dev/landing
EOF
  log "AWAKE ${PUBLIC_OK}"
else
  cat >"$LIVE" <<EOF
LIVE URL — FAILED ${NOW}

hitme local: $(curl -sf http://127.0.0.1:${PORT}/health >/dev/null && echo UP || echo DOWN)
tunnel: $( [[ -f "$PIDFILE" ]] && kill -0 "$(cat "$PIDFILE")" 2>/dev/null && echo UP || echo DOWN)

Run: bash ~/.stan/url_keeper.sh
Fix permanent: fleet/STABLE_URL.txt
EOF
  log "FAILED"
fi
