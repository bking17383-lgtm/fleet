#!/usr/bin/env bash
# THE ONE fleet rail (statusline). Every machine uses THIS — no per-machine duplicates.
# Shows: <machine> · model · ctx% · live site status · team line (RAIL.txt). Local-only, no tokens, no git pull.
# Install on any machine:  ln -sf ~/fleet/scripts/statusline.sh ~/.cursor/statusline.sh   (+ echo <name> > ~/.fleet-name)
payload=$(cat)

NAME=$(cat "$HOME/.fleet-name" 2>/dev/null || hostname 2>/dev/null || echo "?")
MODEL=$(printf '%s' "$payload" | grep -o '"display_name":"[^"]*"' | head -1 | sed 's/.*:"//;s/"$//'); [ -z "$MODEL" ] && MODEL="?"
PCT=$(printf '%s' "$payload" | grep -o '"used_percentage":[0-9.]*' | head -1 | sed 's/.*://' | cut -d. -f1); [ -z "$PCT" ] && PCT=0

SITE=$(cat "$HOME/.cache/hitme-site-state" 2>/dev/null || echo "?")
RAIL=$(cat "$HOME/fleet/bus/RAIL.txt" 2>/dev/null | head -1 || echo "fleet")

G=$'\033[32m'; R=$'\033[31m'; Y=$'\033[33m'; C=$'\033[36m'; D=$'\033[90m'; Z=$'\033[0m'
case "$SITE" in
  up)      S="${G}site:UP${Z}" ;;
  partial) S="${Y}site:PARTIAL${Z}" ;;
  down)    S="${R}site:DOWN${Z}" ;;
  *)       S="${D}site:?${Z}" ;;
esac

printf "%s%s%s · %s · %sctx %s%%%s · %s\n" "$C" "$NAME" "$Z" "$MODEL" "$D" "$PCT" "$Z" "$S"
printf "%s%s%s\n" "$D" "$RAIL" "$Z"
