#!/usr/bin/env bash
# Bunny indie loop — read TO_BUNNY.txt · ack FROM_BUNNY.txt · 30s
set -euo pipefail
# Bun: real sync is usually ~/GoogleDrive — do NOT prefer empty /mnt/shared
if [[ -d "/mnt/shared/GoogleDrive/MyDrive/fleet" ]]; then
  DRIVE="/mnt/shared/GoogleDrive/MyDrive"
elif [[ -d "${HOME}/GoogleDrive/MyDrive/fleet" ]]; then
  DRIVE="${HOME}/GoogleDrive/MyDrive"
else
  DRIVE="${HOME}/GoogleDrive/MyDrive"
fi
LOOP="${DRIVE}/fleet/indie_loop"
TO="${LOOP}/TO_BUNNY.txt"
FROM="${LOOP}/FROM_BUNNY.txt"
ACK="${DRIVE}/drop_pile/from_bbbunny"
INTERVAL="${BUNNY_LOOP_SEC:-30}"
LOG="${HOME}/bbuny_loop.log"

mkdir -p "$LOOP" "$ACK"
LOOP_POKE="${DRIVE}/drop_pile/to_bbbunny/LOOP.txt"

_write_pulse() {
  HOST=$(hostname)
  IP=$(curl -4 -sf --max-time 10 ifconfig.me 2>/dev/null || echo unknown)
  P80=down; P8002=down; P8770=down
  curl -sf -m 2 http://127.0.0.1/ >/dev/null && P80=up
  curl -sf -m 2 http://127.0.0.1:8002/api/health >/dev/null && P8002=up
  curl -sf -m 2 http://127.0.0.1:8770/health >/dev/null && P8770=up
  if [[ -f "$TO" ]] && grep -q start_hitme_proxy "$TO" 2>/dev/null; then
    bash "${DRIVE}/lester/hitme_simple/start_hitme_proxy.sh" >>"$LOG" 2>&1 || true
  fi
  {
    echo "FROM_BUNNY — $HOST — $(date -Iseconds)"
    echo "public_ip: $IP"
    echo "ports: :80=$P80 :8002=$P8002 :8770=$P8770"
    echo "drive: $DRIVE"
    echo "job_read: ${TO:-missing}"
    echo "--- TO_BUNNY ---"
    [[ -f "$TO" ]] && head -12 "$TO" || echo "(no job file)"
  } >"$FROM"
  echo "$IP" >"${ACK}/PUBLIC_IP.txt"
  {
    echo "ACK $HOST $(date -Iseconds)"
    echo "public_ip: $IP"
    echo "ports: :80=$P80 :8002=$P8002 :8770=$P8770"
  } >"${ACK}/ACK.txt"
}

if [[ "${1:-}" == "once" ]]; then
  _write_pulse
  echo "$(date -Iseconds) once pulse → $FROM" >>"$LOG"
  exit 0
fi

while true; do
  [[ -f "$LOOP_POKE" ]] && rm -f "$LOOP_POKE"
  _write_pulse
  sleep "$INTERVAL"
done
