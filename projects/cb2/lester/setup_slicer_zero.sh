#!/usr/bin/env bash
# One-shot Video Slicer zero-cost host on puppy ($0/mo).
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"
DRIVE="${HOME}/GoogleDrive/MyDrive"
[[ -d "/mnt/shared/GoogleDrive/MyDrive" ]] && DRIVE="/mnt/shared/GoogleDrive/MyDrive"

echo "[*] Video Slicer zero-cost setup"

mkdir -p "${HOME}/.stan"
if [[ ! -f "${HOME}/.stan/groq.env" ]]; then
  cat >>"${HOME}/.stan/groq.env" <<'EOF'
# Groq — usage billed; cap uploads in app
GROQ_API_KEY=
SLICER_UPLOADS_PER_IP_DAY=10
EOF
  echo "Created ~/.stan/groq.env — add GROQ_API_KEY"
fi

bash "$DIR/start_slicer_host.sh"

if [[ -n "${CLOUDFLARE_TUNNEL_TOKEN:-}" ]]; then
  bash "$DIR/start_slicer_tunnel_named.sh"
else
  echo ""
  echo "SKIP tunnel: no CLOUDFLARE_TUNNEL_TOKEN"
  echo "  1. Cloudflare Zero Trust → Networks → Tunnels → Create"
  echo "  2. Public hostname → http://localhost:5000"
  echo "  3. export CLOUDFLARE_TUNNEL_TOKEN='...'"
  echo "  4. bash $DIR/start_slicer_tunnel_named.sh"
  echo "  5. echo 'https://YOUR-HOST' > $DRIVE/SLICER_PHONE_URL.txt"
fi

if [[ -d "$DRIVE" ]]; then
  cp -f "$DIR/app_mobile.py" "$DRIVE/lester/app_mobile.py" 2>/dev/null || true
  cp -f "$DIR/"*.sh "$DRIVE/lester/" 2>/dev/null || true
  {
    echo "# Slicer zero-cost host"
    echo "updated: $(date -Iseconds)"
    echo "hostname: $(hostname)"
    echo "local: http://127.0.0.1:5000"
    echo "tunnel: named (see SLICER_PHONE_URL.txt)"
  } >>"$DRIVE/puppy_outbox.txt"
fi

echo "OK — see $DRIVE/lester/SLICER_ZERO_COST.md"
