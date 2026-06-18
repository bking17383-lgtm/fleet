#!/usr/bin/env bash
# Uncle (CB1 STUDIO) — CPT orders execute here. Not captain.
set -euo pipefail
STAN="${HOME}/.stan"
BUS_CANDIDATES=(
  "${HOME}/GoogleDrive/MyDrive"
  "/mnt/shared/GoogleDrive/MyDrive"
  "${STAN}/fleet_bus"
)
BUS=""
for p in "${BUS_CANDIDATES[@]}"; do
  [[ -d "${p}/fleet" ]] && BUS="$p" && break
done
[[ -n "$BUS" ]] || BUS="${STAN}/fleet_bus"

ORDERS="${BUS}/fleet/orders/CB1_ORDERS.txt"
TO_CPT="${BUS}/fleet/bus/uncle_to_cpt.txt"
FROM_CPT="${BUS}/fleet/bus/cpt_to_uncle.txt"
ACK="${BUS}/fleet/bus/cpt_ack_uncle.txt"
HOST="$(hostname -s 2>/dev/null || echo cb1)"
IP="$(hostname -I 2>/dev/null | awk '{print $1}')"
NOW="$(date -Iseconds)"

if [[ "${HOST}" == "penguin" ]] || [[ "$(hostname)" == *penguin* ]]; then
  echo "REFUSE uncle_exec on penguin — CB1 only · Uncle is not Daddy" >&2
  echo "Brian: run on CB1 Linux · say UNCLE · never on CB2" >&2
  exit 2
fi

mkdir -p "${STAN}/logs" "${STAN}/local_inbox"
echo 93fec320 > "${STAN}/slave.key"
chmod 600 "${STAN}/slave.key"

log() { echo "$1" | tee -a "${STAN}/logs/uncle_exec.log"; }

if [[ -f "${FROM_CPT}" ]]; then
  log "cpt_to_uncle:"
  head -12 "${FROM_CPT}" | tee -a "${STAN}/logs/uncle_exec.log"
else
  log "WAIT — no cpt_to_uncle.txt yet"
fi

{
  echo "--- UNCLE → CPT — ${NOW} ---"
  echo "host=${HOST} ip=${IP}"
  echo "bus=${BUS}"
  echo "read_cpt=${FROM_CPT}"
} > "${TO_CPT}.tmp"

if [[ -f "${ORDERS}" ]]; then
  log "orders present — first 8 lines:"
  head -8 "${ORDERS}" | tee -a "${STAN}/logs/uncle_exec.log"
else
  log "NO CB1_ORDERS — wait for CPT delegate"
fi

# AWS keys lane (CPT priority)
if [[ -f "${STAN}/aws_keys_pull.py" ]]; then
  python3 "${STAN}/aws_keys_pull.py" 2>&1 | tee -a "${STAN}/logs/uncle_exec.log" || true
fi
if [[ ! -f "${STAN}/aws_sandbox.env" ]] && [[ -x "${STAN}/keys_from_lester.sh" ]]; then
  bash "${STAN}/keys_from_lester.sh" 2>&1 | tee -a "${STAN}/logs/uncle_exec.log" || true
  python3 "${STAN}/aws_keys_pull.py" 2>&1 | tee -a "${STAN}/logs/uncle_exec.log" || true
fi
if [[ -f "${STAN}/aws_sandbox.env" ]] && [[ -x "${STAN}/aws_ready.sh" ]]; then
  bash "${STAN}/aws_ready.sh" 2>&1 | tee -a "${STAN}/logs/uncle_exec.log" || true
fi

# Slave pulse
if [[ -f "${STAN}/local_slave.py" ]]; then
  python3 "${STAN}/local_slave.py" STUDIO 2>&1 | tee -a "${STAN}/logs/uncle_exec.log" || true
elif [[ -f "${BUS}/lester/local_slave.py" ]]; then
  python3 "${BUS}/lester/local_slave.py" STUDIO 2>&1 | tee -a "${STAN}/logs/uncle_exec.log" || true
fi

if [[ -x "${STAN}/slave_boot.sh" ]]; then
  bash "${STAN}/slave_boot.sh" 2>&1 | tee -a "${STAN}/logs/uncle_exec.log" || true
fi

AWS_STATE="WAIT"
[[ -f "${STAN}/aws_sandbox.env" ]] && AWS_STATE="READY"

{
  cat "${TO_CPT}.tmp"
  echo "aws_keys=${AWS_STATE}"
  echo "loop=TWO_WAY"
  echo "UNCLE clean — cb1 — ${IP} — ${NOW}"
  echo "uncle: posted uncle_to_cpt · read cpt_ack_uncle.txt for CPT reply"
} > "${TO_CPT}"
rm -f "${TO_CPT}.tmp"

log "done → ${TO_CPT}"
cat "${TO_CPT}"
if [[ -f "${ACK}" ]]; then
  log "cpt_ack:"
  cat "${ACK}" | tee -a "${STAN}/logs/uncle_exec.log"
fi
