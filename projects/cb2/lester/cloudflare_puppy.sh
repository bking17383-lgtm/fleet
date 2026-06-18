#!/usr/bin/env bash
# puppy64: app + NAMED Cloudflare tunnel → stable HTTPS ($0/mo)
# Quick trycloudflare URLs ROTATE — not Play Store safe.
set -euo pipefail
STAN="${HOME}/.stan"
for DRIVE in /mnt/home/google_drive/MyDrive "${HOME}/GoogleDrive/MyDrive" /mnt/shared/GoogleDrive/MyDrive; do
  [[ -d "$DRIVE" ]] && break
done
[[ -d "$DRIVE" ]] || { echo "Drive not mounted"; exit 1; }

ENV_FILE="${STAN}/cloudflare.env"
[[ -f "${STAN}/groq.env" ]] && ENV_FILE="${STAN}/groq.env"
CF="${CLOUDFLARED:-${STAN}/cloudflared}"
PORT="${PUPPY_APP_PORT:-5000}"
APP="${PUPPY_APP:-slicer}"
LOG_CF="${STAN}/cloudflare_puppy.log"
STABLE_FILE="${DRIVE}/fleet/STABLE_PUBLIC_URL.txt"
PHONE_FILE="${DRIVE}/fleet/BRIAN_PHONE.txt"
TESTER_FILE="${DRIVE}/fleet/PLAY_TESTER_URL.txt"
OUTBOX="${DRIVE}/fleet/bus/puppy_outbox.txt"

[[ -f "$ENV_FILE" ]] && set -a && source "$ENV_FILE" && set +a

if [[ -z "${CLOUDFLARE_TUNNEL_TOKEN:-}" ]]; then
  echo "ERROR: CLOUDFLARE_TUNNEL_TOKEN missing in ~/.stan/cloudflare.env or groq.env"
  echo "Read: fleet/CLOUDFLARE_PASTE.txt + lester/lester_keys.md"
  exit 1
fi

if [[ -z "${CLOUDFLARE_PUBLIC_URL:-}" ]]; then
  echo "ERROR: CLOUDFLARE_PUBLIC_URL missing — fixed https URL from Cloudflare dashboard"
  echo "Dashboard → Tunnels → Public Hostname → copy https://yoursub.domain"
  exit 1
fi

if [[ ! -x "$CF" ]]; then
  mkdir -p "$STAN"
  curl -sL -o "$CF" https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64
  chmod +x "$CF"
fi

case "$APP" in
  slicer)
    bash "${DRIVE}/lester/start_slicer_host.sh"
    ;;
  baseball)
    PORT=8002
    bash "${DRIVE}/lester/START_BASEBALL_ON_PUPPY.sh" || true
    ;;
  *)
    echo "WARN: unknown PUPPY_APP=$APP — assuming backend already on :$PORT"
    ;;
esac

HEALTH_PATH="${PUPPY_HEALTH_PATH:-/api/status}"
if [[ "$APP" == "baseball" ]]; then HEALTH_PATH="/api/health"; fi
for _ in $(seq 1 25); do
  curl -sf "http://127.0.0.1:${PORT}${HEALTH_PATH}" >/dev/null && break
  sleep 1
done
curl -sf "http://127.0.0.1:${PORT}${HEALTH_PATH}" >/dev/null || {
  echo "ERROR: app not healthy on :$PORT"
  exit 1
}

pkill -f "cloudflared tunnel run" 2>/dev/null || true
sleep 1
: >"$LOG_CF"
nohup "$CF" tunnel run --token "$CLOUDFLARE_TUNNEL_TOKEN" >>"$LOG_CF" 2>&1 &
echo $! >"${STAN}/cloudflare_puppy.pid"
sleep 3

PUBLIC="${CLOUDFLARE_PUBLIC_URL}"
TS="$(date -Iseconds 2>/dev/null || date)"

cat >"$STABLE_FILE" <<EOF
# Stable public URL — Play Store + 12 testers
# Named Cloudflare tunnel on puppy64. Does NOT rotate on reboot.
Updated: $TS
Host: $(hostname)
App: $APP port $PORT

PUBLIC_URL=$PUBLIC

Play internal test: use this URL for TWA manifest + privacy policy + tester link.
EOF

cat >"$TESTER_FILE" <<EOF
Send testers this link (LTE OK):

$PUBLIC

Play Console: Internal testing → add 12 emails → they install from Play link.
App opens this URL (TWA). Server must stay up on puppy64 (plugged in).
EOF

{
  echo ""
  echo "# puppy64 stable URL $TS"
  echo "PUBLIC: $PUBLIC"
  echo "mode: named_tunnel"
  echo "app: $APP"
  echo "port: $PORT"
} >>"$PHONE_FILE"

{
  echo ""
  echo "--- from: puppy | stable-url | $TS ---"
  echo "hostname: $(hostname)"
  echo "public: $PUBLIC"
  echo "mode: named_tunnel"
  echo "app: $APP"
  echo "status: RUNNING"
} >>"$OUTBOX"

echo "STABLE URL: $PUBLIC"
echo "Wrote: $STABLE_FILE $TESTER_FILE"
