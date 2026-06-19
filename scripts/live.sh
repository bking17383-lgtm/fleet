#!/usr/bin/env bash
# LIVE STATE — the "as of now" read. Run this BEFORE acting, every time.
# Free (git + bash), read-only. Answers: what time is it, who's actually alive, what just changed, what's the order.
cd "$HOME/fleet" || { echo "no ~/fleet here"; exit 1; }
git pull -q --no-edit 2>/dev/null || true
NOW=$(date +%s)

echo "=================== LIVE STATE ==================="
echo "now: $(date -Iseconds)"
echo
echo "--- machines (heartbeat + freshness) ---"
for f in bus/status/*.md; do
  [ -f "$f" ] || continue
  name=$(basename "$f" .md)
  last=$(grep -i '^last_seen:' "$f" | cut -d' ' -f2- | tr -d ' ')
  doing=$(grep -i '^doing:' "$f" | sed 's/^[^:]*: *//')
  state=$(grep -i '^state:' "$f" | sed 's/^[^:]*: *//')
  ls_epoch=$(date -d "$last" +%s 2>/dev/null || echo 0)
  if [ "$ls_epoch" -gt 0 ]; then
    age=$(( (NOW - ls_epoch) / 60 ))
    [ "$age" -gt 30 ] && fresh="STALE (${age}m old)" || fresh="fresh (${age}m)"
  else
    fresh="unknown"
  fi
  printf "  %-7s %-8s %-22s  doing: %s\n" "$name" "$state" "$fresh" "$doing"
done
echo
echo "--- current order ---"
grep '^STATUS:' bus/CONTROL.md 2>/dev/null | head -1
echo "  jobs:"; grep -v '^#' bus/orders.txt 2>/dev/null | sed 's/^/    /'
echo
echo "--- last 5 changes ---"
git log --pretty=format:'  %h %an %ar  %s' -5
echo
echo "================================================="
echo "Rule: trust 'fresh' nodes; a STALE node is frozen/faking — do not believe its last claim."
