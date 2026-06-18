#!/usr/bin/env bash
# Sarah links — delegates to url_keeper (single tunnel owner)
set -uo pipefail
STAN="${HOME}/.stan"
LOG="${STAN}/logs/sarah_watch.log"
for DRIVE in /mnt/shared/GoogleDrive/MyDrive "$HOME/GoogleDrive/MyDrive"; do
  [[ -d "$DRIVE/fleet" ]] && break
done

log() { echo "$(date -Iseconds) $*" >>"$LOG"; }

bash "${STAN}/url_keeper.sh" >>"$LOG" 2>&1 || log "url_keeper failed"

LIVE="${DRIVE}/fleet/LIVE_URL.txt"
if [[ -f "$LIVE" ]] && grep -q "Status: AWAKE" "$LIVE"; then
  URL="$(grep -oE 'https://[a-z0-9-]+\.trycloudflare\.com' "$LIVE" | head -1 || true)"
  if [[ -z "$URL" ]] && grep -q 'https://hitme.dev' "$LIVE"; then
    URL="https://hitme.dev"
  fi
  if [[ -n "$URL" ]]; then
    cat >"${DRIVE}/fleet/SARAH_TEST_URL.txt" <<EOF
SARAH LINKS — $(date -Iseconds) · url_keeper OK

Seminary app (Sarah asked for this):
  ${URL}/seminary-app

Sarah test home:
  ${URL}/s

Handoff (Brian shows phone):
  ${URL}/handoff

DIRT STRONG (buddies):
  ${URL}/dirt-strong

Sell sheet (cards — not liquid):
  ${URL}/sell

Same wifi: http://100.115.92.26:8770/seminary-app
EOF
    log "OK $URL"
    exit 0
  fi
fi
log "FAIL — see fleet/LIVE_URL.txt"
