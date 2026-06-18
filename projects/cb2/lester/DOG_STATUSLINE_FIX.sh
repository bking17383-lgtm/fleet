#!/usr/bin/env bash
# DOG box — fix Cursor footer · honest fleet bar
set -euo pipefail
for DRIVE in /mnt/shared/GoogleDrive/MyDrive ~/GoogleDrive/MyDrive; do
  [[ -d "$DRIVE/fleet" ]] && break
done
[[ -d "$DRIVE/fleet" ]] || { echo "FAIL: mount Drive"; exit 1; }
cp -f "$DRIVE/lester/dog_statusline.sh" ~/.cursor/statusline.sh
chmod +x ~/.cursor/statusline.sh
# post checkin
H=$(hostname 2>/dev/null || echo dog64)
IP=$(hostname -I 2>/dev/null | awk '{print $1}')
IP=${IP:-unknown}
T=$(date -Iseconds 2>/dev/null || date)
mkdir -p "$DRIVE/fleet/bus"
cat >"$DRIVE/fleet/bus/dog_outbox.txt" <<EOF
DOG CHECKIN — ${H} — ${IP} — ${T}
hostname: ${H}
agent: DOG · not Composer · not Puppy
status: NET lane · new agent
EOF
echo "OK — statusline + dog_outbox"
python3 ~/.cursor/statusline.sh <<< '{}' 2>/dev/null || true
