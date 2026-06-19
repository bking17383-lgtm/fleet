#!/usr/bin/env bash
# Test hitme.dev and SAY the result out loud (cb1 audio). No keys — public HTTP.
#   ./say-site.sh           one-shot: test + speak the verdict
#   ./say-site.sh watch [N] poll every 30s up to N times (default 120); speak ONCE when it's fully up
export XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}"
PATHS=(/ /goal /daddy /george /bunny /projects)

say() { command -v espeak-ng >/dev/null 2>&1 && espeak-ng -a 200 -s 140 "$1" --stdout 2>/dev/null | paplay 2>/dev/null; }

count_live() {
  local live=0 p code
  for p in "${PATHS[@]}"; do
    code=$(curl -s -o /dev/null -m 8 -w '%{http_code}' "https://hitme.dev$p" 2>/dev/null)
    # 2xx and 3xx (e.g. 302 redirect on home) both count as LIVE; 5xx/000 = down
    [ "$code" -ge 200 ] && [ "$code" -lt 400 ] && live=$((live+1))
  done
  echo "$live"
}

verdict() {
  local live=$1 total=${#PATHS[@]}
  if [ "$live" -eq "$total" ]; then echo "your website works. all $total paths live.";
  elif [ "$live" -gt 0 ]; then echo "website partly up. $live of $total paths live.";
  else echo "website down. zero paths live."; fi
}

if [ "$1" = "watch" ]; then
  N="${2:-120}"
  for i in $(seq 1 "$N"); do
    live=$(count_live)
    if [ "$live" -eq "${#PATHS[@]}" ]; then m=$(verdict "$live"); echo "$m"; say "$m"; exit 0; fi
    sleep 30
  done
  echo "watch ended; site not fully up yet"; exit 1
else
  live=$(count_live); m=$(verdict "$live"); echo "$m"; say "$m"
fi
