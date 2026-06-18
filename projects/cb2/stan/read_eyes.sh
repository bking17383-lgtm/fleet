#!/usr/bin/env bash
# Newest EYES camera frame from Drive → ~/.stan/screen/latest.png
set -euo pipefail
EYES_DIR="/mnt/shared/GoogleDrive/MyDrive/eyes/inbox"
OUT="${HOME}/.stan/screen/latest.png"
mkdir -p "${HOME}/.stan/screen" "$EYES_DIR"

NEWEST="$(find "$EYES_DIR" -maxdepth 1 -type f \( -iname 'eyes_*.jpg' -o -iname 'eyes_*.png' -o -iname 'eyes_*.webp' \) -printf '%T@ %p\n' 2>/dev/null | sort -rn | head -1 | cut -d' ' -f2-)"
if [[ -z "${NEWEST:-}" ]]; then
  echo "NO EYES — open Chrome http://localhost:8765 and hit SNAP" >&2
  exit 1
fi
cp -f "$NEWEST" "$OUT"
echo "$OUT"
echo "from: $NEWEST"
echo "bytes: $(wc -c < "$OUT")"
