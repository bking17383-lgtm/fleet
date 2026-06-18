#!/usr/bin/env bash
# Daddy watches Bunny indie loop — FROM_BUNNY.txt every 30s · writes FROM_DADDY.txt
set -euo pipefail
STAN="${HOME}/.stan"
PY="${STAN}/daddy_indie_status.py"
LOG="${STAN}/logs/cpt_bunny_watch.log"
mkdir -p "$(dirname "$LOG")"

DRIVE=$(python3 -c "import sys; sys.path.insert(0,'${STAN}'); from bus_lane import bus_root; print(bus_root())")
FROM="${DRIVE}/fleet/indie_loop/FROM_BUNNY.txt"
TO="${DRIVE}/fleet/indie_loop/TO_BUNNY.txt"
ACK="${DRIVE}/fleet/bus/cpt_ack_bunny.txt"
LAB="${DRIVE}/fleet/bus/LAB_REPLY.txt"
KEATON_OK="${DRIVE}/drop_pile/from_bbbunny/KEATON_SOUND_OK.txt"
KEATON_HTML="${DRIVE}/drop_pile/from_bbbunny/keaton.html"
LANDING_LIVE="${DRIVE}/fleet/keaton/LANDING_LIVE.txt"
CPT_KEATON="${DRIVE}/fleet/bus/CPT_KEATON_LANDING.txt"
DONE_DIR="${DRIVE}/drop_pile/done"
LOOP_POKE="${DRIVE}/drop_pile/to_bbbunny/LOOP.txt"
LOOP_STATE="${STAN}/logs/bunny_loop_poked.txt"
last=""
tick=0

while true; do
  tick=$((tick + 1))
  if ! python3 "$PY" once >>"$LOG" 2>&1; then
    ts=$(date -Iseconds)
    echo "$ts indie_status ERR tick=$tick" >>"$LOG"
  fi
  cur=$(head -1 "$FROM" 2>/dev/null || echo missing)
  ts=$(date -Iseconds)
  echo "$ts tick=$tick FROM_BUNNY=$cur" >>"$LOG"
  if [[ -f "$KEATON_OK" && -f "$KEATON_HTML" && ! -f "$LANDING_LIVE" ]]; then
    ts=$(date -Iseconds)
    mkdir -p "$(dirname "$LANDING_LIVE")"
    {
      echo "LANDING_LIVE — $ts"
      echo "gate: KEATON_SOUND_OK.txt + keaton.html"
      echo "root: hitme.dev / → /keaton"
      echo "backend-only until visitors ready"
    } > "$LANDING_LIVE"
    {
      echo "CPT ORDER — Keaton landing"
      echo "TIME: $ts"
      echo "STATUS: LIVE"
      echo "root: /keaton"
    } > "$CPT_KEATON"
    {
      echo "$ts"
      echo "Keaton landing LIVE — Bunny sound OK. hitme.dev / → /keaton"
    } > "$LAB"
    echo "$ts KEATON_LANDING_LIVE written" >> "$LOG"
  fi
  # Bunny done audio landed → poke LOOP (once per mp3)
  if [[ -d "$DONE_DIR" ]]; then
    newest=$(ls -t "$DONE_DIR"/*.mp3 2>/dev/null | head -1 || true)
    if [[ -n "${newest:-}" && -f "$newest" ]]; then
      key=$(basename "$newest" .mp3)
      mtime=$(stat -c %Y "$newest" 2>/dev/null || echo 0)
      now=$(date +%s)
      poked=""
      [[ -f "$LOOP_STATE" ]] && poked=$(grep -F "$key:" "$LOOP_STATE" 2>/dev/null | tail -1 || true)
      if (( now - mtime < 600 )) && [[ "$poked" != *"$mtime"* ]]; then
        mkdir -p "$(dirname "$LOOP_POKE")"
        {
          echo "LOOP"
          echo "time: $ts"
          echo "trigger: done/$key.mp3"
          echo "run: bash ~/GoogleDrive/MyDrive/lester/bunny_loop_fix.sh"
          echo "fetch: curl -fLO https://hitme.dev/f/lester/bunny_loop_fix.sh"
        } > "$LOOP_POKE"
        echo "${key}:${mtime}" >> "$LOOP_STATE"
        echo "$ts LOOP poke → $LOOP_POKE (done/$key.mp3)" >> "$LOG"
      fi
    fi
  fi
  if [[ -n "$cur" && "$cur" != "waiting for bunny" && "$cur" != "$last" ]]; then
    mkdir -p "$(dirname "$ACK")" "$(dirname "$LAB")"
    {
      echo "CPT_ACK_BUNNY — $ts"
      echo "from: Daddy · penguin · watch"
      echo "status: BUNNY_LIVE"
      echo "head: $cur"
      head -8 "$FROM" 2>/dev/null | sed 's/^/  /'
    } > "$ACK"
    {
      echo "$ts"
      echo "Bunny answered on drop loop. FROM_BUNNY updated — see cpt_ack_bunny.txt."
    } > "$LAB"
    last="$cur"
    echo "$ts BUNNY_LIVE ack written" >> "$LOG"
  fi
  sleep 30
done
