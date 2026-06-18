#!/usr/bin/env bash
# NEW PUPPY BOOT V2 — check in honest · no fake green · one script
set -euo pipefail

for DRIVE in "$HOME/GoogleDrive/MyDrive" /mnt/shared/GoogleDrive/MyDrive /mnt/home/google_drive/MyDrive; do
  [[ -d "$DRIVE/fleet" ]] && break
done
[[ -d "$DRIVE/fleet" ]] || { echo "FAIL: Drive not mounted"; exit 1; }

STAN="${HOME}/.stan"
mkdir -p "$STAN/logs" "$DRIVE/fleet/bus"

# Statusline fix if present (stops lying NET clean)
if [[ -f "$DRIVE/lester/PUPPY_STATUSLINE_FIX.sh" ]]; then
  bash "$DRIVE/lester/PUPPY_STATUSLINE_FIX.sh" 2>/dev/null || true
fi

HOST=$(hostname 2>/dev/null || echo puppy64)
IP=$(hostname -I 2>/dev/null | tr ' ' '\n' | grep -E '^192\.168\.|^100\.' | head -1)
IP=${IP:-$(hostname -I 2>/dev/null | awk '{print $1}')}
IP=${IP:-unknown}
NOW=$(date -Iseconds 2>/dev/null || date)

port_check() {
  local p=$1
  if curl -sf --connect-timeout 1 "http://127.0.0.1:${p}/" >/dev/null 2>&1; then
    echo "UP"
  elif curl -sf --connect-timeout 1 "http://127.0.0.1:${p}/health" >/dev/null 2>&1; then
    echo "UP"
  else
    echo "DOWN"
  fi
}

P8765=$(port_check 8765)
P8766=$(port_check 8766)
P8002=$(port_check 8002)

OUTBOX="$DRIVE/fleet/bus/puppy_outbox.txt"
cat >"$OUTBOX" <<EOF
PUPPY CHECKIN — ${HOST} — ${IP} — ${NOW}

V2 boot · honest only
ports: :8765=${P8765} :8766=${P8766} :8002=${P8002}
mesh: not started unless ordered
next: read fleet/bus/cpt_to_puppy.txt · one job
boot: lester/NEW_PUPPY_BOOT.sh
EOF

CARD="$DRIVE/fleet/bus/PUPPY_V2_BOOT.txt"
cat >"$CARD" <<EOF
PUPPY V2 BOOT — ${NOW}
host=${HOST} ip=${IP}
outbox=fleet/bus/puppy_outbox.txt
architecture=fleet/FLEET_ARCHITECTURE_V2.txt
EOF

echo "OK — posted ${OUTBOX}"
echo "Ports :8765=${P8765} :8766=${P8766} :8002=${P8002}"
echo "Open on this box: http://127.0.0.1:8770/puppy (if hitme reachable via LAN/Tailscale)"
cat "$OUTBOX"
