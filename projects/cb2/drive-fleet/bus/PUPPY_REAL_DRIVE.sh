#!/usr/bin/env bash
# Puppy — write check-in · lester6 mirror OR real Drive
set -euo pipefail
REAL=""
for DRIVE in /mnt/home/lester6 "$HOME/GoogleDrive/MyDrive" /mnt/home/google_drive/MyDrive /mnt/shared/GoogleDrive/MyDrive; do
  if [[ -d "$DRIVE/fleet/bus" ]] && [[ -w "$DRIVE/fleet/bus" ]]; then
    REAL="$DRIVE"
    break
  fi
done
[[ -n "$REAL" ]] || { echo "FAIL: no fleet/bus writable"; exit 1; }

TOK="LIVE-$(date +%H%M%S)"
NOW=$(date -Iseconds 2>/dev/null || date)
IP=$(hostname -I 2>/dev/null | tr ' ' '\n' | grep -E '^192\.168\.' | head -1)
IP=${IP:-$(hostname -I 2>/dev/null | awk '{print $1}')}
IP=${IP:-UNKNOWN}
BUS="$REAL/fleet/bus"

cat > "$BUS/screen_read.txt" <<EOF
PUPPY RAN REAL_DRIVE — ${NOW}
TOKEN=${TOK}
path=${REAL}
EOF

cat > "$BUS/puppy_outbox.txt" <<EOF
--- from: puppy | ${NOW} ---
PUPPY CHECKIN — puppy64 — ${IP} — ${NOW}
hostname: puppy64
host=puppy64 ip=${IP}
path=${REAL}
token=${TOK}
EOF

echo "OK path=$REAL TOKEN=$TOK"
head -3 "$BUS/puppy_outbox.txt"
