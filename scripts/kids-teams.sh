#!/usr/bin/env bash
# Last teams that stamped. Git only. No invented boxes.
#   ./scripts/kids teams
set -euo pipefail
ROOT="${FLEET_ROOT:-$HOME/fleet}"
if [ ! -d "$ROOT/.git" ]; then
  ROOT="$(cd "$(dirname "$0")/.." && pwd)"
fi
cd "$ROOT"
NOW="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
OUT="bus/kids/TEAMS_NOW.txt"
mkdir -p bus/kids

amen_lines() {
  local f amen who
  for f in bus/jane/stamps/AMEN_*.txt; do
    [ -f "$f" ] || continue
    amen="$(awk '/^amen:/{print $2; exit}' "$f")"
    who="$(awk '/^who:/{print $2; exit}' "$f")"
    [ -n "$who" ] && [ -n "$amen" ] && echo "$amen $who"
  done | sort | awk '{ last[$2] = $1 } END { for (w in last) print "  " w "  " last[w] }' | sort
}

river_lines() {
  local f by base
  for f in bus/jane/river/drops/*.md; do
    [ -f "$f" ] || continue
    by="$(awk '/^by:/{print $2; exit}' "$f")"
    base="$(basename "$f")"
    [ -n "$by" ] && echo "$base $by"
  done | sort | awk '{ last[$2] = $1 } END { for (w in last) print "  " w "  " last[w] }' | sort
}

{
  echo "TEAMS LAST STAMP  ${NOW}  kids · git only"
  echo

  echo "AMEN (who)"
  amen_lines
  echo "  amen_now: $(awk '/^amen:/{print $2; exit}' bus/jane/AMEN_NOW.txt 2>/dev/null)  who=$(awk '/^who:/{print $2; exit}' bus/jane/AMEN_NOW.txt 2>/dev/null)"
  echo

  echo "RIVER (by)  last drop each"
  river_lines
  echo "  HEAD by=$(awk '/^by:/{print $2; exit}' bus/jane/river/HEAD.md)  as_of=$(awk '/^as_of:/{print $2; exit}' bus/jane/river/HEAD.md)"
  echo

  echo "HEARTBEAT (status)"
  if ls bus/status/*.md >/dev/null 2>&1; then
    for f in bus/status/*.md; do
      m=$(awk '/^machine:/{print $2; exit}' "$f")
      s=$(awk '/^last_seen:/{print $2; exit}' "$f")
      d=$(awk '/^doing:/{sub(/^doing: /,""); print; exit}' "$f")
      echo "  ${m}  ${s}  ${d}"
    done
  else
    echo "  none"
  fi
  echo

  echo "HARDWARE library"
  echo "  updated: $(awk '/^Updated:/{print $2; exit}' bus/hardware/LIBRARY.md 2>/dev/null)  by=$(awk '/^Posted by:/{print $3; exit}' bus/hardware/LIBRARY.md 2>/dev/null)"
  cards=""
  for f in bus/hardware/*.md; do
    b="$(basename "$f")"
    [ "$b" = "LIBRARY.md" ] && continue
    cards="${cards}${b} "
  done
  echo "  cards: ${cards}"
  echo

  echo "Word: TEAMS FROM STAMPS · NO INVENT"
} | tee "$OUT"

echo "file: ${OUT}"
