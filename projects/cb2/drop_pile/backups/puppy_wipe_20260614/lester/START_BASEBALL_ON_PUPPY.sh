#!/bin/bash
# Run ON puppy64 — install, start baseball, write status back to Drive for penguin.
set -euo pipefail

DRIVE="${HOME}/GoogleDrive/MyDrive"
[[ -d "/mnt/shared/GoogleDrive/MyDrive" ]] && DRIVE="/mnt/shared/GoogleDrive/MyDrive"
[[ -d "${HOME}/.google-drive" ]] && DRIVE="${HOME}/.google-drive"

DIR="$DRIVE/lester/baseball_cards"
STATUS_FILE="$DRIVE/Hello from Puppy.txt"
PORT=8002
HOST="$(hostname 2>/dev/null || echo unknown)"

# Refuse to run on Chromebook Linux — it reports wrong IP and confuses phone testing.
if [[ "$HOST" == "penguin" ]] || ip -4 addr show eth0 2>/dev/null | grep -q "100\.115\."; then
  echo "ERROR: This script must run on PUPPY64, not Chromebook Linux ($HOST)."
  echo "Chromebook cannot serve normal phone Wi-Fi. Go to puppy64 and run there."
  write_status() { :; }
  exit 1
fi

# Prefer real LAN IP (192.168.x.x), not Tailscale/CGNAT 100.x
IP="${PUPPY_IP:-}"
if [[ -z "$IP" ]]; then
  IP="$(hostname -I 2>/dev/null | tr ' ' '\n' | grep -E '^192\.168\.' | head -1)"
fi
if [[ -z "$IP" ]]; then
  IP="$(hostname -I 2>/dev/null | tr ' ' '\n' | grep -Ev '^100\.' | head -1)"
fi
IP="${IP:-192.168.1.4}"

write_status() {
  cat > "$STATUS_FILE" <<EOF
# Puppy status ($(date -Iseconds))

status: $1
ip: ${IP}
port: ${PORT}
url: http://${IP}:${PORT}
hostname: $(hostname 2>/dev/null || echo puppy)

---
$2
EOF
}

if [[ ! -f "$DIR/app_baseball.py" ]]; then
  write_status "FAILED" "Missing $DIR/app_baseball.py — sync Google Drive first."
  echo "ERROR: baseball files not found at $DIR"
  exit 1
fi

echo "[*] Firewall off..."
/etc/init.d/rc.firewall stop 2>/dev/null || iptables -F 2>/dev/null || true

echo "[*] Stop upload_server on :8002..."
pkill -f "upload_server.py" 2>/dev/null || true
pkill -f "app_baseball.py" 2>/dev/null || true
sleep 1

echo "[*] Install flask if needed..."
python3 -c "import flask" 2>/dev/null || python3 -m pip install flask -q

cd "$DIR"
nohup python3 app_baseball.py >> baseball_server.log 2>&1 &
echo $! > baseball_server.pid
sleep 2

if curl -sf "http://127.0.0.1:${PORT}/api/health" >/dev/null; then
  write_status "RUNNING" "Baseball app OK locally. Phone (same Wi-Fi): http://${IP}:${PORT}"
  echo "OK: http://${IP}:${PORT}"
  python3 -m pip install qrcode pillow -q 2>/dev/null || true
  if python3 -c "import qrcode" 2>/dev/null; then
    python3 <<PY
import qrcode
from pathlib import Path
url = "http://${IP}:${PORT}"
out = Path("$DRIVE/baseball_qr_puppy.png")
qr = qrcode.QRCode(box_size=8, border=3)
qr.add_data(url)
qr.make(fit=True)
qr.make_image().save(out)
print("QR:", out, "->", url)
PY
  fi
  exit 0
else
  write_status "FAILED" "app_baseball.py not responding on 127.0.0.1:${PORT}. See baseball_server.log"
  echo "FAILED — check $DIR/baseball_server.log"
  tail -20 "$DIR/baseball_server.log" 2>/dev/null || true
  exit 1
fi
