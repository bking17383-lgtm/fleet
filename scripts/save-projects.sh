#!/usr/bin/env bash
# PRESERVE: copy this machine's real projects INTO the fleet repo.
# Only writes into projects/<name>/. NEVER deletes anything from the machine.
#   usage: ./save-projects.sh [name]
NAME="${1:-$(hostname)}"
cd "$HOME/fleet" || { echo "no ~/fleet here"; exit 1; }
git pull -q --no-edit 2>/dev/null || true
DEST="projects/$NAME"
mkdir -p "$DEST"

# Folders that hold real work on this machine (puppy: everything under bunny/workspace)
SRCS=("$HOME/bunny/workspace")

for S in "${SRCS[@]}"; do
  [ -d "$S" ] || continue
  rsync -a \
    --exclude '.git' --exclude 'node_modules' --exclude 'venv' \
    --exclude '__pycache__' --exclude '.cache' --exclude '*.log' \
    "$S"/ "$DEST"/
done

git add "$DEST"
git commit -q -m "preserve: $NAME real projects (copy only, no deletes)" || true
git push -q
echo "preserved -> $DEST  (source on machine untouched)"
du -sh "$DEST" 2>/dev/null
