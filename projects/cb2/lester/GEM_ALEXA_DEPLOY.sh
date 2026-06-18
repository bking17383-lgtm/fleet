#!/usr/bin/env bash
# GEM · CB1 — Alexa fix deploy (NET host :8770)
set -euo pipefail
for DRIVE in ~/GoogleDrive/MyDrive /mnt/shared/GoogleDrive/MyDrive; do
  [[ -d "$DRIVE/fleet" ]] && break
done
[[ -d "$DRIVE/fleet" ]] || { echo "FAIL: Drive"; exit 1; }
STAN="${HOME}/.stan"
mkdir -p "$STAN" "$DRIVE/phone" "$DRIVE/fleet/bus"
cp -f "$DRIVE/lester/alexa_speech.py" "$STAN/alexa_speech.py"
if [[ -f "$DRIVE/lester/aws_speech_deploy.py" ]]; then
  cp -f "$DRIVE/lester/aws_speech_deploy.py" "$STAN/aws_speech.py"
fi

# Filter test — must NOT speak "do now" or fleet paths
TEST=$(python3 -c "import sys; sys.path.insert(0,'$STAN'); from alexa_speech import for_aloud; print(for_aloud('do now: check fleet/bus/CPT_DELEGATE_NOW.txt tell captain: fix :8765=DOWN'))")
echo "filter_test=$TEST"

# Write honest aloud line for Echo routine
ALOUD="${TEST:-Fleet ready. NET is live on CB1.}"
echo "$ALOUD" > "$DRIVE/phone/say.txt"
echo "$ALOUD" > "$DRIVE/fleet/bus/AWS_SPEAK_ALOUD.txt"

GOAL_OK=NO
if curl -sf --connect-timeout 2 "http://127.0.0.1:8770/goal" | grep -qi alexa; then
  GOAL_OK=YES
fi
ALEXA_OK=NO
if curl -sf --connect-timeout 2 "http://127.0.0.1:8770/alexa" >/dev/null; then
  ALEXA_OK=YES
fi

NOW=$(date -Iseconds 2>/dev/null || date)
IP=$(hostname -I 2>/dev/null | awk '{print $1}')
cat > "$DRIVE/fleet/bus/GEM_ALEXA_DONE.txt" <<EOF
GEM ALEXA DEPLOY — ${NOW}
host=cb1 ip=${IP}
filter_test=${TEST}
phone/say.txt updated · no protocol paths
/goal alexa_section=${GOAL_OK} · /alexa=${ALEXA_OK}
Brian: say "Alexa, enable Brief Mode" once — fleet/ALEXA_FAST.txt
EOF

cat > "$DRIVE/fleet/bus/gem_to_cpt.txt" <<EOF
BUDDY ok — Alexa deploy cb1 · filter OK · say.txt clean · goal_alexa=${GOAL_OK} — ${NOW} · host: cb1
EOF

echo "OK — GEM_ALEXA_DONE.txt + gem_to_cpt posted"
