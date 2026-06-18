#!/usr/bin/env bash
# Team project backup → Google Drive drop_pile/backups/
# Run on any CAPTN box after major work or before risky changes.
set -euo pipefail

STAMP="${1:-$(date +%Y%m%d_%H%M)}"
BACKUP_NAME="team_project_${STAMP}"
DRIVE="/mnt/shared/GoogleDrive/MyDrive"
DEST="${DRIVE}/drop_pile/backups/${BACKUP_NAME}"
HOST="$(hostname -s 2>/dev/null || echo unknown)"

mkdir -p "${DEST}"

copy_tree() {
  local src="$1" dst="$2"
  shift 2
  local skip_logs=0
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --exclude) [[ "$2" == "*.log" ]] && skip_logs=1; shift 2 ;;
      *) shift ;;
    esac
  done
  [[ -d "${src}" ]] || return 0
  mkdir -p "${dst}"
  if command -v rsync >/dev/null 2>&1; then
    rsync -a --exclude='*.log' --exclude='*.pid' --exclude='__pycache__/' "${src}/" "${dst}/"
  else
    find "${src}" -type f ! -name '*.gdoc' -print0 2>/dev/null | while IFS= read -r -d '' f; do
      rel="${f#${src}/}"
      mkdir -p "${dst}/$(dirname "${rel}")"
      cp -a "${f}" "${dst}/${rel}" 2>/dev/null || true
    done
    find "${src}" -mindepth 1 -type d -print0 2>/dev/null | while IFS= read -r -d '' d; do
      rel="${d#${src}/}"
      mkdir -p "${dst}/${rel}"
    done
    if [[ "${skip_logs}" -eq 1 ]]; then
      find "${dst}" -name '*.log' -delete 2>/dev/null || true
      find "${dst}" -name '*.pid' -delete 2>/dev/null || true
    fi
  fi
}

# --- local CB2 (or whatever box runs this) ---
copy_tree "${HOME}/.stan" "${DEST}/local/stan" \
  --exclude '*.log' --exclude '*.pid' --exclude 'screen/' --exclude '__pycache__/'

copy_tree "${HOME}/.cursor/skills-cursor" "${DEST}/local/cursor/skills-cursor"
copy_tree "${HOME}/.cursor/projects/home-bking17383/agent-transcripts" \
  "${DEST}/local/cursor/agent-transcripts"

for f in statusline.sh argv.json agent-cli-state.json; do
  [[ -f "${HOME}/.cursor/${f}" ]] && cp "${HOME}/.cursor/${f}" "${DEST}/local/cursor/" 2>/dev/null || true
done
[[ -f "${HOME}/.cursor/cli-config.json" ]] && cp "${HOME}/.cursor/cli-config.json" "${DEST}/local/cursor/" 2>/dev/null || true

copy_tree "${HOME}/lester" "${DEST}/local/lester"
copy_tree "${HOME}/Applications/cursor" "${DEST}/local/applications/cursor" 2>/dev/null || true

# secrets: copy but flag in manifest (needed to restore tunnels)
if [[ -f "${HOME}/.stan/cloudflare.env" ]]; then
  mkdir -p "${DEST}/local/secrets"
  cp "${HOME}/.stan/cloudflare.env" "${DEST}/local/secrets/cloudflare.env"
fi

# --- Drive snapshots (point-in-time even though live copies exist) ---
copy_tree "${DRIVE}/fleet" "${DEST}/drive/fleet"
copy_tree "${DRIVE}/lester" "${DEST}/drive/lester"
copy_tree "${DRIVE}/phone" "${DEST}/drive/phone"
copy_tree "${DRIVE}/drop_pile/to_puppy" "${DEST}/drive/drop_pile/to_puppy"
copy_tree "${DRIVE}/drop_pile/to_cursor" "${DEST}/drive/drop_pile/to_cursor"
copy_tree "${DRIVE}/drop_pile/to_lester" "${DEST}/drive/drop_pile/to_lester"
copy_tree "${DRIVE}/drop_pile/from_lester" "${DEST}/drive/drop_pile/from_lester"
copy_tree "${DRIVE}/drop_pile/from_puppy" "${DEST}/drive/drop_pile/from_puppy"
copy_tree "${DRIVE}/drop_pile/from_brian" "${DEST}/drive/drop_pile/from_brian"

# queue + bus state
mkdir -p "${DEST}/drive/fleet/bus"
for f in brian_queue.json mac_inbox.txt mac_outbox.txt brian_says.txt; do
  [[ -f "${DRIVE}/fleet/bus/${f}" ]] && cp "${DRIVE}/fleet/bus/${f}" "${DEST}/drive/fleet/bus/" 2>/dev/null || true
done

# --- manifest ---
FILE_COUNT=$(find "${DEST}" -type f | wc -l | tr -d ' ')
TOTAL_KB=$(du -sk "${DEST}" | cut -f1)

cat > "${DEST}/MANIFEST.txt" <<EOF
TEAM PROJECT BACKUP
===================
Created: $(date -Iseconds)
Host: ${HOST} (${HOSTNAME})
Path: drop_pile/backups/${BACKUP_NAME}/
Files: ${FILE_COUNT}
Size: ${TOTAL_KB} KB

Contains:
  local/stan/          mesh_radio, scripts, handoff (no logs)
  local/cursor/        skills, agent transcripts (~50h sessions)
  local/lester/        jailbreak code on this box
  local/secrets/       cloudflare.env — RESTORE LOCALLY ONLY
  drive/fleet/         fleet docs snapshot
  drive/lester/        slave configs snapshot
  drive/phone/         phone lane docs snapshot
  drive/drop_pile/     orders + acks snapshot
  drive/fleet/bus/     queue + inbox snapshot

Restore: TEAM_RESTORE_AFTER_LOSS.md in this folder
Isolation law: LINKAGE_ISOLATION_LAW.md in this folder
EOF

echo "BACKUP_OK ${DEST} files=${FILE_COUNT} kb=${TOTAL_KB}"
