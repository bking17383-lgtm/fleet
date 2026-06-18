#!/usr/bin/env bash
# Puppy — install honest fleet bar (stops fake 3/3)
set -euo pipefail
for DRIVE in /mnt/shared/GoogleDrive/MyDrive "$HOME/GoogleDrive/MyDrive" /mnt/home/google_drive/MyDrive; do
  [[ -d "$DRIVE/fleet" ]] && break
done
mkdir -p ~/.cursor
cp -f "$DRIVE/lester/gem_statusline.sh" ~/.cursor/statusline.sh
chmod +x ~/.cursor/statusline.sh
echo "OK: honest statusline → ~/.cursor/statusline.sh"
echo "Truth: read fleet/bus/FLEET_CHECKIN.txt (not stale NET clean)"
python3 ~/.cursor/statusline.sh <<< '{}' 2>/dev/null || true
