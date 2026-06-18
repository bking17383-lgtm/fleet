#!/usr/bin/env bash
# Daddy background — watch/delegate/screen · never block Brian in chat.
set -euo pipefail
STAN="${HOME}/.stan"
LOG="${STAN}/logs"
mkdir -p "${LOG}"

_start() {
  local match="$1"
  local cmd="$2"
  local log="$3"
  if pgrep -f "${match}" >/dev/null 2>&1; then
    return 0
  fi
  nohup bash -c "${cmd}" >> "${log}" 2>&1 &
}

# Thin infra Daddy keeps on CB2 (dashboard + eyes + captain loop)
_start "hitme_who_server.py" "python3 ${STAN}/hitme_who_server.py" "${LOG}/hitme_who.log"
_start "gem_gate_server.py" "python3 ${STAN}/gem_gate_server.py" "${LOG}/gem_gate.log"
_start "screen_watch.py watch" "python3 ${STAN}/screen_watch.py watch 20" "${LOG}/screen_watch.log"
_start "fleet_self_check.py watch" "python3 ${STAN}/fleet_self_check.py watch 25" "${LOG}/fleet_self_check.log"
_start "cpt_autopilot.py watch" "python3 ${STAN}/cpt_autopilot.py watch 25" "${LOG}/cpt_autopilot.log"
_start "brian_router.py watch" "python3 ${STAN}/brian_router.py watch 12" "${LOG}/brian_router.log"
_start "cpt_daddy_ready_loop.py watch" "python3 ${STAN}/cpt_daddy_ready_loop.py watch" "${LOG}/daddy_ready_loop.log"
_start "cpt_lab_auto.py watch" "python3 ${STAN}/cpt_lab_auto.py watch 8" "${LOG}/cpt_lab_auto.log"
_start "picture_inbox_watch.py watch" "python3 ${STAN}/picture_inbox_watch.py watch 12" "${LOG}/picture_inbox_watch.log"
_start "cpt_bunny_watch.sh" "bash ${STAN}/cpt_bunny_watch.sh" "${LOG}/cpt_bunny_watch.log"
_start "drive_watch.sh" "bash ${STAN}/drive_watch.sh" "${LOG}/drive_watch.log"
_start "hitme_always.sh" "bash ${STAN}/hitme_always.sh" "${LOG}/hitme_always.log"
_start "dog_fake_net.py" "python3 ${STAN}/dog_fake_net.py" "${LOG}/dog_fake_net.log"
_start "dog_trust_test.py watch" "python3 ${STAN}/dog_trust_test.py watch 45" "${LOG}/dog_trust_test.log"
_start "alexa_watch.py watch" "REAL_ALEXA=1 python3 ${STAN}/alexa_watch.py watch" "${LOG}/alexa_watch.log"
# repair_crew OFF — delegate all · Puppy/Uncle execute

python3 "${STAN}/screen_watch.py" once >/dev/null 2>&1 || true
python3 "${STAN}/cpt_autopilot.py" once >/dev/null 2>&1 || true

echo "DADDY BACKGROUND OK — screen 20s · delegate default · $(date -Iseconds)"
