#!/usr/bin/env bash
# Replace puppy's bottom bar with a CLEAN one (name only). Backs up the old first.
# No Drive reads, no fleet lanes, no fake 3/3. Split-brain safe.
cd "$HOME/fleet" || { echo "no ~/fleet here"; exit 1; }
git pull -q --no-edit 2>/dev/null || true
SL="$HOME/.cursor/statusline.sh"
BAK="projects/puppy/_old_rules"
mkdir -p "$BAK" "$(dirname "$SL")"

# 1. back up the old bar if present
[ -f "$SL" ] && cp -a "$SL" "$BAK/statusline.sh.$(date +%Y%m%d-%H%M%S).bak"

# 2. write the clean bar — name only
cat > "$SL" <<'SH'
#!/usr/bin/env bash
# puppy clean bar — name only. No Drive, no lanes, no fake status.
cat >/dev/null 2>&1   # swallow Cursor's JSON input
printf 'puppy'
SH
chmod +x "$SL"

# 3. keep a copy of the clean bar in the repo for record
cp -a "$SL" "$BAK/statusline.sh.CLEAN"

git add "$BAK"
git commit -q -m "clean-bar: puppy statusline reset to name only (old backed up)" || true
git push -q
echo "puppy bar cleaned. old bar backed up in $BAK. new bar shows: puppy"
echo "NOTE: reload / fresh chat to see the new bar."
