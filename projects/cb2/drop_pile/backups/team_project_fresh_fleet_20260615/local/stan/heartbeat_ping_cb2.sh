#!/bin/bash
# Cursor session start — ping cb2 heartbeat (Daddy T3)
# Run at start of Daddy Cursor sessions on CB2

DRIVE="${DRIVE:-$HOME/GoogleDrive/MyDrive}"
[ -d /mnt/shared/GoogleDrive/MyDrive ] && DRIVE=/mnt/shared/GoogleDrive/MyDrive

HB="$DRIVE/drop_pile/from_lester/cb2_heartbeat.md"
NOW="$(date -Iseconds)"

cat > "$HB" <<EOF
--- cb2 heartbeat ---
time: $NOW
power: plugged in
cursor: live
lester6: awaiting
paired: no
last_cursor_ping: $NOW
last_lester_refresh: (pending BEACON PULSE)
last_brian: Cursor session started — BEACON refresh now
EOF

echo "cb2 heartbeat pinged: cursor live — tell BEACON: PULSE"
