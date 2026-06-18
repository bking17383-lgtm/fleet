#!/usr/bin/env bash
# Puppy leash — start local page + open Firefox (works when hitme.dev DNS down)
set -u
for DRIVE in /mnt/home/google_drive/MyDrive "$HOME/GoogleDrive/MyDrive" /mnt/shared/GoogleDrive/MyDrive; do
  [[ -d "$DRIVE/fleet" ]] && break
done
[[ -d "$DRIVE/fleet" ]] || { echo "FAIL: Drive not mounted"; exit 1; }

# Honest fleet bar (stops fake 3/3 from stale NET clean)
bash "$DRIVE/lester/PUPPY_STATUSLINE_FIX.sh" 2>/dev/null || true

STAN="${HOME}/.stan"
PKG="${DRIVE}/lester/puppy_hitme"
PORT=8770
mkdir -p "$STAN"
cp -f "$PKG/hitme_who_server.py" "$PKG/bus_lane.py" "$PKG/design_links.py" "$STAN/" 2>/dev/null || true

python3 -c "import flask" 2>/dev/null || python3 -m pip install --user flask >/dev/null 2>&1

if ! curl -sf "http://127.0.0.1:${PORT}/health" >/dev/null 2>&1; then
  pkill -f hitme_who_server.py 2>/dev/null || true
  sleep 1
  nohup python3 "$STAN/hitme_who_server.py" >>"$STAN/hitme.log" 2>&1 &
  sleep 2
fi

OPEN="http://127.0.0.1:${PORT}/puppy"
IP=$(hostname -I 2>/dev/null | tr ' ' '\n' | grep -E '^192\.168\.' | head -1)
NOW=$(date -Iseconds 2>/dev/null || date)
BUS="${DRIVE}/fleet/bus"
mkdir -p "$BUS"

{
  echo ""
  echo "--- PUPPY LEASH | ${NOW} ---"
  echo "PUPPY CHECKIN — puppy64 — ${IP:-?} — ${NOW}"
  echo "open: ${OPEN}"
  echo "hitme.dev: pending DNS/tunnel — use local URL above"
  echo "health: $(curl -sf "http://127.0.0.1:${PORT}/health" || echo FAIL)"
} >> "$BUS/puppy_outbox.txt"

echo "OPEN: ${OPEN}"
command -v firefox >/dev/null && firefox "$OPEN" >/dev/null 2>&1 &
command -v firefox-esr >/dev/null && firefox-esr "$OPEN" >/dev/null 2>&1 &
