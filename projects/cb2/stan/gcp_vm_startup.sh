#!/bin/bash
# First-boot on fleet-net GCP VM — logs: /var/log/fleet-net-startup.log
set -euo pipefail
exec > /var/log/fleet-net-startup.log 2>&1
echo "=== fleet-net startup $(date -Iseconds) ==="

export DEBIAN_FRONTEND=noninteractive
apt-get update -y
apt-get install -y python3 python3-pip python3-venv curl ca-certificates jq \
  espeak-ng ffmpeg unzip

curl -fsSL -o /usr/local/bin/cloudflared \
  https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64
chmod +x /usr/local/bin/cloudflared

python3 -m pip install --break-system-packages flask boto3 requests 2>/dev/null \
  || python3 -m pip install flask boto3 requests

id fleet 2>/dev/null || useradd -m -s /bin/bash fleet
mkdir -p /home/fleet/.stan/logs /home/fleet/.cloudflared /mnt/shared/GoogleDrive/MyDrive

MD="http://metadata.google.internal/computeMetadata/v1/instance/attributes"
mget() { curl -sf -H "Metadata-Flavor: Google" "${MD}/$1" || true; }

BUCKET="$(mget bootstrap_bucket)"
TOKEN="$(mget cloudflare_tunnel_token)"
TARBALL="$(mget bootstrap_object)"

if [[ -n "${BUCKET}" && -n "${TARBALL}" ]]; then
  curl -fsSL -o /tmp/fleet-bootstrap.tar.gz \
    "https://storage.googleapis.com/${BUCKET}/${TARBALL}" \
    || gsutil cp "gs://${BUCKET}/${TARBALL}" /tmp/fleet-bootstrap.tar.gz
  tar xzf /tmp/fleet-bootstrap.tar.gz -C /home/fleet/
fi

chown -R fleet:fleet /home/fleet

if [[ -n "${TOKEN}" ]]; then
  install -d -o fleet -g fleet /home/fleet/.cloudflared
  printf "CLOUDFLARE_TUNNEL_TOKEN='%s'\n" "${TOKEN}" > /home/fleet/.stan/cloudflare.env
  chown fleet:fleet /home/fleet/.stan/cloudflare.env
  chmod 600 /home/fleet/.stan/cloudflare.env
fi

cat > /etc/systemd/system/cloudflared-fleet.service <<'UNIT'
[Unit]
Description=Cloudflare tunnel — hitme.dev
After=network-online.target
Wants=network-online.target

[Service]
User=fleet
Environment=HOME=/home/fleet
WorkingDirectory=/home/fleet
EnvironmentFile=/home/fleet/.stan/cloudflare.env
ExecStart=/bin/bash -c 'source /home/fleet/.stan/cloudflare.env && exec /usr/local/bin/cloudflared tunnel run --token "$CLOUDFLARE_TUNNEL_TOKEN"'
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
UNIT

cat > /etc/systemd/system/fleet-hitme.service <<'UNIT'
[Unit]
Description=Fleet who server :8770
After=network-online.target cloudflared-fleet.service
Wants=network-online.target

[Service]
User=fleet
Environment=HOME=/home/fleet
WorkingDirectory=/home/fleet/.stan
ExecStart=/usr/bin/python3 /home/fleet/.stan/hitme_who_server.py
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
UNIT

cat > /etc/systemd/system/fleet-background.service <<'UNIT'
[Unit]
Description=Fleet background watchers
After=fleet-hitme.service

[Service]
User=fleet
Environment=HOME=/home/fleet
WorkingDirectory=/home/fleet/.stan
ExecStart=/bin/bash /home/fleet/.stan/daddy_background.sh
RemainAfterExit=yes
Type=oneshot

[Install]
WantedBy=multi-user.target
UNIT

systemctl daemon-reload
systemctl enable cloudflared-fleet fleet-hitme fleet-background
systemctl start cloudflared-fleet fleet-hitme
systemctl start fleet-background || true

echo "=== fleet-net startup done $(date -Iseconds) ==="
