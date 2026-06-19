#!/usr/bin/env bash
# THE ONE fleet rail (statusline). Every machine uses THIS — no per-machine duplicates.
# Line1: <machine> · model · ctx% · site · [FLASHING RED problems if any]
# Line2: team line (RAIL.txt). Local-only, no tokens, no git pull.
# Install: ln -sf ~/fleet/scripts/statusline.sh ~/.cursor/statusline.sh  (+ echo <name> > ~/.fleet-name)
payload=$(cat)

NAME=$(cat "$HOME/.fleet-name" 2>/dev/null || hostname 2>/dev/null || echo "?")
MODEL=$(printf '%s' "$payload" | grep -o '"display_name":"[^"]*"' | head -1 | sed 's/.*:"//;s/"$//'); [ -z "$MODEL" ] && MODEL="?"
PCT=$(printf '%s' "$payload" | grep -o '"used_percentage":[0-9.]*' | head -1 | sed 's/.*://' | cut -d. -f1); [ -z "$PCT" ] && PCT=0

SITE=$(cat "$HOME/.cache/hitme-site-state" 2>/dev/null || echo "?")
RAIL=$(cat "$HOME/fleet/bus/RAIL.txt" 2>/dev/null | head -1 || echo "fleet")

G=$'\033[32m'; R=$'\033[31m'; Y=$'\033[33m'; C=$'\033[36m'; D=$'\033[90m'; Z=$'\033[0m'
FR=$'\033[5;1;31m'   # FLASHING bold red for problems (falls back to bold red if no blink)

# --- collect PROBLEMS (each rendered flashing red) ---
probs=()
case "$SITE" in
  up)      S="${G}site:UP${Z}" ;;
  partial) S="${FR}site:PARTIAL${Z}"; probs+=("site partial") ;;
  down)    S="${FR}site:DOWN${Z}";    probs+=("SITE DOWN") ;;
  *)       S="${D}site:?${Z}" ;;
esac

# cb1-only: Jane daemons + disk/RAM (the box Jane runs on)
if [ "$NAME" = "cb1" ]; then
  jdown=0
  for d in jane-listen.py jane-voiced.py jane-watch.sh jane-refresh-loop jane-keeper.sh; do
    pgrep -f "$d" >/dev/null 2>&1 || jdown=$((jdown+1))
  done
  [ "$jdown" -gt 0 ] && probs+=("JANE ${jdown}/5 DOWN")
  freek=$(df -Pk / 2>/dev/null | awk 'NR==2{print $4}')
  [ -n "$freek" ] && [ "$freek" -lt 1048576 ] && probs+=("DISK LOW")
  availm=$(free -m 2>/dev/null | awk '/Mem/{print $7}')
  [ -n "$availm" ] && [ "$availm" -lt 200 ] && probs+=("RAM LOW")
fi

# build the problem banner (flashing red) if any
PROB=""
if [ "${#probs[@]}" -gt 0 ]; then
  joined=$(printf '%s · ' "${probs[@]}"); joined=${joined% · }
  PROB=" · ${FR}⚠ ${joined}${Z}"
fi

printf "%s%s%s · %s · %sctx %s%%%s · %s%s\n" "$C" "$NAME" "$Z" "$MODEL" "$D" "$PCT" "$Z" "$S" "$PROB"
printf "%s%s%s\n" "$D" "$RAIL" "$Z"
