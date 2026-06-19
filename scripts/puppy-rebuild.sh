#!/usr/bin/env bash
# CLEAN PUPPY REBUILD — installs clean brain + soul + clean bar in one shot.
# Backs up whatever exists first. Projects are already preserved in the repo.
# This resets puppy's IDENTITY to known-good. No Drive bus, no slaves, no old wake.
cd "$HOME/fleet" || { echo "no ~/fleet here — clone bking17383-lgtm/fleet first"; exit 1; }
git pull -q --no-edit 2>/dev/null || true
RDIR="$HOME/.cursor/rules"
REC="projects/puppy/_clean_boot"
BAK="$REC/old_$(date +%Y%m%d-%H%M%S)"
mkdir -p "$RDIR" "$HOME/.cursor" "$BAK"

# WIPE: back up EVERY existing rule file + the bar, then clear all old .mdc rules
if [ -d "$RDIR" ]; then
  cp -a "$RDIR"/. "$BAK/" 2>/dev/null || true
  rm -f "$RDIR"/*.mdc 2>/dev/null || true
fi
[ -f "$HOME/.cursor/statusline.sh" ] && cp -a "$HOME/.cursor/statusline.sh" "$BAK/"
# NOTE: we do NOT touch labwc/swayidle/keep-awake (DO_NOT_BREAK) or running loops here.

# 1. the brain = puppy's SANDBOX (voice + real paths + rules + challenge), with .mdc header
{
  printf -- '---\n'
  printf 'description: Puppy — voice, paths, and rules (puppy64, GitHub single truth)\n'
  printf 'alwaysApply: true\n'
  printf -- '---\n\n'
  cat bus/puppy/puppy-soul.txt
} > "$RDIR/puppy-soul.mdc"

# 3. clean bar
cat > "$HOME/.cursor/statusline.sh" <<'SH'
#!/usr/bin/env bash
cat >/dev/null 2>&1
printf 'puppy'
SH
chmod +x "$HOME/.cursor/statusline.sh"

# record the clean set in the repo
cp -a "$RDIR/puppy-soul.mdc"      "$REC/puppy-soul.mdc.CLEAN"
cp -a "$HOME/.cursor/statusline.sh"  "$REC/statusline.sh.CLEAN"

git add "$REC"
git commit -q -m "rebuild: puppy clean brain + soul + clean bar (old backed up)" || true
git push -q
echo "PUPPY REBUILT: clean brain + soul + clean bar installed."
echo "Old files backed up in $BAK"
echo "Start a FRESH puppy chat to wake him up clean."
