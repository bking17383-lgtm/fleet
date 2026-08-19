#!/usr/bin/env bash
# AMEN — one word from Brian. UTC timestamp restamp. Kids run this. Sidekick just calls it.
# Does NOT drop Jane river. River stays gated until this stamp verifies.
#   ./scripts/amen.sh <who>
set -e
ROOT="${FLEET_ROOT:-$HOME/fleet}"
if [ ! -d "$ROOT/.git" ]; then
  ROOT="$(cd "$(dirname "$0")/.." && pwd)"
fi
cd "$ROOT"
WHO="${1:-kids}"
NOW="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
ID="$(date -u +%Y%m%dT%H%M%SZ)"
BRANCH="$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo unknown)"
HEAD="$(git rev-parse --short HEAD 2>/dev/null || echo unknown)"
mkdir -p bus/jane/stamps bus/kids
STAMP="bus/jane/stamps/AMEN_${ID}.txt"
NOWFILE="bus/jane/AMEN_NOW.txt"

cat > "$STAMP" <<EOF
amen: ${NOW}
who: ${WHO}
box: $(hostname) $(id -un)
git_root: ${ROOT}
git: ${HEAD} ${BRANCH}
word: amen
EOF

cat > "$NOWFILE" <<EOF
# AMEN NOW — latest restamp. Sidekick reads this. Not a river drop.
amen: ${NOW}
who: ${WHO}
stamp_file: ${STAMP}
id: ${ID}
box: $(hostname) $(id -un) ${ROOT}
git: ${HEAD} ${BRANCH}
EOF

if ! grep -qxF "amen: ${NOW}" "$NOWFILE" || ! grep -qxF "amen: ${NOW}" "$STAMP"; then
  echo "AMEN RED: timestamp did not land"
  exit 1
fi
EPOCH_NOW="$(date -u +%s)"
STAMP_EPOCH="$(date -u -d "${NOW}" +%s 2>/dev/null || echo 0)"
AGE=$((EPOCH_NOW - STAMP_EPOCH))
if [ "$STAMP_EPOCH" -le 0 ] || [ "$AGE" -lt 0 ] || [ "$AGE" -gt 120 ]; then
  echo "AMEN RED: timestamp not now (amen=${NOW} age=${AGE}s)"
  exit 1
fi

git add "$STAMP" "$NOWFILE"
git commit -q -m "amen: ${WHO} ${NOW}" || true

echo "AMEN PASS ${NOW}"
echo "stamp: ${STAMP}"
echo "now:   ${NOWFILE}"
echo "age:   ${AGE}s"
