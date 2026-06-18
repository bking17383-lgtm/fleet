#!/usr/bin/env bash
# Terminal 2 — CPT lab auto · close this when /lab works without manual check lab
set -euo pipefail
STAN="${HOME}/.stan"
LOG="${STAN}/logs/cpt_lab_auto.log"
mkdir -p "${LOG%/*}"
if pgrep -f "cpt_lab_auto.py watch" >/dev/null 2>&1; then
  echo "CPT LAB AUTO already running — tail -f ${LOG}"
  tail -f "${LOG}"
  exit 0
fi
echo "CPT LAB AUTO — $(date -Iseconds) — watching BRIAN_LAST_POST lane=cpt"
echo "Type at http://127.0.0.1:8770/lab — reply on same page"
echo "Log: ${LOG}"
exec python3 "${STAN}/cpt_lab_auto.py" watch "${LAB_AUTO_SEC:-8}"
