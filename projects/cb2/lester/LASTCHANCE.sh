#!/usr/bin/env bash
# PUPPY LAST CHANCE — one script · Drive only · 2026-06-16
set -euo pipefail
D=""
for p in ~/GoogleDrive/MyDrive /mnt/shared/GoogleDrive/MyDrive /mnt/home/google_drive/MyDrive; do
  [[ -d "$p/fleet/bus" ]] && D="$p" && break
done
if [[ -z "$D" ]]; then
  echo "FAIL: open Files → Google Drive · wait · run again"
  exit 1
fi
if [[ -f "$D/lester/NEW_PUPPY_BOOT.sh" ]]; then
  bash "$D/lester/NEW_PUPPY_BOOT.sh" && exit 0
fi
H=$(hostname 2>/dev/null || echo puppy64)
IP=$(hostname -I 2>/dev/null | awk '{print $1}')
IP=${IP:-unknown}
T=$(date -Iseconds 2>/dev/null || date)
cat >"$D/fleet/bus/puppy_outbox.txt" <<EOF
PUPPY CHECKIN — ${H} — ${IP} — ${T}
hostname: ${H}
status: lastchance · Drive post
EOF
echo "OK — wrote ${D}/fleet/bus/puppy_outbox.txt"
cat "$D/fleet/bus/puppy_outbox.txt"
