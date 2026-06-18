#!/usr/bin/env bash
# HTTPS link for Sarah's phone — quick tunnel WITHOUT named config (avoids 404 catch-all)
set -euo pipefail
STAN="${HOME}/.stan"
CF="${STAN}/cloudflared"
PORT=8770
LOG="${STAN}/logs/sarah_tunnel_live.log"
EMPTY=/tmp/cf-empty.yml
DRIVE="/mnt/shared/GoogleDrive/MyDrive"
[[ -d "$HOME/GoogleDrive/MyDrive" ]] && DRIVE="$HOME/GoogleDrive/MyDrive"
OUT="${DRIVE}/fleet/SARAH_TEST_URL.txt"

echo "tunnel: none" >"$EMPTY"

if ! curl -sf "http://127.0.0.1:${PORT}/health" >/dev/null; then
  nohup python3 "${STAN}/hitme_who_server.py" >>"${STAN}/logs/hitme_who.log" 2>&1 &
  sleep 2
fi

if ! pgrep -f "cloudflared tunnel --config ${EMPTY}" >/dev/null; then
  # Drop quick tunnels that load named config (404 catch-all breaks phone links)
  pkill -f "cloudflared tunnel --protocol http2 --url http://127.0.0.1:${PORT}" 2>/dev/null || true
  pkill -f "cloudflared tunnel --url http://127.0.0.1:${PORT}" 2>/dev/null || true
  sleep 1
  nohup "$CF" tunnel --config "$EMPTY" --url "http://127.0.0.1:${PORT}" >>"$LOG" 2>&1 &
fi

URL=""
for _ in $(seq 1 30); do
  URL="$(grep -oE 'https://[a-z0-9-]+\.trycloudflare\.com' "$LOG" 2>/dev/null | tail -1 || true)"
  if [[ -n "$URL" ]] && curl -sf "${URL}/health" >/dev/null 2>&1; then
    break
  fi
  sleep 1
done

NOW="$(date -Iseconds)"
if [[ -z "$URL" ]]; then
  echo "FAIL — no tunnel URL yet · see $LOG"
  exit 1
fi

LINK="${URL}/s"
HANDOFF="${URL}/handoff"
cat >"$OUT" <<EOF
SARAH LINK — ${NOW}

TEXT HER (line 1 = URL only):
  ${LINK}

BRIAN IN PERSON (no QR-of-QR — open this on YOUR phone, she taps green):
  ${HANDOFF}

Same wifi (if HTTPS fails):
  http://100.115.92.26:8770/handoff

Refresh: bash ~/.stan/sarah_phone_tunnel.sh
EOF

echo "OK ${LINK}"
echo "→ $OUT"
