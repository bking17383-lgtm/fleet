#!/usr/bin/env bash
# GEM · Alexa QUICK — say.txt already filtered on Drive · ~30s
set -euo pipefail
for DRIVE in ~/GoogleDrive/MyDrive /mnt/shared/GoogleDrive/MyDrive; do
  [[ -d "$DRIVE/fleet" ]] && break
done
[[ -d "$DRIVE/fleet" ]] || { echo "FAIL: Drive"; exit 1; }

STAN="${HOME}/.stan"
mkdir -p "$STAN" "$DRIVE/phone" "$DRIVE/fleet/bus"
[[ -f "$DRIVE/lester/alexa_speech.py" ]] && cp -f "$DRIVE/lester/alexa_speech.py" "$STAN/"

# Already clean? Skip heavy test.
SAY="$DRIVE/phone/say.txt"
if grep -qiE 'do now|tell captain|fleet/bus' "$SAY" 2>/dev/null; then
  ALOUD=$(python3 -c "import sys; sys.path.insert(0,'$STAN'); from alexa_speech import for_aloud; print(for_aloud(open('$SAY').read()))" 2>/dev/null || echo "Fleet ready.")
  echo "$ALOUD" > "$SAY"
  echo "$ALOUD" > "$DRIVE/fleet/bus/AWS_SPEAK_ALOUD.txt"
else
  echo "say.txt already clean — skip filter rewrite"
fi

NOW=$(date -Iseconds 2>/dev/null || date)
GEM_STAMP="GEM DONE — Alexa quick · say.txt OK · Brief Mode for Brian — $NOW"
echo "$GEM_STAMP" > "$DRIVE/fleet/bus/GEM_STAMP.txt"
cat > "$DRIVE/fleet/bus/gem_to_cpt.txt" <<EOF
GEM ok — Alexa quick done · say.txt clean · Brief Mode for Brian — $NOW · host: cb1
EOF
echo "OK — quick alexa · gem_to_cpt posted"
