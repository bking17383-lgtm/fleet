#!/usr/bin/env bash
# Park all game / card-app UI on CB2. Execute lives on puppy64; games on CB1.
set -euo pipefail

STAN="${HOME}/.stan"
PARK="${STAN}/parked/baseball_cards_cb2"
FLAG="${STAN}/CB2_NO_GAMES"
DRIVE="/mnt/shared/GoogleDrive/MyDrive"
[[ -d "${HOME}/GoogleDrive/MyDrive" ]] && DRIVE="${HOME}/GoogleDrive/MyDrive"

echo "[*] CB2 game clean — stopping servers…"
pkill -f "app_baseball.py" 2>/dev/null || true
pkill -f "cloudflared tunnel.*8002" 2>/dev/null || true
pkill -f "cloudflared tunnel --protocol http2 --url http://127.0.0.1:8002" 2>/dev/null || true
sleep 1

APP="${HOME}/Applications/cursor/baseball_cards"
if [[ -d "$APP" ]]; then
  mkdir -p "${STAN}/parked"
  rm -rf "$PARK"
  mv "$APP" "$PARK"
  echo "[*] Parked local app → $PARK"
fi

: >"$FLAG"
date -Iseconds >>"$FLAG"

for pid in baseball_cb2.pid baseball_tunnel.pid; do
  rm -f "${STAN}/${pid}" 2>/dev/null || true
done

# Leave mesh radio (:8765) — fleet comms, not a game.

NOW="$(date -Iseconds)"
mkdir -p "$DRIVE/fleet" "$DRIVE/drop_pile/from_lester"
cat >"$DRIVE/fleet/CB2_NO_GAMES.txt" <<EOF
CB2 — NO GAMES (parked)
Updated: $NOW

Brian asked: this machine is design desk only. No game/card UI popping on sync.

Parked on CB2 Linux:
  ~/.stan/parked/baseball_cards_cb2  (was Applications/cursor/baseball_cards)

Blocked scripts (exit early if CB2_NO_GAMES flag exists):
  ~/.stan/cloudflare_cb2.sh
  ~/.stan/start_baseball_tunnel.sh
  ~/Applications/cursor/baseball_cards/start_baseball.sh

Still live elsewhere:
  puppy64 — baseball + execute (when Brian revives)
  CB1 — CAMEL game (when Brian says CAMEL)

To revive baseball on CB2 only: rm ~/.stan/CB2_NO_GAMES && bash ~/.stan/clean_games_cb2.sh --restore
EOF

cat >"$DRIVE/drop_pile/from_lester/cb2_games_parked.md" <<EOF
--- cb2 games parked ---
time: $NOW
action: clean_games_cb2.sh
reason: Brian — game popped while syncing text editor
local: moved to ~/.stan/parked/baseball_cards_cb2
servers: app_baseball :8002 stopped · baseball tunnel stopped
mesh_radio: untouched (:8765 fleet comms)
EOF

echo "[*] Wrote fleet/CB2_NO_GAMES.txt"
echo "OK — CB2 is game-free. Design desk only."
