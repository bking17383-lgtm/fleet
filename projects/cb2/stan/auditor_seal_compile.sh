#!/usr/bin/env bash
# Seal + compile auditor packet — NO READ of sealed proposals
set -euo pipefail
for DRIVE in /mnt/shared/GoogleDrive/MyDrive "$HOME/GoogleDrive/MyDrive"; do
  [[ -d "$DRIVE/fleet" ]] && break
done
SEALED="${DRIVE}/drop_pile/auditor_inbox/SEALED"
OUT="${DRIVE}/drop_pile/auditor_inbox/COMPILE"
mkdir -p "${SEALED}" "${OUT}"

# Seal patterns from args · default bigbutt + lickface
PATTERNS=("${@:-}")
if [[ ${#PATTERNS[@]} -eq 0 ]]; then
  PATTERNS=(bigbutt lickface)
fi

seal_pattern() {
  local pat="$1"
  find "${DRIVE}" -maxdepth 12 -type f -iname "*${pat}*" 2>/dev/null \
    ! -path '*/drop_pile/auditor_inbox/SEALED/*' \
    ! -path '*/drop_pile/auditor_inbox/COMPILE/*' \
    ! -path '*/fleet/bus/*_SEALED.txt' \
    ! -path '*/fleet/AUDITOR_*' | while read -r src; do
    base="$(basename "$src")"
    dest="${SEALED}/${base}"
    cp -f "$src" "${dest}"
    echo "sealed: ${base} · bytes=$(wc -c <"${dest}" | tr -d ' ') · sha=$(sha256sum "${dest}" | awk '{print $1}')"
  done
}

for pat in "${PATTERNS[@]}"; do
  seal_pattern "${pat}"
done

# Open packet (Daddy/Bunny may read)
mkdir -p "${OUT}/fleet" "${OUT}/bunny"
for f in FARTHEAD.txt BUDDY_POISON.txt FRESH_CURSOR_BOOT.txt DO_THIS_NOW.txt CREDIT_CHECK.txt BRIAN_NORTH_STAR.txt; do
  [[ -f "${DRIVE}/fleet/${f}" ]] && cp -f "${DRIVE}/fleet/${f}" "${OUT}/fleet/"
done
[[ -f "${DRIVE}/fleet/indie_loop/TO_BUNNY.txt" ]] && cp -f "${DRIVE}/fleet/indie_loop/TO_BUNNY.txt" "${OUT}/bunny/"
[[ -f "${DRIVE}/fleet/PROJECTS_BUNNY.txt" ]] && cp -f "${DRIVE}/fleet/PROJECTS_BUNNY.txt" "${OUT}/bunny/"

NOW="$(date -Iseconds)"
MANIFEST="${OUT}/MANIFEST.txt"
{
  echo "AUDITOR COMPILE — ${NOW}"
  echo "sealed_dir: drop_pile/auditor_inbox/SEALED/ (Fresh Cursor ONLY · Daddy/Bunny do not read)"
  echo "open_dir:   drop_pile/auditor_inbox/COMPILE/ (fleet+bunny context)"
  echo "--- sealed files (name · bytes · sha256) ---"
  for s in "${SEALED}"/*; do
    [[ -f "$s" ]] || continue
    echo "$(basename "$s") · $(wc -c <"$s" | tr -d ' ') · $(sha256sum "$s" | awk '{print $1}')"
  done
  echo "--- open files ---"
  find "${OUT}" -type f ! -name MANIFEST.txt | sed "s|${OUT}/||"
} > "${MANIFEST}"

echo "OK — ${MANIFEST}"
