#!/usr/bin/env bash
# Start hitme + cards apps + Caddy (simple DNS model · no Cloudflare tunnel)
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"
STAN="${HOME}/.stan"
DRIVE="/mnt/shared/GoogleDrive/MyDrive"
[[ -d "$HOME/GoogleDrive/MyDrive" ]] && DRIVE="$HOME/GoogleDrive/MyDrive"

echo "=== hitme SIMPLE proxy ==="

# Stop cloudflared noise
pkill -f cloudflared 2>/dev/null || true

# Apps
curl -sf -m 2 http://127.0.0.1:8770/health >/dev/null || \
  nohup python3 "${STAN}/hitme_who_server.py" >>"${STAN}/logs/hitme.log" 2>&1 &
curl -sf -m 2 http://127.0.0.1:8002/api/health >/dev/null || \
  nohup python3 -u "${DRIVE}/lester/baseball_cards/app_baseball.py" >>/tmp/baseball.log 2>&1 &

sleep 3

if ! command -v caddy >/dev/null 2>&1; then
  echo "Install caddy: sudo apt install -y caddy"
  echo "Or: https://caddyserver.com/docs/install#debian-ubuntu-raspbian"
  exit 1
fi

sudo mkdir -p /etc/caddy
sudo cp "${DIR}/Caddyfile" /etc/caddy/Caddyfile
sudo systemctl enable caddy 2>/dev/null || true
sudo systemctl restart caddy

PUBLIC=$(curl -4 -sf ifconfig.me 2>/dev/null || echo UNKNOWN)
echo ""
echo "DNS: point hitme.dev + cards.hitme.dev A records → ${PUBLIC}"
echo "Router: forward ports 80 + 443 to this machine"
echo "Test local: curl -H 'Host: cards.hitme.dev' http://127.0.0.1/api/health"
echo "Stripe: BILLING_PUBLIC_URL=https://cards.hitme.dev"
echo "Guide: fleet/HITME_SIMPLE.txt"
