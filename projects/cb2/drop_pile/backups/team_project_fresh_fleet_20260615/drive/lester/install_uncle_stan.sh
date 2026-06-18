#!/usr/bin/env bash
# Install Uncle/CB1 stan tools from Drive + refresh fleet board
set -euo pipefail
DRIVE="${HOME}/GoogleDrive/MyDrive"
[[ -d /mnt/shared/GoogleDrive/MyDrive ]] && DRIVE="/mnt/shared/GoogleDrive/MyDrive"
STAN="${HOME}/.stan"
mkdir -p "$STAN"
cp -f "$DRIVE/lester/fleet_board.py" "$STAN/fleet_board.py"
cat >"$STAN/fleet_desk.sh" <<'EOF'
#!/usr/bin/env bash
python3 "$HOME/.stan/fleet_board.py"
EOF
chmod +x "$STAN/fleet_desk.sh" "$STAN/fleet_board.py"
RULES="${HOME}/.cursor/rules"
mkdir -p "$RULES"
if [[ -f "$DRIVE/lester/cursor_rules/uncle-voice.mdc" ]]; then
  cp -f "$DRIVE/lester/cursor_rules/uncle-voice.mdc" "$RULES/uncle-voice.mdc"
  echo "OK: Uncle personality rule → $RULES/uncle-voice.mdc"
fi
python3 "$STAN/fleet_board.py"
echo "OK: fleet board refreshed"
