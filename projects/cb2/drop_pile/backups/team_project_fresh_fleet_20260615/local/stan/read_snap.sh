#!/usr/bin/env bash
# Read newest screenshot Brian dropped on Drive (Chrome OS snap → Drive folder)
set -euo pipefail
SNAP_DIR="${HOME}/GoogleDrive/MyDrive/drop_pile/from_brian/snaps"
[[ -d /mnt/shared/GoogleDrive/MyDrive/drop_pile/from_brian/snaps ]] && \
  SNAP_DIR="/mnt/shared/GoogleDrive/MyDrive/drop_pile/from_brian/snaps"
OUT="${HOME}/.stan/screen/latest.png"
mkdir -p "${HOME}/.stan/screen" "$SNAP_DIR"

NEWEST="$(find "$SNAP_DIR" -maxdepth 1 -type f \( -iname '*.png' -o -iname '*.jpg' -o -iname '*.webp' \) -printf '%T@ %p\n' 2>/dev/null | sort -rn | head -1 | cut -d' ' -f2-)"
if [[ -z "${NEWEST:-}" ]]; then
  echo "NO SNAP — drop a screenshot in Drive: drop_pile/from_brian/snaps/" >&2
  exit 1
fi
cp -f "$NEWEST" "$OUT"
echo "$OUT"
echo "from: $NEWEST"
echo "bytes: $(wc -c < "$OUT")"