#!/usr/bin/env bash
# MESH RADIO — phone extension on :8765 + optional scanner
set -euo pipefail
LOG="${HOME}/.stan/mesh_radio.log"
SCAN_LOG="${HOME}/.stan/radio_scanner.log"

pkill -f "mesh_radio.py" 2>/dev/null || true
pkill -f "camera_sink.py" 2>/dev/null || true
pkill -f "transcript_sink.py" 2>/dev/null || true
sleep 0.5

nohup python3 "${HOME}/.stan/mesh_radio.py" >>"$LOG" 2>&1 &
if ! pgrep -f "radio_scanner.py" >/dev/null 2>&1; then
  nohup python3 "${HOME}/.stan/radio_scanner.py" >>"$SCAN_LOG" 2>&1 &
fi

echo "MESH RADIO"
echo "  phone:  http://100.115.92.26:8765"
echo "  desk:   http://127.0.0.1:8765/desk"
echo "  status: http://127.0.0.1:8765/status"
echo "  log:    $LOG"
