#!/usr/bin/env bash
# PRESERVE: copy this machine's real projects INTO the fleet repo.
# Only writes into projects/<name>/. NEVER deletes anything on the machine.
# NO secrets: *.env · keys · secrets/ excluded.
#   usage: ./save-projects.sh [name]
set -euo pipefail
NAME="${1:-$(hostname)}"
cd "$HOME/fleet" || { echo "no ~/fleet here"; exit 1; }
git pull -q --no-edit 2>/dev/null || true
DEST="projects/$NAME"
mkdir -p "$DEST"

RSYNC_EX=(
  --exclude '.git'
  --exclude '*.gdoc'
  --exclude '*.env'
  --exclude 'cloudflare*.env'
  --exclude 'groq.env'
  --exclude 'gemini.env'
  --exclude 'aws*.env'
  --exclude 'slave_keys.env'
  --exclude '**/secrets/**'
  --exclude '**/*.key'
  --exclude '**/agent-transcripts/**'
  --exclude 'aws_key_drop.txt'
  --exclude 'lester_keys*.md'
  --exclude '*lester_keys*'
  --exclude 'CLOUDFLARE_API_PASTE.txt'
  --exclude 'node_modules'
  --exclude 'venv'
  --exclude 'venv-*'
  --exclude '__pycache__'
  --exclude '.cache'
  --exclude '*.log'
)

# Strip files that still contain live credentials (git push protection).
scrub_secrets() {
  local dir="$1"
  [ -d "$dir" ] || return 0
  local n=0
  while IFS= read -r -d '' f; do
    rm -f "$f"
    n=$((n + 1))
  done < <(grep -rIlE \
    'AKIA[0-9A-Z]{16}|gsk_[a-zA-Z0-9]{20,}|AWS_SECRET_ACCESS_KEY|CLOUDFLARE.*API.*TOKEN' \
    "$dir" 2>/dev/null | tr '\n' '\0')
  [ "$n" -gt 0 ] && echo "  scrubbed $n secret file(s) from $dir"
}

preserve_pair() {
  local src="$1" sub="$2"
  [ -d "$src" ] || return 0
  mkdir -p "$DEST/$sub"
  set +e
  rsync -a "${RSYNC_EX[@]}" "$src"/ "$DEST/$sub"/
  code=$?
  set -e
  if [ "$code" -ne 0 ] && [ "$code" -ne 23 ]; then
    return "$code"
  fi
  [ "$code" -eq 23 ] && echo "  warn: partial (fuse/gdoc ok): $sub"
  echo "  copied: $src -> $DEST/$sub ($(du -sh "$DEST/$sub" 2>/dev/null | cut -f1))"
}

case "$NAME" in
  puppy)
    preserve_pair "$HOME/bunny/workspace" "workspace"
    ;;
  cb2)
    FUSE="/mnt/shared/GoogleDrive/MyDrive"
    if [ ! -d "$FUSE/lester" ] && [ -d "$HOME/GoogleDrive/MyDrive/lester" ]; then
      FUSE="$HOME/GoogleDrive/MyDrive"
    fi
    echo "preserve cb2 · fuse=$FUSE · no secrets · copy only"
    preserve_pair "$FUSE/lester" "lester"
    preserve_pair "$FUSE/drop_pile" "drop_pile"
    preserve_pair "$FUSE/fleet" "drive-fleet"
    preserve_pair "$FUSE/gl" "gl"
    preserve_pair "$HOME/lester" "lester-local"
    preserve_pair "$HOME/.stan" "stan"
    scrub_secrets "$DEST"
    ;;
  *)
    echo "no SRCS for: $NAME"
    exit 1
    ;;
esac

git add "$DEST"
git commit -q -m "preserve: $NAME all projects (no secrets · copy only)" || true
git push -q
echo "preserved -> $DEST"
du -sh "$DEST" 2>/dev/null
