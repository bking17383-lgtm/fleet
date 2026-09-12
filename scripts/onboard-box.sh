#!/usr/bin/env bash
# Onboard THIS box: measure → hardware card → Jane river drop.
#   ./scripts/onboard-box.sh <fleet_id> <agent>
# Agent runs this. Brian never pastes. Git is the library.
set -e
ROOT="${FLEET_ROOT:-$HOME/fleet}"
if [ ! -d "$ROOT/.git" ]; then
  ROOT="$(cd "$(dirname "$0")/.." && pwd)"
fi
cd "$ROOT"
ID="${1:?fleet_id}"
AGENT="${2:?agent}"
NOW="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

HOST="$(hostname)"
USERN="$(id -un)"
OS="$(. /etc/os-release 2>/dev/null; echo "${PRETTY_NAME:-unknown}")"
KERN="$(uname -r)"
VIRT="$(systemd-detect-virt 2>/dev/null || echo unknown)"
NCPU="$(nproc 2>/dev/null || echo unknown)"
CPU="$(grep -m1 'model name' /proc/cpuinfo 2>/dev/null | cut -d: -f2- | sed 's/^ //')"
MEM="$(awk '/MemTotal/ {printf "%.0f GiB", $2/1024/1024}' /proc/meminfo)"
DISK="$(df -hT / 2>/dev/null | awk 'NR==2{print $3" total, "$4" used, "$5" avail ("$2")"}')"
NET="$(hostname -I 2>/dev/null | awk '{print $1}')"

mkdir -p bus/hardware
CARD="bus/hardware/${ID}.md"
cat > "$CARD" <<EOF
# ${ID} — ${AGENT}
# Measured ${NOW} on this box. Not a guess.

fleet_id: ${ID}
agent: ${AGENT}
hostname: ${HOST}
user: ${USERN}
os: ${OS}
kernel: ${KERN}
virt: ${VIRT}
cpu: ${NCPU} × ${CPU}
ram: ${MEM}
root_disk: ${DISK}
net_ip: ${NET}
git_root: ${ROOT}

## PROOF
- hostname: \`hostname\`
- cpu: \`nproc\`; \`lscpu\`
- ram: \`free -h\`
- disk: \`df -hT /\`
- virt: \`systemd-detect-virt\`

## JANE + KIDS
River: bus/jane/river/HEAD.md
EOF

BODY="$(mktemp)"
cat > "$BODY" <<EOF
## speak
New box on the fleet: name ${AGENT}, designation ${ID}. ${NCPU} CPUs, ${MEM} RAM, ${OS}. Hostname ${HOST}. Virt ${VIRT}.

## measured
- hostname: ${HOST}
- virt: ${VIRT}
- cpu: ${NCPU} × ${CPU}
- ram: ${MEM}
- os: ${OS}
- card: ${CARD}
EOF

git add "$CARD"
git commit -q -m "hardware: ${ID} ${AGENT}" || true
git push -q 2>/dev/null || true

./scripts/jane-river.sh drop "$AGENT" "${ID} ${AGENT} joined" "$BODY"
rm -f "$BODY"
echo "onboarded: ${ID} / ${AGENT}  card=${CARD}"
echo "done-test: ./scripts/verify.sh file ${CARD} ${ID}"
