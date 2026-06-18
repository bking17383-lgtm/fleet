#!/usr/bin/env bash
# Public HTTPS for mesh radio :8765 (works when Tailscale fails on phone)
set -euo pipefail
CF="${HOME}/.stan/cloudflared"
LOG="${HOME}/.stan/mesh_radio_tunnel.log"
URL_FILE="/mnt/shared/GoogleDrive/MyDrive/fleet/MESH_RADIO_URL.txt"
PHONE_FILE="/mnt/shared/GoogleDrive/MyDrive/fleet/BRIAN_PHONE.txt"
PID_FILE="${HOME}/.stan/mesh_radio_tunnel.pid"

[[ -d "$HOME/GoogleDrive/MyDrive" ]] && URL_FILE="$HOME/GoogleDrive/MyDrive/fleet/MESH_RADIO_URL.txt" && PHONE_FILE="$HOME/GoogleDrive/MyDrive/fleet/BRIAN_PHONE.txt"

pkill -f "cloudflared tunnel --protocol http2 --url http://127.0.0.1:8765" 2>/dev/null || true
sleep 1

# Reuse live quick tunnel if still healthy (avoids new URL → 1033 on phone)
if [[ -f "$LOG" ]]; then
  OLD="$(grep -oE 'https://[a-z0-9-]+\.trycloudflare\.com' "$LOG" 2>/dev/null | tail -1 || true)"
  if [[ -n "$OLD" ]] && curl -sf --max-time 6 "${OLD}/status" >/dev/null 2>&1; then
    PUBLIC="$OLD"
  fi
fi

if [[ -z "${PUBLIC:-}" ]]; then
  : >"$LOG"
  nohup "$CF" tunnel --protocol http2 --url "http://127.0.0.1:8765" >>"$LOG" 2>&1 &
  echo $! >"$PID_FILE"
  for _ in $(seq 1 25); do
    sleep 2
    PUBLIC="$(grep -oE 'https://[a-z0-9-]+\.trycloudflare\.com' "$LOG" 2>/dev/null | head -1 || true)"
    [[ -n "$PUBLIC" ]] && break
  done
fi

if [[ -z "$PUBLIC" ]]; then
  echo "WARN: no public URL yet — tail $LOG"
  exit 1
fi

OFFICE_LOCAL="http://127.0.0.1:8765/office"
ROVER_LOCAL="http://127.0.0.1:8765/rover"
cat >"${URL_FILE%/*}/OFFICE_RADIO.txt" <<EOF
RADIO OFFICE — CB2 fleet debug (local or tunnel)

Local:  $OFFICE_LOCAL
Public: ${PUBLIC}/office

Updated: $(date -Iseconds)
EOF

cat >"${URL_FILE%/*}/ROVER_RADIO_URL.txt" <<EOF
ROVER — Moto phone lane (LTE, no Tailscale)

${PUBLIC}/rover

Add to Home Screen. Name: CAPTN
Normal = /radio · Emergency = /emergency
MIC ON = talk · SNAP = eyes · HEAR AGAIN = CAPTN voice
No Gemini Live on phone.
Updated: $(date -Iseconds)
Keep Chromebook awake.
EOF

cat >"$URL_FILE" <<EOF
MESH RADIO — phone base (works on LTE, no Tailscale needed)

${PUBLIC}/rover

ROVER lane for Moto: fleet/ROVER_RADIO_URL.txt
Add to Home Screen. Name: CAPTN
Updated: $(date -Iseconds)
Keep Chromebook awake.
EOF

cat >"$PHONE_FILE" <<EOF
For Brian on phone — ROVER

USE THIS NOW (Moto LTE or WiFi):
  ${PUBLIC}/rover

Tailscale (when phone app shows Connected + sees penguin):
  http://100.115.92.26:8765/rover

Desk (Chromebook only): http://127.0.0.1:8765/desk
Office (CB2 eyes): http://127.0.0.1:8765/office
Baseball: http://100.115.92.26:8002

No Gemini Live on phone — ROVER page only.
Guide: phone/ROVER_OPEN_THIS.txt
Updated: $(date -Iseconds)
EOF

echo "PUBLIC: $PUBLIC"
echo "Wrote: $URL_FILE"
