#!/usr/bin/env bash
# Read Brian's clipboard from Linux (works when Brian copies text in Chrome)
set -euo pipefail
if command -v xclip >/dev/null 2>&1; then
  xclip -selection clipboard -o 2>/dev/null | head -c 4000
  exit 0
fi
if command -v wl-paste >/dev/null 2>&1; then
  wl-paste 2>/dev/null | head -c 4000
  exit 0
fi
echo "(clipboard unavailable — install xclip)"
exit 1
