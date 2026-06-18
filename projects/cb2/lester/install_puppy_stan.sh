#!/usr/bin/env bash
# Puppy64 — install NET slave tools from Drive (fixes missing local_slave.py)
set -euo pipefail
for DRIVE in /mnt/home/google_drive/MyDrive "$HOME/GoogleDrive/MyDrive" /mnt/shared/GoogleDrive/MyDrive; do
  [[ -d "$DRIVE/fleet" ]] && break
done
[[ -d "$DRIVE/fleet" ]] || { echo "FAIL: Drive not mounted — open Files → Google Drive → My Drive first"; exit 1; }

STAN="${HOME}/.stan"
mkdir -p "$STAN"
cp "$DRIVE/lester/bus_lane.py" "$DRIVE/lester/local_slave.py" "$STAN/"
echo 5f54badb > "$STAN/slave.key"
chmod 600 "$STAN/slave.key"
chmod +x "$STAN/local_slave.py" 2>/dev/null || true

echo "OK — installed ~/.stan/{bus_lane,local_slave}.py · NET key set"
python3 "$STAN/local_slave.py" NET
