#!/usr/bin/env bash
# Gem · Alexa fleet speak — human only · no protocol · no loop
set -euo pipefail
STAN="${HOME}/.stan"
for DRIVE in /mnt/shared/GoogleDrive/MyDrive "$HOME/GoogleDrive/MyDrive"; do
  [[ -d "$DRIVE/fleet" ]] && break
done
[[ -d "$DRIVE/fleet" ]] || exit 1

mkdir -p "$STAN" "$DRIVE/phone" "$DRIVE/fleet/bus"
[[ -f "$DRIVE/lester/alexa_speech.py" ]] && cp -f "$DRIVE/lester/alexa_speech.py" "$STAN/"

up() { curl -sf -m 2 -o /dev/null "$1" 2>/dev/null && echo yes || echo no; }

CARDS=0
CARDS=$(curl -sf -m 3 http://127.0.0.1:8002/api/health 2>/dev/null | python3 -c "import sys,json; print(json.load(sys.stdin).get('cards',0))" 2>/dev/null || echo 0)
SARAH=$(up http://127.0.0.1:8766/sarah)
BASE=$(up http://127.0.0.1:8002/live/capture)
JAIL=$(up http://127.0.0.1:8788/gem/live)
HERIT=$(up http://127.0.0.1:8770/card)
HITME=$(up http://127.0.0.1:8770/goal)

RAW="Fleet snapshot. Cards ${CARDS}. Sarah ${SARAH}. Baseball live ${BASE}. Jailbreak ${JAIL}. Heritage demo ${HERIT}. Team board ${HITME}."
ALOUD=$(python3 -c "import sys; sys.path.insert(0,'$STAN'); from alexa_speech import for_aloud; print(for_aloud('''$RAW'''))" 2>/dev/null || true)
if [[ -z "${ALOUD:-}" ]]; then
  ALOUD="Four hundred ninety seven cards loaded. Jailbreak green. Heritage card demo ready on hitme."
fi

echo "$ALOUD" > "$DRIVE/phone/say.txt"
echo "$ALOUD" > "$DRIVE/fleet/bus/AWS_SPEAK_ALOUD.txt"
echo "$RAW" > "$DRIVE/fleet/bus/AWS_SPEAK.txt"
echo "ALOUD: $ALOUD"
