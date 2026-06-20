#!/usr/bin/env bash
# loop.sh — isolation-safe fleet loop (write-back WITHOUT touching the truth).
#
# WHY: heartbeat.sh pushes the current branch (main), so any reporting box could
# corrupt the one truth. That made "give a box a key" == "let it infect main",
# so keys were banned -> no write-back -> human couriering. This breaks that trap.
#
# HOW: each machine reports to its OWN branch  loop/<name>  (force-updated, branch
# only). main is NEVER pushed here. The boss reads every box via  origin/loop/*
# and merges only what he accepts. A box can only ever pollute its own branch.
#
#   usage: ./scripts/loop.sh [name] ["what I'm doing"]
#   name defaults to ~/.fleet-name, else hostname.
set -euo pipefail

NAME="${1:-$(cat "$HOME/.fleet-name" 2>/dev/null || hostname)}"
DOING="${2:-looped}"
REPO="$HOME/fleet"
BR="loop/$NAME"
cd "$REPO"

git fetch -q origin
TRUTH_BEFORE="$(git rev-parse origin/main)"

# Build the report in an isolated worktree forked from the LATEST truth, so the
# main working tree/branch is never switched or risked.
WT="$(mktemp -d)"
cleanup() { git worktree remove --force "$WT" >/dev/null 2>&1 || true; }
trap cleanup EXIT

git worktree add -q -B "$BR" "$WT" origin/main
(
  cd "$WT"
  mkdir -p bus/status
  cat > "bus/status/$NAME.md" <<EOF
machine: $NAME
host: $(hostname)
last_seen: $(date -Iseconds)
truth_hash: $(git rev-parse --short origin/main)
doing: $DOING
state: looped (read truth; reporting on $BR — main untouched)
EOF
  git add "bus/status/$NAME.md"
  git -c user.name='bking17383' -c user.email="$NAME@fleet.local" \
      commit -q -m "loop: $NAME — $DOING" || true
  git push -qf origin "$BR"
)

# Prove the truth was NOT touched by this loop.
git fetch -q origin
TRUTH_AFTER="$(git rev-parse origin/main)"
if [ "$TRUTH_BEFORE" != "$TRUTH_AFTER" ]; then
  echo "WARN: origin/main changed during loop ($TRUTH_BEFORE -> $TRUTH_AFTER) — not by this script's push." >&2
fi

echo "looped: $NAME -> branch $BR | truth origin/main=$(git rev-parse --short origin/main) (untouched)"
