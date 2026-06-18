#!/usr/bin/env bash
# AWS lane boot — run after Brian says AWS KEYS IN or keys land
set -euo pipefail
STAN="${HOME}/.stan"
BUS="${HOME}/.stan/fleet_bus"
mkdir -p "${STAN}/logs" "${BUS}/drop_pile/from_aws" "${BUS}/fleet/bus"

if [[ ! -f "${STAN}/aws_sandbox.env" ]]; then
  python3 "${STAN}/vault_keeper.py" pull aws 2>/dev/null || true
fi
if [[ ! -f "${STAN}/aws_sandbox.env" ]]; then
  bash "${STAN}/keys_from_lester.sh" 2>/dev/null || true
  python3 "${STAN}/aws_keys_pull.py" 2>/dev/null || true
fi

if [[ ! -f "${STAN}/aws_sandbox.env" ]]; then
  echo "WAIT — no ~/.stan/aws_sandbox.env yet. Brian: AWS KEYS IN when lester_keys on Drive."
  echo "WAIT" > "${BUS}/fleet/bus/AWS_STATUS.txt"
  exit 0
fi

pip3 install --user boto3 botocore 2>/dev/null || pip3 install boto3 botocore
python3 "${STAN}/aws_sandbox_probe.py" && python3 "${STAN}/aws_lane.py" greet

echo "AWS lane ready — talk: python3 ~/.stan/aws_lane.py talk \"your message\""
echo "Report: fleet/bus/AWS_PROBE_REPORT.txt · fleet/bus/AWS_STATUS.txt"
