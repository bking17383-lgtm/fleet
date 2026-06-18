#!/usr/bin/env bash
# CB2: baseball :8002 + Cloudflare (named if token, else quick tunnel)
set -euo pipefail
STAN="${HOME}/.stan"
DRIVE="/mnt/shared/GoogleDrive/MyDrive"
[[ -d "$HOME/GoogleDrive/MyDrive" ]] && DRIVE="$HOME/GoogleDrive/MyDrive"
ENV_FILE="${STAN}/cloudflare.env"
CF="${CLOUDFLARED:-${STAN}/cloudflared}"
APP_DIR="${HOME}/Applications/cursor/baseball_cards"
PORT=8002
LOG_APP="${STAN}/baseball_cb2.log"
LOG_CF="${STAN}/cloudflare_cb2.log"
URL_FILE="${DRIVE}/BRIAN_PHONE.txt"
STRANGER_FILE="${DRIVE}/STRANGER_TESTER_LINK.txt"

[[ -f "$ENV_FILE" ]] && set -a && source "$ENV_FILE" && set +a

mkdir -p "$STAN" "$APP_DIR/data/collx" "$APP_DIR/uploads"

SRC="$DRIVE/lester/baseball_cards"
if [[ -d "$SRC" ]]; then
  cp -f "$SRC"/*.py "$SRC"/*.html "$APP_DIR/" 2>/dev/null || true
  cp -rf "$SRC/data/"* "$APP_DIR/data/" 2>/dev/null || true
fi

if [[ ! -f "$APP_DIR/app_baseball.py" ]]; then
  echo "ERROR: missing app_baseball.py"
  exit 1
fi

if [[ ! -x "$CF" ]]; then
  curl -sL -o "$CF" https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64
  chmod +x "$CF"
fi

python3 -c "import flask" 2>/dev/null || sudo apt-get install -y python3-flask >/dev/null 2>&1

pkill -f "app_baseball.py" 2>/dev/null || true
pkill -f "cloudflared tunnel" 2>/dev/null || true
sleep 2

cd "$APP_DIR"
: >"$LOG_APP"
nohup python3 app_baseball.py >>"$LOG_APP" 2>&1 &
echo $! >"${STAN}/baseball_cb2.pid"

HEALTH_OK=0
for _ in $(seq 1 20); do
  sleep 1
  if curl -sf "http://127.0.0.1:${PORT}/api/health" >/dev/null; then
    HEALTH_OK=1
    break
  fi
done
if [[ "$HEALTH_OK" -ne 1 ]]; then
  echo "ERROR: baseball not up"
  tail -20 "$LOG_APP" 2>/dev/null || true
  exit 1
fi
echo "OK: baseball on port $PORT"

rm -f "$LOG_CF"
MODE="quick_tunnel"
PUBLIC=""

if [[ -n "${CLOUDFLARE_TUNNEL_TOKEN:-}" ]]; then
  MODE="named"
  nohup "$CF" tunnel run --token "$CLOUDFLARE_TUNNEL_TOKEN" >>"$LOG_CF" 2>&1 &
  echo $! >"${STAN}/cloudflare_cb2.pid"
  PUBLIC="${CLOUDFLARE_PUBLIC_URL:-}"
  if [[ -z "$PUBLIC" ]]; then
    echo "Named tunnel started. Set CLOUDFLARE_PUBLIC_URL in ~/.stan/cloudflare.env"
    sleep 3
    tail -5 "$LOG_CF" 2>/dev/null || true
    exit 0
  fi
else
  nohup "$CF" tunnel --protocol http2 --url "http://127.0.0.1:${PORT}" >>"$LOG_CF" 2>&1 &
  echo $! >"${STAN}/cloudflare_cb2.pid"
  for _ in $(seq 1 30); do
    sleep 2
    PUBLIC="$(grep -oE 'https://[a-z0-9-]+\.trycloudflare\.com' "$LOG_CF" 2>/dev/null | head -1 || true)"
    [[ -n "$PUBLIC" ]] && break
  done
fi

if [[ -z "$PUBLIC" ]]; then
  echo "WARN: no public URL yet"
  tail -10 "$LOG_CF" 2>/dev/null || true
  exit 1
fi

cat >"$URL_FILE" <<EOF
For Brian + strangers on LTE - one link:

$PUBLIC

Open in Chrome on Android. CB2 interim host until puppy64 named tunnel.
Updated: $(date -Iseconds) hostname=$(hostname) mode=$MODE
EOF

printf '%s\n' "$PUBLIC" >"$STRANGER_FILE"

{
  echo ""
  echo "# CB2 cloudflare $(date -Iseconds) hostname=$(hostname)"
  echo "status: RUNNING"
  echo "url: $PUBLIC"
  echo "mode: $MODE"
  echo "port: $PORT"
} >>"$DRIVE/puppy_outbox.txt"

echo "PUBLIC URL: $PUBLIC"
echo "Wrote: $URL_FILE"
echo "Screen: bash ~/.stan/screen_capture.sh"
