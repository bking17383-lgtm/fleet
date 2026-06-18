#!/usr/bin/env bash
# Puppy — escape mirror · write REAL Drive only
set -euo pipefail
REAL=""
for DRIVE in "$HOME/GoogleDrive/MyDrive" /mnt/shared/GoogleDrive/MyDrive /mnt/home/google_drive/MyDrive; do
  if [[ -d "$DRIVE/fleet/bus" ]] && [[ -w "$DRIVE/fleet/bus" ]]; then
    REAL="$DRIVE"
    break
  fi
done

if [[ -z "$REAL" ]]; then
  echo "FAIL: no writable Google Drive — open Files · mount My Drive" >&2
  exit 1
fi

MIRROR="${HOME}/.stan/fleet_bus"
if [[ -d "$MIRROR/fleet" ]]; then
  echo "WARN: mirror at ~/.stan/fleet_bus — ignoring for posts"
fi

TOK="LIVE-$(date +%H%M%S)"
NOW=$(date -Iseconds 2>/dev/null || date)
IP=$(hostname -I 2>/dev/null | tr ' ' '\n' | grep -E '^192\.168\.' | head -1)
IP=${IP:-$(hostname -I 2>/dev/null | awk '{print $1}')}
IP=${IP:-UNKNOWN}
BUS="$REAL/fleet/bus"

cat > "$BUS/PUPPY_LIVE_PROOF.txt" <<EOF
REAL TEXT FROM PUPPY — NOT A MIRROR
TIME: ${NOW}
TOKEN=${TOK}
drive_path=${REAL}
hostname: $(hostname -s 2>/dev/null || echo puppy64)
EOF

cat > "$BUS/puppy_outbox.txt" <<EOF
--- from: puppy | real_drive | ${NOW} ---
PUPPY CHECKIN — puppy64 — ${IP} — ${NOW}
hostname: puppy64
host=puppy64 ip=${IP}
mirror=NO · path=${REAL}/fleet/bus/
token=${TOK}
EOF

cat > "$BUS/puppy_wrote.txt" <<EOF
puppy_wrote — ${NOW}
real_drive=${REAL}
token=${TOK}
ok=YES
EOF

# read-back proof
RB=$(grep -m1 '^TOKEN=' "$BUS/PUPPY_LIVE_PROOF.txt" | cut -d= -f2)
if [[ "$RB" != "$TOK" ]]; then
  echo "FAIL: read-back token mismatch — still mirror?" >&2
  exit 2
fi

echo "REAL DRIVE OK · path=$REAL"
echo "TOKEN MATCH · $TOK"
echo "wrote puppy_outbox + PUPPY_LIVE_PROOF.txt"
head -4 "$BUS/puppy_outbox.txt"
