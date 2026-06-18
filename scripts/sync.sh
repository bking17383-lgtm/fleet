#!/usr/bin/env bash
# Pull the fleet and show the current orders. (the "orders" command)
cd "$HOME/fleet" 2>/dev/null || { echo "no ~/fleet here"; exit 1; }
git pull -q --no-edit 2>/dev/null || true
echo "===================== ORDERS ====================="
grep '^STATUS:' bus/CONTROL.md
echo "--------------------------------------------------"
echo "goals: bus/GOALS.md   |   full control: bus/CONTROL.md"
echo "after you act, run:  ./scripts/heartbeat.sh <name> \"what I did\""
echo "=================================================="
