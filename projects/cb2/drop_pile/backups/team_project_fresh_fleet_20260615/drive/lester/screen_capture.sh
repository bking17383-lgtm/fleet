#!/usr/bin/env bash
# Capture Chromebook screen for Daddy/Cursor (read via ~/.stan/screen/latest.png)
set -euo pipefail
OUT_DIR="${HOME}/.stan/screen"
OUT="${OUT_DIR}/latest.png"
STAMP="${OUT_DIR}/capture_$(date +%Y%m%d_%H%M%S).png"
mkdir -p "$OUT_DIR"

export DISPLAY="${DISPLAY:-:0}"
export WAYLAND_DISPLAY="${WAYLAND_DISPLAY:-wayland-0}"

capture() {
  if command -v scrot >/dev/null 2>&1; then
    scrot -o "$1" 2>/dev/null && return 0
  fi
  if command -v import >/dev/null 2>&1; then
    import -window root "$1" 2>/dev/null && return 0
  fi
  if command -v gnome-screenshot >/dev/null 2>&1; then
    gnome-screenshot -f "$1" 2>/dev/null && return 0
  fi
  if command -v grim >/dev/null 2>&1; then
    grim "$1" 2>/dev/null && return 0
  fi
  return 1
}

if ! capture "$OUT"; then
  echo "FAIL: no capture tool worked. Enable Linux screen access: Chrome Settings → Linux → Allow Linux to access microphone/camera (and display)." >&2
  exit 1
fi

cp -f "$OUT" "$STAMP"
echo "$OUT"
echo "bytes: $(wc -c < "$OUT")"
