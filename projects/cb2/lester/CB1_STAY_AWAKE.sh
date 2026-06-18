#!/usr/bin/env bash
# CB1 — keep screen awake while plugged (Uncle Linux · not Gem chat)
set -u
STAN="${HOME}/.stan"
mkdir -p "$STAN/logs"
NOW=$(date -Iseconds 2>/dev/null || date)
LOG="$STAN/logs/cb1_stay_awake.log"

log() { echo "$1" | tee -a "$LOG"; }

log "=== CB1_STAY_AWAKE ${NOW} ==="

if command -v xset >/dev/null 2>&1 && [[ -n "${DISPLAY:-}" ]]; then
  xset s off 2>/dev/null || true
  xset s noblank 2>/dev/null || true
  xset -dpms 2>/dev/null || true
  log "xset: screen blanking off"
else
  log "xset: skip (no DISPLAY — run from Linux desktop session)"
fi

if command -v gsettings >/dev/null 2>&1; then
  gsettings set org.gnome.settings-daemon.plugins.power sleep-inactive-ac-type 'nothing' 2>/dev/null || true
  gsettings set org.gnome.settings-daemon.plugins.power sleep-inactive-battery-type 'nothing' 2>/dev/null || true
  log "gsettings: sleep-inactive= nothing (if GNOME)"
fi

for DRIVE in "$HOME/GoogleDrive/MyDrive" /mnt/shared/GoogleDrive/MyDrive; do
  [[ -d "$DRIVE/fleet" ]] && break
done
if [[ -d "${DRIVE:-}/fleet" ]]; then
  CARD="${DRIVE}/fleet/bus/CB1_POWER_FIX.txt"
  {
    echo "CB1 POWER FIX — ${NOW}"
    echo "from: Uncle Linux on $(hostname -s 2>/dev/null || hostname)"
    echo "fix: xset off · gsettings sleep-inactive-ac-type nothing"
    echo "Brian: Chrome → Settings → Device → Power → While charging: Stay awake"
    echo "Gem: post BUDDY ok on gem_to_cpt when you read this"
  } >"$CARD"
  log "posted ${CARD}"
fi

log "done"
