#!/usr/bin/env bash
# Word: LOOP — Bunny done with job · restart fuse writer · one pulse now
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"
LOG="${HOME}/bbuny_loop.log"
pkill -f 'bbunny_loop.sh' 2>/dev/null || true
sleep 1
bash "$DIR/bbunny_loop.sh" once >>"$LOG" 2>&1
nohup bash "$DIR/bbunny_loop.sh" >>"$LOG" 2>&1 &
echo "LOOP ok — $(date -Iseconds) · FROM_BUNNY pulse sent"
