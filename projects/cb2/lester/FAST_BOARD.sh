#!/usr/bin/env bash
# FAST — no hitme.dev · no tunnel · 10 second board
set -u
for D in "$HOME/GoogleDrive/MyDrive" /mnt/shared/GoogleDrive/MyDrive /mnt/home/google_drive/MyDrive; do
  [[ -d "$D/fleet/bus" ]] && BUS="$D/fleet/bus" && break
done
[[ -n "${BUS:-}" ]] || { echo "FAIL: Drive/bus not found"; exit 1; }
PORT=8888
pkill -f "http.server ${PORT}" 2>/dev/null || true
sleep 1
nohup python3 -m http.server "$PORT" --directory "$BUS" >>/tmp/fleet_http.log 2>&1 &
sleep 1
IP=$(hostname -I 2>/dev/null | awk '{print $1}')
echo ""
echo "OPEN ON THIS KEYBOARD:"
echo "  http://127.0.0.1:${PORT}/FLEET_CHECKIN.txt"
echo "  http://127.0.0.1:${PORT}/FLEET_NEEDS_SERVER.txt"
echo "  http://127.0.0.1:${PORT}/PUPPY_FIX_TRUTH.txt"
[[ -n "$IP" ]] && echo "  http://${IP}:${PORT}/FLEET_CHECKIN.txt"
echo ""
echo "FIX PUPPY (same keyboard if puppy64):"
echo "  bash ${D:-$HOME/GoogleDrive/MyDrive}/lester/PUPPY_JAILBREAK.sh"
