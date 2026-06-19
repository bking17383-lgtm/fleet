#!/usr/bin/env bash
# Site guardian: watch hitme.dev and SPEAK only when the up/down state CHANGES (not every check).
# Free (curl + bash, no tokens). Safe to run from cron every few minutes, or as a loop.
#   ./site-guard.sh           one check; speak + log only if state changed since last run
#   ./site-guard.sh loop [S]  check every S seconds (default 120) forever
export XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}"
PATHS=(/ /goal /daddy /george /bunny /projects)
STATE="$HOME/.cache/hitme-site-state"   # remembers last known state across runs
mkdir -p "$(dirname "$STATE")"

say() { command -v espeak-ng >/dev/null 2>&1 && espeak-ng -a 200 -s 140 "$1" --stdout 2>/dev/null | paplay 2>/dev/null; }

check() {
  local live=0 p code
  for p in "${PATHS[@]}"; do
    code=$(curl -s -o /dev/null -m 8 -w '%{http_code}' "https://hitme.dev$p" 2>/dev/null)
    [ "$code" -ge 200 ] && [ "$code" -lt 400 ] && live=$((live+1))
  done
  [ "$live" -eq "${#PATHS[@]}" ] && echo "up" || { [ "$live" -gt 0 ] && echo "partial" || echo "down"; }
}

once() {
  local now prev; now=$(check); prev=$(cat "$STATE" 2>/dev/null || echo "unknown")
  if [ "$now" != "$prev" ]; then
    echo "$now" > "$STATE"
    local ts; ts=$(date -Iseconds)
    case "$now" in
      up)      say "your website is back up." ;;
      partial) say "warning. website is only partly up." ;;
      down)    say "alert. your website is down." ;;
    esac
    # log the transition into the fleet truth (cb1 is the writer)
    cd "$HOME/fleet" 2>/dev/null && {
      printf '\n- [%s] site-guard: state changed %s -> %s\n' "$ts" "$prev" "$now" >> bus/cb2/dns-problems.md
      git add bus/cb2/dns-problems.md 2>/dev/null
      git commit -q -m "site-guard: $prev -> $now" 2>/dev/null
      git push -q 2>/dev/null
    }
    echo "STATE CHANGE: $prev -> $now"
  else
    echo "no change ($now)"
  fi
}

if [ "$1" = "loop" ]; then
  S="${2:-120}"
  while true; do once; sleep "$S"; done
else
  once
fi
