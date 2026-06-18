#!/usr/bin/env bash
# READ-ONLY: find candidate projects & websites on this machine and report them
# into the fleet repo. Does NOT copy, move, or delete anything. Split-brain safe.
#   usage: ./projects.sh [name]
NAME="${1:-$(hostname)}"
cd "$HOME/fleet" || { echo "no ~/fleet here"; exit 1; }
git pull -q --no-edit 2>/dev/null || true
OUT="bus/reports/${NAME}-projects.md"

ROOTS=("$HOME" /root /home/spot)
MARKERS='package\.json|index\.html|requirements\.txt|Dockerfile|composer\.json|Cargo\.toml|go\.mod|manage\.py|wp-config\.php|next\.config\.js|vite\.config\.js|pyproject\.toml'
SKIP='/(node_modules|\.cache|\.cursor|\.config|\.local|fleet|\.git)/'

# deeper, read-only project detection
CAND=$(mktemp)
for R in "${ROOTS[@]}"; do
  [ -d "$R" ] || continue
  find "$R" -maxdepth 6 -type f 2>/dev/null | grep -E "/($MARKERS)\$" | sed -E 's#/[^/]+$##'
  find "$R" -maxdepth 6 -name .git -type d 2>/dev/null | sed 's#/\.git$##'
done 2>/dev/null | grep -vE "$SKIP" | sort -u > "$CAND"
COUNT=$(wc -l < "$CAND" | tr -d ' ')

{
  echo "# Projects inventory: $NAME  ($(date -Iseconds))"
  echo
  echo "_Read-only scan. Nothing was copied, moved, or changed._"
  echo
  echo "## COUNT: $COUNT candidate projects found"
  echo
  echo "## Candidate projects (folders with project files or a .git)"
  echo
  while read -r d; do
    [ -z "$d" ] && continue
    sz=$(du -sh "$d" 2>/dev/null | cut -f1)
    mod=$(date -r "$d" +%Y-%m-%d 2>/dev/null)
    printf -- "- %s  (%s, last change %s)\n" "$d" "${sz:-?}" "${mod:-?}"
  done < "$CAND"
  echo
  echo "## Every folder inside the likely work dirs (catch plain folders w/o project files)"
  for W in "$HOME"/bunny/workspace "$HOME"/my-applications "$HOME"/my-documents \
           "$HOME"/lester "$HOME"/puppy-server "$HOME"/uploaded_files "$HOME"/spot \
           "$HOME"/GoogleDrive "$HOME"/GoogleDrive/projects "$HOME"/Applications; do
    [ -d "$W" ] || continue
    echo "### $W"
    ls -d "$W"/*/ 2>/dev/null | sed 's#^#- #'
  done
  echo
  echo "## All top-level folders in \$HOME"
  ls -d "$HOME"/*/ 2>/dev/null | sed 's#^#- #'
  echo
  echo "## Files that may already list projects"
  ls -1 "$HOME"/currentProjects.* "$HOME"/inbox 2>/dev/null | sed 's#^#- #'
} > "$OUT"
rm -f "$CAND"

git add "$OUT"
git commit -q -m "inventory: $NAME projects (read-only)" || true
git push -q
echo "projects inventory filed -> $OUT"
