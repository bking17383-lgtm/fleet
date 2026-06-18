#!/usr/bin/env bash
# CB1 only — rename Crostini from penguin → cb1 (new Crostini still defaults penguin)
set -euo pipefail
STAN="${HOME}/.stan"
mkdir -p "$STAN"
echo cb1 > "${STAN}/FLEET_BOX_ID"
chmod 600 "${STAN}/FLEET_BOX_ID"

if [[ "$(hostname -s)" == "cb1" ]]; then
  echo "hostname already cb1 · FLEET_BOX_ID ok"
  exit 0
fi

if [[ "$(hostname -s)" != "penguin" ]]; then
  echo "REFUSE — expected penguin before rename · got $(hostname -s)" >&2
  echo "Run on CB1 only · Daddy CB2 keeps penguin" >&2
  exit 2
fi

sudo hostnamectl set-hostname cb1
sudo sed -i 's/\bpenguin\b/cb1/g' /etc/hosts
grep -q '127.0.1.1 cb1' /etc/hosts || echo '127.0.1.1 cb1' | sudo tee -a /etc/hosts >/dev/null
echo "cb1 hostname set · reopen terminal or restart Cursor to pick up"
