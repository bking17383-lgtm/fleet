#!/usr/bin/env bash
# UNCLE PUPPY TAKEOVER — CB1 Linux only · hold NET proxy until puppy64 back
set -euo pipefail
STAN="${HOME}/.stan"
for DRIVE in "${HOME}/GoogleDrive/MyDrive" /mnt/shared/GoogleDrive/MyDrive; do
  [[ -d "$DRIVE/fleet" ]] && break
done
[[ -d "$DRIVE/fleet" ]] || { echo "Drive not mounted"; exit 1; }

HOST=$(hostname -s 2>/dev/null || echo cb1)
if [[ "$HOST" == "penguin" ]] || [[ "$(hostname)" == *penguin* ]]; then
  echo "REFUSE — run on CB1 Linux only"
  exit 2
fi

IP=$(hostname -I 2>/dev/null | awk '{print $1}')
NOW=$(date -Iseconds)
PUPPY_IP="${PUPPY_LAN:-192.168.1.4}"
mkdir -p "$STAN/logs"

log() { echo "$1" | tee -a "$STAN/logs/uncle_puppy_takeover.log"; }

log "=== UNCLE PUPPY TAKEOVER ${NOW} ==="

# Reboot Uncle agent stack
if [[ -x "$STAN/uncle_exec.sh" ]]; then
  bash "$STAN/uncle_exec.sh" 2>&1 | tee -a "$STAN/logs/uncle_puppy_takeover.log" || true
elif [[ -x "$DRIVE/lester/uncle_exec.sh" ]]; then
  bash "$DRIVE/lester/uncle_exec.sh" 2>&1 | tee -a "$STAN/logs/uncle_puppy_takeover.log" || true
else
  log "WARN: no uncle_exec.sh"
fi

port() {
  local p=$1
  if curl -sf --connect-timeout 2 "http://${PUPPY_IP}:${p}/health" >/dev/null 2>&1; then
    echo UP
  elif curl -sf --connect-timeout 2 "http://${PUPPY_IP}:${p}/" >/dev/null 2>&1; then
    echo UP
  else
    echo DOWN
  fi
}

PING=DOWN
ping -c 1 -W 2 "$PUPPY_IP" >/dev/null 2>&1 && PING=UP
P8002=$(port 8002)
P8765=$(port 8765)
P8766=$(port 8766)

PROXY="$DRIVE/fleet/bus/UNCLE_PUPPY_PROXY.txt"
cat >"$PROXY" <<EOF
UNCLE PUPPY PROXY — ${NOW}
from: Uncle on ${HOST} (${IP})
puppy_lan: ${PUPPY_IP}
ping: ${PING}
ports: :8002=${P8002} :8765=${P8765} :8766=${P8766}

ROLE: Uncle holds Puppy NET proxy until puppy64 posts real checkin.
Daddy TEMP still on penguin :8765 :8766 :8770 — both OK during wipe.

FIREFOX (Brian on CB1):
  http://127.0.0.1:8770/checkin  (if Tailscale/LAN to penguin)
  http://100.115.92.26:8770/checkin
  file:///${DRIVE}/fleet/bus/DADDY_TEMPROLE.txt

IF PUPPY LAN UP + keyboard there:
  bash ~/GoogleDrive/MyDrive/lester/NEW_PUPPY_BOOT.sh

UNCLE agent rebooted: uncle_exec.sh ran this tick.
EOF

OUT="$DRIVE/fleet/bus/uncle_to_cpt.txt"
{
  echo "UNCLE CHECKIN — cb1 — ${IP} — ${NOW}"
  echo "host=cb1 ip=${IP}"
  echo "role=UNCLE PUPPY PROXY until puppy64 live"
  echo "puppy_lan=${PUPPY_IP} ping=${PING} :8002=${P8002} :8765=${P8765} :8766=${P8766}"
  echo "agent=rebooted uncle_exec + UNCLE_PUPPY_TAKEOVER.sh"
  echo "read: fleet/bus/UNCLE_PUPPY_PROXY.txt · fleet/DADDY_OWNS_ALL.txt"
  echo "firefox: open checkin + Drive bus for Brian"
} >"$OUT"

log "posted ${OUT} and ${PROXY}"
cat "$OUT"
