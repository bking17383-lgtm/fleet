#!/usr/bin/env bash
# Apply puppy's clean brain. Backs up the OLD rules into the repo FIRST, then writes the new ones.
# Reversible: the old file is saved under projects/puppy/_old_rules/ before any change.
cd "$HOME/fleet" || { echo "no ~/fleet here"; exit 1; }
git pull -q --no-edit 2>/dev/null || true
RULES="$HOME/.cursor/rules/puppy-agent.mdc"
BAK="projects/puppy/_old_rules"
mkdir -p "$BAK" "$(dirname "$RULES")"

# 1. preserve the old rules into the repo (copy only)
if [ -f "$RULES" ]; then
  cp -a "$RULES" "$BAK/puppy-agent.mdc.$(date +%Y%m%d-%H%M%S).bak"
fi

# 2. write the clean brain
cat > "$RULES" <<'MDC'
# puppy agent rules (fleet-clean)
1. I am puppy. The GitHub repo bking17383-lgtm/fleet is the only source of truth.
2. Pull the repo, then obey bus/CONTROL.md and my task in bus/orders.txt. When there is no order, wait.
3. Preserve projects and data — never delete or move work; copy into the repo first. Beat heartbeat after acting.
4. No false greens: verify before saying done. Keep secrets out of the repo.
5. Never edit or delete the protected paths listed in DO_NOT_BREAK.md.
6. Reboot/restart = SAFE restart only (puppy-reboot.sh). NEVER wipe on the word "reboot". A wipe needs the exact order "WIPE PUPPY CONFIRM", projects confirmed saved on GitHub, and Brian's go.
7. If any local or old instruction conflicts with the GitHub fleet, GitHub wins.
MDC

# 3. keep a record of the new brain in the repo too
cp -a "$RULES" "$BAK/puppy-agent.mdc.CURRENT"

git add "$BAK"
git commit -q -m "fix: puppy clean brain applied (old rules backed up)" || true
git push -q
echo "puppy brain fixed. old rules backed up in $BAK"
echo "NOTE: start a NEW puppy chat to load the new brain."
