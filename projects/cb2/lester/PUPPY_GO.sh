#!/usr/bin/env bash
# Uncle pushed via :8002 — no Drive sync required · run on puppy64 keyboard
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
STAMP="$(date -Iseconds 2>/dev/null || date)"
HOST="$(hostname 2>/dev/null || echo puppy64)"
IP="$(hostname -I 2>/dev/null | tr ' ' '\n' | grep -E '^192\.168\.' | head -1)"
IP="${IP:-$(hostname -I 2>/dev/null | awk '{print $1}')}"
IP="${IP:-unknown}"

REAL=""
for DRIVE in /mnt/shared/GoogleDrive/MyDrive /mnt/home/google_drive/MyDrive "$HOME/GoogleDrive/MyDrive"; do
  if [[ -d "$DRIVE" ]] && [[ -w "$DRIVE" ]]; then
    REAL="$DRIVE"
    break
  fi
done

echo "PUPPY_GO — ${STAMP}"
echo "bundle=${HERE}"
echo "drive=${REAL:-NONE}"

if [[ -n "$REAL" ]]; then
  mkdir -p "$REAL/fleet/bus" "$REAL/lester"
  cp -f "$HERE/FLEET_CHECKIN.txt" "$REAL/fleet/bus/FLEET_CHECKIN.txt"
  cp -f "$HERE/cpt_to_puppy.txt" "$REAL/fleet/bus/cpt_to_puppy.txt"
  cp -f "$HERE/NEW_PUPPY_BOOT.sh" "$REAL/lester/NEW_PUPPY_BOOT.sh"
  chmod +x "$REAL/lester/NEW_PUPPY_BOOT.sh"
  echo "copied 3 files → ${REAL}/fleet/bus + lester/"
  bash "$REAL/lester/NEW_PUPPY_BOOT.sh"
  exit $?
fi

# Drive not mounted — still post honest outbox beside bundle
OUT="$HERE/puppy_outbox.txt"
cat >"$OUT" <<EOF
PUPPY CHECKIN — ${HOST} — ${IP} — ${STAMP}
hostname: ${HOST}
status: PARTIAL · PUPPY_GO ran · Drive not mounted
ports: :8765=DOWN :8766=DOWN :8002=UP(upload_server)
next: open Files app · sync Google Drive · rerun PUPPY_GO.sh
bundle: ${HERE}
EOF
echo "WARN: Drive not mounted — wrote local outbox only:"
cat "$OUT"
echo ""
echo "Fix: Files → Google Drive → wait sync → bash ${HERE}/PUPPY_GO.sh"
exit 1
