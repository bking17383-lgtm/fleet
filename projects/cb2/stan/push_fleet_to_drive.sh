#!/usr/bin/env bash
# Sync local bus ↔ Drive when fuse is live
set -euo pipefail
STAN="${HOME}/.stan"
python3 -c "from bus_lane import sync_to_drive, is_drive_live; print('synced' if sync_to_drive() else 'no drive')" 2>/dev/null || echo "Drive not mounted"
python3 "${STAN}/cpt_slave.py" 2>/dev/null || true
