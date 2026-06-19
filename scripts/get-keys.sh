#!/usr/bin/env bash
# GET KEYS — set up this machine's keys. Keys are made LOCALLY and NEVER touch the repo.
#   usage: ./get-keys.sh <machine-name>     e.g. ./get-keys.sh puppy
set -e
NAME="${1:-$(hostname)}"
echo "== Keys for: $NAME =="
echo "(Keys stay hidden on this machine. Nothing secret is ever pushed.)"
echo

# --- 1. GitHub SSH key (to pull/push the repo) ---
KEY="$HOME/.ssh/fleet_key"
mkdir -p ~/.ssh && chmod 700 ~/.ssh
if [ -f "$KEY" ]; then
  echo "[github] key already here ($KEY) — reusing it. Good."
else
  ssh-keygen -t ed25519 -f "$KEY" -N "" -C "$NAME-fleet"
  echo "[github] new key made."
fi
# point git at this key
if ! grep -q "Host github.com" ~/.ssh/config 2>/dev/null; then
  printf 'Host github.com\n  HostName github.com\n  User git\n  IdentityFile %s\n  IdentitiesOnly yes\n' "$KEY" >> ~/.ssh/config
  chmod 600 ~/.ssh/config
fi
echo
echo ">>> ADD THIS ONE LINE at github.com -> Settings -> SSH and GPG keys -> New SSH key"
echo "    (title it: $NAME)"
echo "------------------------------------------------------------------------------"
cat "$KEY.pub"
echo "------------------------------------------------------------------------------"
echo "Then test:  ssh -T git@github.com   (look for: successfully authenticated)"

# --- 2. Cursor API key (only if the agent hits the ~1-min browser-login timeout) ---
echo
echo "== Cursor key (headless login — skips the browser popup that times out) =="
echo "Get one: cursor.com -> Settings -> API Keys  (on the bking account)."
echo "Then on THIS machine (never paste it into a repo file):"
echo "    echo 'export CURSOR_API_KEY=your_key_here' >> ~/.bashrc && source ~/.bashrc"
echo
echo "Done. Private keys live ONLY here (~/.ssh and your shell) — never in git."
