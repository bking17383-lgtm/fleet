#!/bin/bash
# HTTPS tunnel so Sarah's phone mic works (Chrome blocks speech on http://192.168.x.x)
# Run on CB2 while sarah_voice_sample.py is on :8766
set -e
CF="${HOME}/.stan/cloudflared"
OUT="/mnt/shared/GoogleDrive/MyDrive/fleet/SARAH_VOICE_URL.txt"
PORT="${SARAH_PORT:-8766}"
mkdir -p "$(dirname "$OUT")"
echo "Starting tunnel to localhost:$PORT …"
"$CF" tunnel --url "http://127.0.0.1:$PORT" 2>&1 | while read -r line; do
  echo "$line"
  if echo "$line" | grep -q 'https://.*trycloudflare.com'; then
    url=$(echo "$line" | grep -oE 'https://[a-z0-9-]+\.trycloudflare\.com')
    if [ -n "$url" ]; then
      echo "$url/sarah" > "$OUT"
      echo ">>> Sarah open: $url/sarah  (mic should work)"
      echo ">>> QR page:   $url/qr"
    fi
  fi
done
