#!/usr/bin/env bash
# cb2 local rail — Spark (Gemini Lester6) vs linux-loop (box_slave_loop). No tokens.
set -euo pipefail

DRIVE=""
for d in /mnt/shared/GoogleDrive/MyDrive "$HOME/GoogleDrive/MyDrive"; do
  [[ -d "$d/fleet" ]] && DRIVE="$d" && break
done
[[ -n "$DRIVE" ]] || exit 0

ACK="$DRIVE/drop_pile/from_lester/lester6_to_daddy.md"
HB="$DRIVE/drop_pile/from_lester/cb2_heartbeat.md"
JOB_DIR="$DRIVE/drop_pile/to_lester"
AWS="$DRIVE/drop_pile/from_lester/aws_sandbox.env"
OUT="$HOME/.cache/cb2-rail.txt"
mkdir -p "$(dirname "$OUT")"

now_epoch() { date +%s; }

file_age_sec() {
  local f=$1
  [[ -f "$f" ]] || { echo 999999; return; }
  echo $(( $(now_epoch) - $(stat -c %Y "$f" 2>/dev/null || echo 0) ))
}

# --- Spark (Gemini developer / Lester6) — NOT the linux loop ---
spark_state="OFF"
spark_detail=""
if [[ -f "$ACK" ]]; then
  body=$(tr '[:upper:]' '[:lower:]' <"$ACK")
  age=$(file_age_sec "$ACK")
  if grep -q 'slave: live on penguin' <<<"$body" && ! grep -q 'callsign:' <<<"$body"; then
    spark_state="FAKE"
    spark_detail="old linux stamp"
  elif grep -qE 'spark:[[:space:]]*live' <<<"$body"; then
    if (( age <= 1800 )); then spark_state="LIVE"; else spark_state="STALE"; fi
    spark_detail="${age}s"
  elif grep -qE 'callsign:[[:space:]]*beacon' <<<"$body" && grep -qE 'mode:[[:space:]]*slave' <<<"$body"; then
    spark_state="BOUND"
    spark_detail="no spark:live yet · ${age}s"
  elif grep -qE '^done:|^need:' <<<"$body"; then
    if (( age <= 3600 )); then spark_state="LIVE"; else spark_state="STALE"; fi
    spark_detail="${age}s"
  else
    spark_state="STALE"
    spark_detail="${age}s"
  fi
fi

# --- linux-loop (box_slave_loop on penguin) — Drive executor ping, NOT Spark ---
loop_state="OFF"
if pgrep -f 'box_slave_loop.py daddy' >/dev/null 2>&1; then
  loop_state="live"
else
  loop_state="dead"
fi

# --- current job (newest to_lester brief) ---
job="none"
if [[ -d "$JOB_DIR" ]]; then
  newest=$(find "$JOB_DIR" -maxdepth 1 -name '*.md' -type f -printf '%T@ %f\n' 2>/dev/null | sort -rn | head -1 | cut -d' ' -f2-)
  [[ -n "$newest" ]] && job="${newest%.md}"
fi

aws_state="WAIT"
[[ -f "$AWS" ]] && aws_state="READY"
[[ -f "$HOME/.stan/aws_sandbox.env" ]] && aws_state="LOCAL"

{
  printf 'spark:%s · loop:%s · job:%s · aws:%s\n' "$spark_state" "$loop_state" "$job" "$aws_state"
  printf 'Spark=Lester6 Gemini dev · loop=linux box_slave · ack=%s\n' "$(basename "$ACK")"
} >"$OUT"
