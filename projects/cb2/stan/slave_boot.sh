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

bash "${STAN}/daddy_background.sh"

python3 "${STAN}/local_slave.py" CPT_SLAVE || true
python3 "${STAN}/cpt_slave.py"
bash "${STAN}/push_fleet_to_drive.sh" 2>/dev/null || true

echo "SLAVE OK — bg watch running · say SLAVE anytime"
