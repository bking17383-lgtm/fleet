#!/usr/bin/env bash
# Run ONCE on any machine to join the fleet.
#   usage: ./connect-machine.sh <shortname>   e.g. ./connect-machine.sh cb2
set -e
REPO="git@github.com:bking17383-lgtm/fleet.git"
NAME="${1:-$(hostname)}"

# 1. ensure git
command -v git >/dev/null || sudo apt-get install -y git

# 2. per-machine ssh key for github
KEY="$HOME/.ssh/fleet_key"
mkdir -p ~/.ssh && chmod 700 ~/.ssh
[ -f "$KEY" ] || ssh-keygen -t ed25519 -f "$KEY" -N "" -C "$NAME"
if ! grep -q "Host github.com" ~/.ssh/config 2>/dev/null; then
  printf 'Host github.com\n    HostName github.com\n    User git\n    IdentityFile %s\n    IdentitiesOnly yes\n' "$KEY" >> ~/.ssh/config
  chmod 600 ~/.ssh/config
fi

echo ""
echo ">>> ADD THIS PUBLIC KEY at github.com -> Settings -> SSH and GPG keys (title: $NAME)"
echo "-------------------------------------------------------------------------------"
cat "$KEY.pub"
echo "-------------------------------------------------------------------------------"
read -p "Press ENTER once the key is added on GitHub... "

# 3. clone or update
if [ -d "$HOME/fleet/.git" ]; then
  cd "$HOME/fleet" && git pull
else
  git clone "$REPO" "$HOME/fleet"
fi
echo "Joined the fleet. Repo at ~/fleet  (machine name: $NAME)"
