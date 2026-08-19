#!/usr/bin/env bash
# Jane river — sole git writer for bus/jane/river/
# Kids/boxes post here. Jane reads HEAD.md. Drive is not a river.
#   ./scripts/jane-river.sh drop <who> "<one-line what>" [body-file|-]
#   ./scripts/jane-river.sh head
#   ./scripts/jane-river.sh works "<bullet>"
set -e
ROOT="${FLEET_ROOT:-$HOME/fleet}"
if [ ! -d "$ROOT/.git" ]; then
  ROOT="$(cd "$(dirname "$0")/.." && pwd)"
fi
cd "$ROOT"
git pull -q --no-edit 2>/dev/null || true

CMD="${1:-}"
RIVER="bus/jane/river"
mkdir -p "$RIVER/drops"

stamp_now() { date -u +%Y-%m-%dT%H:%M:%SZ; }
drop_id() { date -u +%Y-%m-%dT%H%MZ; }

write_head() { # $1=stamp-line $2=who $3=as_of $4=drop-relpath $5=now-bullets-file
  local stamp="$1" who="$2" as_of="$3" drop="$4"
  cat > "$RIVER/HEAD.md" <<EOF
# JANE RIVER — HEAD (read this; speak this; don't guess)
# git is truth · Drive is dark · kids refresh ~180s

stamp: $stamp
as_of: $as_of
by: $who
latest_drop: $drop

## now
$(cat "$5")

## do-not
- Do not invent boxes or paths not listed here or in what-works.md
- Do not use Drive / Google as truth (Disk river is dark)
- Do not call a KVM worker a Chromebook or cb1
EOF
}

commit_river() { # $1=msg
  git add "$RIVER"
  git commit -q -m "$1" || true
  git push -q 2>/dev/null || true
}

case "$CMD" in
  drop)
    WHO="${2:?who}"
    WHAT="${3:?what}"
    BODY="${4:-}"
    NOW="$(stamp_now)"
    ID="$(drop_id)"
    SLUG=$(printf '%s' "$WHAT" | tr '[:upper:]' '[:lower:]' | tr -cs 'a-z0-9' '-' | sed 's/^-//;s/-$//' | cut -c1-40)
    [ -n "$SLUG" ] || SLUG=drop
    DROP_REL="$RIVER/drops/${ID}-${WHO}-${SLUG}.md"
    STAMP="JANE RIVER — ${WHAT} · by=${WHO} — ${NOW}"
    {
      echo "# $STAMP"
      echo
      echo "by: $WHO"
      echo
      if [ -n "$BODY" ] && [ "$BODY" != "-" ] && [ -f "$BODY" ]; then
        cat "$BODY"
      elif [ "$BODY" = "-" ]; then
        cat
      fi
    } > "$DROP_REL"
    NOWFILE="$(mktemp)"
    printf -- '- %s\n- Latest drop: %s\n- What works: bus/jane/river/what-works.md\n' "$WHAT" "$DROP_REL" > "$NOWFILE"
    write_head "$STAMP" "$WHO" "$NOW" "$DROP_REL" "$NOWFILE"
    rm -f "$NOWFILE"
    commit_river "river: $WHO $WHAT"
    echo "river drop: $DROP_REL"
    echo "jane head:  $RIVER/HEAD.md"
    ;;
  head)
    test -f "$RIVER/HEAD.md"
    cat "$RIVER/HEAD.md"
    ;;
  works)
    BULLET="${2:?bullet}"
    touch "$RIVER/what-works.md"
    grep -qxF -- "- $BULLET" "$RIVER/what-works.md" 2>/dev/null || echo "- $BULLET" >> "$RIVER/what-works.md"
    commit_river "river: what-works"
    echo "what-works appended"
    ;;
  *)
    echo "usage: jane-river.sh drop <who> \"<what>\" [body-file|-] | head | works \"<bullet>\""
    exit 2
    ;;
esac
