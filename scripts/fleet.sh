#!/usr/bin/env bash
# One command to see the whole fleet:  ./fleet.sh
cd "$HOME/fleet"
git pull -q --no-edit || true
echo "===================== FLEET ====================="
echo "--- GOALS (now) ---"
sed -n '/## Now/,/## Not now/p' bus/GOALS.md | sed '$d' | grep -v '## Now'
echo "--- CONTROL ---"
grep '^STATUS:' bus/CONTROL.md
echo "--- MACHINES ---"
shopt -s nullglob
for f in bus/status/*.md; do
  name=$(grep '^machine:'  "$f" | cut -d' ' -f2-)
  seen=$(grep '^last_seen:' "$f" | cut -d' ' -f2-)
  doing=$(grep '^doing:'   "$f" | cut -d':' -f2- | sed 's/^ //')
  printf "  %-6s | %s | %s\n" "$name" "$seen" "$doing"
done
echo "================================================="
