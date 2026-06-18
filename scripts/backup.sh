#!/usr/bin/env bash
# Back up a folder into the fleet:  ./backup.sh /path/to/project [name]
set -e
SRC="$1"; NAME="${2:-$(basename "$SRC")}"
[ -d "$SRC" ] || { echo "no such folder: $SRC"; exit 1; }
cd "$HOME/fleet"
git pull -q --no-edit || true
mkdir -p "projects/$NAME"
rsync -a --delete --exclude '.git' "$SRC"/ "projects/$NAME"/
git add "projects/$NAME"
git commit -q -m "backup: $NAME" || true
git push -q
echo "backed up: $SRC -> projects/$NAME (pushed)"
