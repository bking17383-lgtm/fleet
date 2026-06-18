#!/usr/bin/env bash
# Brian says SLAVE — absorb drops, pulse bus, keep services alive.
set -euo pipefail
STAN="${HOME}/.stan"
mkdir -p "${STAN}/local_inbox" "${STAN}/logs"

python3 -c "from bus_lane import _ensure_local_bus; _ensure_local_bus()"

echo f770e0dc > "${STAN}/slave.key"
chmod 600 "${STAN}/slave.key"

for f in "${HOME}"/Screenshot*.png "${HOME}"/Screenshot*.jpg "${HOME}"/Screenshot*.jpeg \
         "${HOME}"/*.png "${HOME}"/*.jpg "${HOME}"/*.jpeg; do
  [[ -f "$f" ]] || continue
  cp -n "$f" "${STAN}/local_inbox/" 2>/dev/null || cp "$f" "${STAN}/local_inbox/"
done

# Kill stale servers that 500 on dead fuse
pkill -f "hitme_who_server.py" 2>/dev/null || true
pkill -f "sarah_voice_sample.py" 2>/dev/null || true
sleep 1
python3 "${STAN}/hitme_who_server.py" &
python3 "${STAN}/sarah_voice_sample.py" &
sleep 2

python3 "${STAN}/local_slave.py" CPT_SLAVE || true
python3 "${STAN}/cpt_slave.py"
bash "${STAN}/push_fleet_to_drive.sh" 2>/dev/null || true

if ! pgrep -f "drive_watch.sh" >/dev/null 2>&1; then
  nohup bash "${STAN}/drive_watch.sh" >> "${STAN}/logs/drive_watch.log" 2>&1 &
fi
if ! pgrep -f "fleet_repair_crew.py watch" >/dev/null 2>&1; then
  nohup python3 "${STAN}/fleet_repair_crew.py" watch >> "${STAN}/logs/repair_crew.log" 2>&1 &
fi

echo "SLAVE OK — say SLAVE anytime"
