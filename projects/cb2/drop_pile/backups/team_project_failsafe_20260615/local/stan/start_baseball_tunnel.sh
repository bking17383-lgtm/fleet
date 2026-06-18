#!/usr/bin/env bash
# Quick public HTTPS for baseball :8002 only — does NOT kill mesh radio :8765 tunnel
set -euo pipefail
if [[ -f "${HOME}/.stan/CB2_NO_GAMES" ]]; then
  echo "BLOCKED: CB2 games parked — no baseball tunnel here."
  exit 0
fi
CF="${HOME}/.stan/cloudflared"
LOG="${HOME}/.stan/baseball_tunnel.log"
URL_FILE="/mnt/shared/GoogleDrive/MyDrive/fleet/DADDY_BASEBALL_URL.txt"
PHONE_FILE="/mnt/shared/GoogleDrive/MyDrive/fleet/BRIAN_PHONE.txt"
PID_FILE="${HOME}/.stan/baseball_tunnel.pid"

[[ -d "$HOME/GoogleDrive/MyDrive" ]] && URL_FILE="$HOME/GoogleDrive/MyDrive/fleet/DADDY_BASEBALL_URL.txt" && PHONE_FILE="$HOME/GoogleDrive/MyDrive/fleet/BRIAN_PHONE.txt"

curl -sf --max-time 5 http://127.0.0.1:8002/api/health >/dev/null || { echo "ERROR: baseball :8002 not up"; exit 1; }

pkill -f "cloudflared tunnel --protocol http2 --url http://127.0.0.1:8002" 2>/dev/null || true
sleep 1

PUBLIC=""
if [[ -f "$LOG" ]]; then
  OLD="$(grep -oE 'https://[a-z0-9-]+\.trycloudflare\.com' "$LOG" 2>/dev/null | tail -1 || true)"
  if [[ -n "$OLD" ]] && curl -sf --max-time 6 "${OLD}/api/health" >/dev/null 2>&1; then
    PUBLIC="$OLD"
  fi
fi

if [[ -z "$PUBLIC" ]]; then
  : >"$LOG"
  nohup "$CF" tunnel --protocol http2 --url "http://127.0.0.1:8002" >>"$LOG" 2>&1 &
  echo $! >"$PID_FILE"
  for _ in $(seq 1 25); do
    sleep 2
    PUBLIC="$(grep -oE 'https://[a-z0-9-]+\.trycloudflare\.com' "$LOG" 2>/dev/null | head -1 || true)"
    [[ -n "$PUBLIC" ]] && break
  done
fi

[[ -n "$PUBLIC" ]] || { echo "WARN: no baseball public URL"; exit 1; }

cat >"$URL_FILE" <<EOF
DADDY BASEBALL — cards app (LTE ok)

$PUBLIC

Local/Tailscale: http://100.115.92.26:8002
Updated: $(date -Iseconds)
Named tunnel cb2-daddy also running when dashboard hostname is set.
EOF

RADIO="$(grep -oE 'https://[a-z0-9-]+\.trycloudflare\.com' /mnt/shared/GoogleDrive/MyDrive/fleet/MESH_RADIO_URL.txt 2>/dev/null | head -1 || true)"
cat >"$PHONE_FILE" <<EOF
For Brian on phone — DADDY + RADIO

BASEBALL (Daddy cards):
  $PUBLIC

MESH RADIO (voice):
  ${RADIO:-see fleet/MESH_RADIO_URL.txt}

Tailscale: baseball :8002 · radio :8765
Updated: $(date -Iseconds)
EOF

echo "PUBLIC: $PUBLIC"
