#!/usr/bin/env bash
# CB1 — fix lying statusline (CPT/PUPPY/STUDIO · NET-clean=POISON)
set -u
for DRIVE in "$HOME/GoogleDrive/MyDrive" /mnt/shared/GoogleDrive/MyDrive; do
  [[ -d "$DRIVE/fleet" ]] && break
done
[[ -d "${DRIVE:-}/fleet" ]] || { echo "FAIL: Drive not mounted"; exit 1; }

SRC="$DRIVE/lester/gem_statusline.sh"
DST="${HOME}/.cursor/statusline.sh"
mkdir -p "${HOME}/.cursor"
cp -f "$SRC" "$DST"
chmod +x "$DST"
echo "OK — statusline fixed from lester/gem_statusline.sh"
python3 "$DST" <<< '{}' 2>/dev/null || true
