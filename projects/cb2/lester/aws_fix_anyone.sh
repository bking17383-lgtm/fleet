#!/usr/bin/env bash
# AWS FIX — run on ANY fleet box (NET · STUDIO · CPT · puppy)
# Posts YES/NO to bus only · secrets stay local chmod 600
set -euo pipefail

STAN="${HOME}/.stan"
BUS="${HOME}/GoogleDrive/MyDrive"
[[ -d "/mnt/shared/GoogleDrive/MyDrive" ]] && BUS="/mnt/shared/GoogleDrive/MyDrive"
NOW="$(date -Iseconds)"
HOST="$(hostname)"

mkdir -p "${STAN}/logs" "${STAN}/local_inbox"

_log() { echo "[${NOW}] ${HOST} aws_fix_anyone: $*" | tee -a "${STAN}/logs/aws_fix_anyone.log"; }

if [[ ! -d "${BUS}/fleet" ]]; then
  _log "FAIL no Drive fleet/ — mount Drive first"
  echo "NO_DRIVE" > "${STAN}/fleet_bus/fleet/bus/AWS_STATUS.txt" 2>/dev/null || true
  exit 2
fi

# Ensure stan scripts exist (copy minimal from CB2 push if missing)
for f in aws_keys_pull.py aws_sandbox_probe.py aws_lane.py aws_ready.sh; do
  if [[ ! -f "${STAN}/${f}" ]] && [[ -f "${BUS}/lester/${f}" ]]; then
    cp "${BUS}/lester/${f}" "${STAN}/${f}" 2>/dev/null || true
  fi
done

_log "pull keys"
python3 "${STAN}/aws_keys_pull.py" 2>/dev/null || {
  _log "pull failed — need lester/lester_keys.md AKIA lines or ~/.stan/aws_key_drop.txt"
  printf 'AWS_STATUS — %s\nok=WAIT\nhost=%s\nfrom=aws_fix_anyone\nreason=no_keys_local\n' "${NOW}" "${HOST}" \
    > "${BUS}/fleet/bus/AWS_STATUS.txt"
  exit 1
}

_log "probe"
if [[ -x "${STAN}/aws_ready.sh" ]]; then
  bash "${STAN}/aws_ready.sh" || true
else
  pip3 install --user boto3 2>/dev/null || true
  python3 "${STAN}/aws_sandbox_probe.py" 2>/dev/null || true
fi

# Bus line for fleet roll call (no secrets)
PROBE="${BUS}/fleet/bus/AWS_PROBE_REPORT.txt"
STATUS="${BUS}/fleet/bus/AWS_STATUS.txt"
if grep -q SANDBOX_OK "${PROBE}" 2>/dev/null; then
  OK="SANDBOX_OK"
else
  OK="WAIT"
fi

printf 'AWS_STATUS — %s\nok=%s\nhost=%s\nfrom=aws_fix_anyone\n' "${NOW}" "${OK}" "${HOST}" > "${STATUS}"
_log "done ok=${OK} → ${STATUS}"

# Optional outbox ping by role
if [[ "${HOST}" == *puppy* ]]; then
  echo "NET aws-fix — ${HOST} — ${OK} — ${NOW}" >> "${BUS}/fleet/bus/puppy_outbox.txt"
elif [[ -f "${BUS}/fleet/bus/uncle_to_cpt.txt" ]]; then
  echo "aws_fix — ${OK} — ${NOW}" >> "${BUS}/fleet/bus/uncle_to_cpt.txt"
fi

echo "AWS FIX ${OK} — report on Drive fleet/bus/AWS_STATUS.txt"
