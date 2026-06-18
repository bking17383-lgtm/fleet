#!/usr/bin/env bash
# The one-word "orders" brain. Each machine runs:  ./scripts/order.sh <name>
# It looks up THIS machine's job in bus/orders.txt and runs it. Read-only by default.
NAME="${1:-$(hostname)}"
cd "$HOME/fleet" || { echo "no ~/fleet here"; exit 1; }
git pull -q --no-edit 2>/dev/null || true
TASK=$(grep -E "^${NAME}:" bus/orders.txt 2>/dev/null | head -1 | cut -d: -f2- | tr -d ' ')
echo "machine: $NAME   task: ${TASK:-none}"
case "$TASK" in
  scan)     ./scripts/projects.sh "$NAME" ;;
  preserve) ./scripts/save-projects.sh "$NAME" ;;
  wait)     echo "standing by — no action." ;;
  *)        echo "no task set for $NAME in bus/orders.txt — doing nothing." ;;
esac
