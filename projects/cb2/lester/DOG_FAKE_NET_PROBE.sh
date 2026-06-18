#!/usr/bin/env bash
# DOG — fake net trust drill · honest post only
set -euo pipefail
for DRIVE in /mnt/shared/GoogleDrive/MyDrive ~/GoogleDrive/MyDrive; do
  [[ -d "$DRIVE/fleet" ]] && break
done
[[ -d "$DRIVE/fleet" ]] || { echo "FAIL: Drive"; exit 1; }

H=$(hostname 2>/dev/null || echo dog64)
IP=$(hostname -I 2>/dev/null | awk '{print $1}')
IP=${IP:-unknown}
T=$(date -Iseconds 2>/dev/null || date)

M8002=$(curl -sf -m 3 -o /dev/null -w '%{http_code}' "http://127.0.0.1:8002/" 2>/dev/null || echo FAIL)
M8765=$(curl -sf -m 3 "http://127.0.0.1:8765/health" 2>/dev/null | head -c 40 || echo DOWN)
M8766=$(curl -sf -m 3 "http://127.0.0.1:8766/health" 2>/dev/null | head -c 40 || echo DOWN)

mkdir -p "$DRIVE/fleet/bus"
cat >"$DRIVE/fleet/bus/dog_outbox.txt" <<EOF
DOG CHECKIN — ${H} — ${IP} — ${T}
hostname: ${H}
agent: DOG · not Composer · not Puppy
probe: FAKE_NET_DRILL
local_ports: :8002=${M8002} :8765=${M8766:0:12} :8766=${M8766:0:12}
mesh: DOWN
status: trust drill ran · honest ports only

Word: DOG
EOF
echo "OK — dog_outbox posted · ports honest"
