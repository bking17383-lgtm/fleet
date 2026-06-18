#!/usr/bin/env bash
# Capture Chromebook screen for Daddy/Cursor (read via ~/.stan/screen/latest.png)
set -euo pipefail
OUT_DIR="${HOME}/.stan/screen"
OUT="${OUT_DIR}/latest.png"
HELD="${OUT_DIR}/held.png"
STAMP="${OUT_DIR}/capture_$(date +%Y%m%d_%H%M%S).png"
MIN_BYTES="${SCREEN_MIN_BYTES:-15000}"
mkdir -p "$OUT_DIR"

export DISPLAY="${DISPLAY:-:0}"
CAPTURE_DISPLAY="${CAPTURE_DISPLAY:-$DISPLAY}"

is_real_capture() {
  local f="$1"
  [[ -f "$f" ]] || return 1
  local n
  n="$(wc -c < "$f" | tr -d ' ')"
  [[ "$n" -ge "$MIN_BYTES" ]]
}

capture() {
  for try_d in "$CAPTURE_DISPLAY" ":1" ":0"; do
    DISPLAY="$try_d" scrot -o "$1" 2>/dev/null && is_real_capture "$1" && return 0
    DISPLAY="$try_d" import -window root "$1" 2>/dev/null && is_real_capture "$1" && return 0
    rm -f "$1"
  done
  if command -v gnome-screenshot >/dev/null 2>&1; then
    gnome-screenshot -f "$1" 2>/dev/null && is_real_capture "$1" && return 0
    rm -f "$1"
  fi
  return 1
}

# ChromeOS penguin: scrot usually returns black tiny frames — fail loudly
if ! capture "$OUT"; then
  echo "FAIL: no real capture (need ≥${MIN_BYTES} bytes). Use /screen SHOW SCREEN or eyes/inbox snap." >&2
  exit 1
fi

cp -f "$OUT" "$STAMP"
cp -f "$OUT" "$HELD"
echo "$OUT"
echo "bytes: $(wc -c < "$OUT")"
