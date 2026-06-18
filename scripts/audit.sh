#!/usr/bin/env bash
# Audit this machine, report its state into the fleet.  usage: ./audit.sh <name>
NAME="${1:-$(hostname)}"
cd "$HOME/fleet" || exit 1
git pull -q --no-edit 2>/dev/null || true
OUT="bus/reports/${NAME}-audit.md"
{
  echo "# Audit: $NAME  ($(date -Iseconds))"
  echo
  echo "## OS"
  grep -hE 'NAME|VERSION|ID' /etc/*release 2>/dev/null | head -5
  echo
  echo "## Cron jobs (old loops?)"
  crontab -l 2>/dev/null || echo "(none)"
  echo
  echo "## Suspicious processes (agents/loops/drive/gemini/bus)"
  ps aux 2>/dev/null | grep -iE 'cursor|gemini|rclone|drive|loop|fetch|[b]us' | grep -v grep | head -20 || echo "(none)"
  echo
  echo "## Git repos present (besides fleet)"
  find "$HOME" -maxdepth 3 -name .git -type d 2>/dev/null | grep -v "/fleet/" | head -20 || echo "(none)"
  echo
  echo "## Drive / rclone (old bus?)"
  mount 2>/dev/null | grep -iE 'drive|rclone|gdrive' || echo "(no drive mounts)"
  ls -d ~/.config/rclone 2>/dev/null || echo "(no rclone config)"
  echo
  echo "## Tools"
  for t in git ssh cron cursor-agent rclone; do printf "%s=%s\n" "$t" "$(command -v "$t" || echo NO)"; done
  echo
  echo "## Home top-level"
  ls -la "$HOME" 2>/dev/null | head -30
} > "$OUT"
git add "$OUT"
git commit -q -m "audit: $NAME" || true
git push -q
echo "audit filed: $OUT"
