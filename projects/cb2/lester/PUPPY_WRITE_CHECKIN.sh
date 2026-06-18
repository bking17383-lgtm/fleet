#!/usr/bin/env bash
# Puppy — write honest check-in to Drive · one command · no typing for Brian
set -euo pipefail
for DRIVE in "$HOME/GoogleDrive/MyDrive" /mnt/shared/GoogleDrive/MyDrive /mnt/home/google_drive/MyDrive; do
  [[ -d "$DRIVE/fleet/bus" ]] && break
done
if [[ ! -d "${DRIVE:-}/fleet/bus" ]]; then
  echo "FAIL: Google Drive not mounted — open Files app · mount My Drive · rerun" >&2
  exit 1
fi

IP=$(hostname -I 2>/dev/null | tr ' ' '\n' | grep -E '^192\.168\.' | head -1)
IP=${IP:-$(hostname -I 2>/dev/null | awk '{print $1}')}
IP=${IP:-UNKNOWN}
NOW=$(date -Iseconds 2>/dev/null || date)
BUS="$DRIVE/fleet/bus"

cat > "$BUS/puppy_outbox.txt" <<EOF
--- from: puppy | checkin | ${NOW} ---
PUPPY CHECKIN — puppy64 — ${IP} — ${NOW}
hostname: puppy64
host=puppy64 ip=${IP}
status: CHECKIN · wrote from PUPPY_WRITE_CHECKIN.sh
note: not 3/3 until FLEET_CHECKIN shows Puppy ✓ fresh
EOF

cat > "$BUS/puppy_wrote.txt" <<EOF
puppy_wrote — ${NOW}
ok=YES
path=${BUS}/puppy_outbox.txt
line=PUPPY CHECKIN — puppy64 — ${IP} — ${NOW}
next=Brian refresh Drive · read fleet/bus/FLEET_CHECKIN.txt
EOF

echo "OK — wrote ${BUS}/puppy_outbox.txt"
echo "PUPPY CHECKIN — puppy64 — ${IP} — ${NOW}"
head -5 "$BUS/puppy_outbox.txt"
