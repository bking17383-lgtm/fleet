#!/usr/bin/env bash
# Stand up fleet NET on Google Cloud — e2-standard-2 · uses $300 credit
set -euo pipefail

STAN="${HOME}/.stan"
GCLOUD="${STAN}/gcloud"
for DRIVE in /mnt/shared/GoogleDrive/MyDrive "$HOME/GoogleDrive/MyDrive"; do
  [[ -d "$DRIVE/fleet" ]] && break
done
DRIVE="${DRIVE:-/mnt/shared/GoogleDrive/MyDrive}"
LOG="${STAN}/logs/gcp_net_standup.log"
STATUS="${DRIVE}/fleet/GCP_NET.txt"

mkdir -p "${STAN}/logs" "${DRIVE}/fleet"
exec > >(tee -a "$LOG") 2>&1

log() { echo "$(date -Iseconds) $*"; }

: "${GCP_ZONE:=us-central1-a}"
: "${GCP_INSTANCE:=fleet-net-1}"
: "${GCP_MACHINE:=e2-standard-2}"
: "${GCP_DISK_GB:=50}"
: "${GCP_BOOT_OBJECT:=fleet-bootstrap.tar.gz}"

if ! [[ -x "${GCLOUD}" ]]; then
  log "FAIL: install gcloud first — bash ${STAN}/gcp_install.sh"
  exit 1
fi

ACTIVE="$("${GCLOUD}" auth list --filter=status:ACTIVE --format='value(account)' 2>/dev/null | head -1 || true)"
if [[ -z "${ACTIVE}" ]]; then
  log "NEED LOGIN — run once: ${GCLOUD} auth login"
  cat >"${STATUS}" <<EOF
GCP NET — BLOCKED — $(date -Iseconds)

Need one Google login (2 min · Brian once):
  bash ${STAN}/gcloud auth login

Then Daddy runs:
  bash ${STAN}/gcp_net_standup.sh

Plan: e2-standard-2 · us-central1 · ~\$55-65/mo · \$300 credit ≈ 5 months
EOF
  exit 2
fi

PROJECT="${GCP_PROJECT:-$("${GCLOUD}" config get-value project 2>/dev/null || true)}"
if [[ -z "${PROJECT}" || "${PROJECT}" == "(unset)" ]]; then
  PROJECT="$("${GCLOUD}" projects list --format='value(projectId)' --limit=1 2>/dev/null || true)"
fi
if [[ -z "${PROJECT}" ]]; then
  log "FAIL: set GCP_PROJECT=your-project-id"
  exit 1
fi

"${GCLOUD}" config set project "${PROJECT}" >/dev/null
BUCKET="${GCP_BUCKET:-${PROJECT}-fleet-bootstrap}"

log "project=${PROJECT} zone=${GCP_ZONE} machine=${GCP_MACHINE} account=${ACTIVE}"

log "enable APIs"
"${GCLOUD}" services enable compute.googleapis.com storage.googleapis.com --quiet

log "build bootstrap tarball"
TMP="$(mktemp -d)"
trap 'rm -rf "${TMP}"' EXIT
mkdir -p "${TMP}/pack/.stan"
rsync -a --exclude='logs/*' --exclude='parked' --exclude='__pycache__' \
  "${STAN}/" "${TMP}/pack/.stan/"
[[ -f "${STAN}/cloudflare.env" ]] && cp "${STAN}/cloudflare.env" "${TMP}/pack/.stan/"
tar czf "${TMP}/${GCP_BOOT_OBJECT}" -C "${TMP}/pack" .

log "upload bootstrap → gs://${BUCKET}/${GCP_BOOT_OBJECT}"
if ! "${GCLOUD}" storage buckets describe "gs://${BUCKET}" >/dev/null 2>&1; then
  "${GCLOUD}" storage buckets create "gs://${BUCKET}" --location=us-central1 --uniform-bucket-level-access
fi
"${GCLOUD}" storage cp "${TMP}/${GCP_BOOT_OBJECT}" "gs://${BUCKET}/${GCP_BOOT_OBJECT}"

TOKEN=""
if [[ -f "${STAN}/cloudflare.env" ]]; then
  # shellcheck source=/dev/null
  source "${STAN}/cloudflare.env"
  TOKEN="${CLOUDFLARE_TUNNEL_TOKEN:-}"
fi
[[ -n "${TOKEN}" ]] || { log "FAIL: no CLOUDFLARE_TUNNEL_TOKEN in ${STAN}/cloudflare.env"; exit 1; }

META="bootstrap_bucket=${BUCKET},bootstrap_object=${GCP_BOOT_OBJECT},cloudflare_tunnel_token=${TOKEN}"

if "${GCLOUD}" compute instances describe "${GCP_INSTANCE}" --zone="${GCP_ZONE}" >/dev/null 2>&1; then
  log "instance exists — updating metadata + restart"
  "${GCLOUD}" compute instances add-metadata "${GCP_INSTANCE}" --zone="${GCP_ZONE}" \
    --metadata="${META}"
  "${GCLOUD}" compute instances reset "${GCP_INSTANCE}" --zone="${GCP_ZONE}" --quiet
else
  log "create ${GCP_INSTANCE} (${GCP_MACHINE})"
  "${GCLOUD}" compute instances create "${GCP_INSTANCE}" \
    --zone="${GCP_ZONE}" \
    --machine-type="${GCP_MACHINE}" \
    --boot-disk-size="${GCP_DISK_GB}GB" \
    --boot-disk-type=pd-balanced \
    --image-family=ubuntu-2204-lts \
    --image-project=ubuntu-os-cloud \
    --tags=fleet-net \
    --metadata="${META}" \
    --metadata-from-file=startup-script="${STAN}/gcp_vm_startup.sh" \
    --scopes=storage-ro,logging-write,monitoring-write
fi

IP="$("${GCLOUD}" compute instances describe "${GCP_INSTANCE}" --zone="${GCP_ZONE}" \
  --format='get(networkInterfaces[0].accessConfigs[0].natIP)' 2>/dev/null || echo pending)"

cat >"${STATUS}" <<EOF
GCP NET — PROVISIONED — $(date -Iseconds)

project:  ${PROJECT}
instance: ${GCP_INSTANCE}
zone:     ${GCP_ZONE}
machine:  ${GCP_MACHINE} (2 vCPU · 8 GB)
disk:     ${GCP_DISK_GB} GB
external: ${IP:-booting}

bootstrap: gs://${BUCKET}/${GCP_BOOT_OBJECT}
tunnel:    cloudflared on VM (same hitme.dev token)

Cost: ~\$55-65/mo · \$300 credit ≈ 5 months

NEXT (Daddy when VM health green):
  1. Stop penguin cloudflared (avoid split tunnel)
  2. Verify https://hitme.dev/health from VM
  3. rclone Drive on VM (phase 2)
  4. Penguin = captain only · VM = NET

SSH (debug):
  ${GCLOUD} compute ssh ${GCP_INSTANCE} --zone=${GCP_ZONE}
EOF

log "DONE — see ${STATUS}"
echo "OK — ${GCP_INSTANCE} in ${GCP_ZONE} · ${IP:-booting}"
