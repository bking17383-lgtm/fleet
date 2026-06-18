#!/usr/bin/env bash
# hitme.dev fleet management — start services + status on Drive
set -euo pipefail

STAN="${HOME}/.stan"
DRIVE="/mnt/shared/GoogleDrive/MyDrive"
[[ -d "$HOME/GoogleDrive/MyDrive" ]] && DRIVE="$HOME/GoogleDrive/MyDrive"
DOMAIN="hitme.dev"
STATUS="${DRIVE}/fleet/HITME_STATUS.txt"
URLS="${DRIVE}/fleet/HITME_URLS.txt"
CF="${STAN}/cloudflared"
TUNNEL_NAME="cb2-daddy"
TUNNEL_ID="11431ecb-5cbd-40a5-b635-cec2aff9de03"
ACCOUNT="ad430a8e50c3ba0990c395528f3482ba"

mkdir -p "${DRIVE}/fleet"
echo "${DOMAIN}" > "${DRIVE}/fleet/HITME_DOMAIN.txt"

refresh_who() {
  python3 "${DRIVE}/lester/plate_who.py" >/dev/null 2>&1 || true
}

start_if_down() {
  local name="$1" port="$2" cmd="$3"
  if curl -sf "http://127.0.0.1:${port}/health" >/dev/null 2>&1; then
    echo "  ${name}:${port} UP"
    return 0
  fi
  echo "  starting ${name}:${port}…"
  nohup bash -c "$cmd" >"${STAN}/${name}.log" 2>&1 &
  sleep 2
  if curl -sf "http://127.0.0.1:${port}/health" >/dev/null 2>&1; then
    echo "  ${name}:${port} UP"
  else
    echo "  ${name}:${port} FAIL — see ${STAN}/${name}.log"
  fi
}

refresh_who
echo "=== hitme.dev manage ==="

start_if_down "hitme_who" 8770 "python3 ${STAN}/hitme_who_server.py"
start_if_down "sarah" 8766 "python3 ${STAN}/sarah_voice_sample.py"
bash "${STAN}/hitme_tunnel.sh" 2>/dev/null || true

mesh="DOWN"
if curl -sf "http://127.0.0.1:8765/health" >/dev/null 2>&1 || curl -sf "http://127.0.0.1:8765/status" >/dev/null 2>&1; then
  mesh="UP"
fi
echo "  mesh:8765 ${mesh}"

cat >"${URLS}" <<EOF
# hitme.dev — canonical URLs (after tunnel hostnames live)
Updated: $(date -Iseconds)

ROOT / WHO     https://${DOMAIN}/
               https://who.${DOMAIN}/

SARAH          https://sarah.${DOMAIN}/sarah

MESH           https://mesh.${DOMAIN}/   (when :8765 up)

EMAIL (setup)  hello@${DOMAIN} → tpgoround@gmail.com (Cloudflare Email Routing)

Tunnel dash:  https://dash.cloudflare.com/${ACCOUNT}/networks/tunnels/${TUNNEL_ID}
Email dash:     https://dash.cloudflare.com/${ACCOUNT}/${DOMAIN}/email/routing
EOF

cat >"${STATUS}" <<EOF
hitme.dev STATUS — $(date -Iseconds)
hostname: $(hostname -s)

SERVICES (CB2)
  who server :8770  $(curl -sf http://127.0.0.1:8770/health >/dev/null && echo UP || echo DOWN)
  sarah      :8766  $(curl -sf http://127.0.0.1:8766/health >/dev/null && echo UP || echo DOWN)
  mesh       :8765  ${mesh}

TUNNEL: ${TUNNEL_NAME} (${TUNNEL_ID})
  Add public hostnames in dashboard (see fleet/HITME_TUNNEL_HOSTNAMES.txt)

DNS: Cloudflare NS active (pranab / tia)

WHO data: fleet/WHO.json · fleet/WHO.md
Regenerate: python3 lester/plate_who.py
EOF

echo ""
cat "${STATUS}"
echo ""
echo "URLs: ${URLS}"

if [[ "${1:-}" == "dns" ]]; then
  echo ""
  echo "=== DNS route (needs cloudflared login once) ==="
  for h in "${DOMAIN}" "who.${DOMAIN}" "sarah.${DOMAIN}" "mesh.${DOMAIN}"; do
    echo "  ${CF} tunnel route dns ${TUNNEL_NAME} ${h}"
  done
fi
