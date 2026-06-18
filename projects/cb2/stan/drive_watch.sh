#!/usr/bin/env bash
# Poll Drive fuse; sync when it returns.
set -euo pipefail
STAN="${HOME}/.stan"
INTERVAL="${DRIVE_WATCH_SEC:-30}"

while true; do
  bash "${STAN}/push_fleet_to_drive.sh" 2>/dev/null || true
  sleep "${INTERVAL}"
done
