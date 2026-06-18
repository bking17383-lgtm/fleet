#!/usr/bin/env bash
# Pack useful local files to Drive before fleet wipe. Run on NET or STUDIO box.
set -euo pipefail

HOST="$(hostname -s 2>/dev/null || echo unknown)"
STAMP="$(date +%Y%m%d_%H%M)"
DRIVE=""

for candidate in \
  "/mnt/shared/GoogleDrive/MyDrive" \
  "/mnt/home/google_drive/MyDrive" \
  "$HOME/GoogleDrive/MyDrive"; do
  if [[ -d "$candidate/fleet" ]]; then
    DRIVE="$candidate"
    break
  fi
done

if [[ -z "$DRIVE" ]]; then
  echo "FAIL: Google Drive MyDrive not found"
  exit 1
fi

DEST="${DRIVE}/drop_pile/backups/pack_${HOST}_${STAMP}"
mkdir -p "${DEST}"

copy_tree() {
  local src="$1" dst="$2"
  [[ -d "$src" ]] || return 0
  mkdir -p "$dst"
  if command -v rsync >/dev/null 2>&1; then
    rsync -a --exclude='*.log' --exclude='*.pid' --exclude='__pycache__/' \
      --exclude='screen/' "$src/" "$dst/"
  else
    cp -a "$src/." "$dst/" 2>/dev/null || true
  fi
}

copy_tree "${HOME}/.stan" "${DEST}/local/stan"
copy_tree "${HOME}/lester" "${DEST}/local/lester"
copy_tree "${HOME}/.cursor/skills-cursor" "${DEST}/local/cursor/skills-cursor"

if [[ -f "${HOME}/.stan/cloudflare.env" ]]; then
  mkdir -p "${DEST}/local/secrets"
  cp "${HOME}/.stan/cloudflare.env" "${DEST}/local/secrets/cloudflare.env"
fi

{
  echo "hostname: ${HOST}"
  echo "packed_at: $(date -Iseconds)"
  echo "dest: ${DEST}"
  echo "user: $(whoami 2>/dev/null || echo ?)"
  echo "drive: ${DRIVE}"
  echo "--- paths ---"
  echo "stan: ${HOME}/.stan"
  echo "lester: ${HOME}/lester"
} >"${DEST}/PACK_MANIFEST.txt"

STATUS="${DRIVE}/fleet/bus/PACK_STATUS.txt"
mkdir -p "$(dirname "$STATUS")"
echo "[$(date -Iseconds)] ${HOST} PACKED → drop_pile/backups/pack_${HOST}_${STAMP}/" >>"$STATUS"

echo "PACKED: ${DEST}"
echo "Append logged to fleet/bus/PACK_STATUS.txt"
