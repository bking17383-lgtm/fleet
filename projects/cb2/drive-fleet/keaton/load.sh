#!/usr/bin/env bash
# KEATON loader — read INDEX + box file · start allowed projects only
set -euo pipefail
DRIVE="/mnt/shared/GoogleDrive/MyDrive"
[[ -d "$HOME/GoogleDrive/MyDrive" ]] && DRIVE="$HOME/GoogleDrive/MyDrive"
ROOT="${DRIVE}/fleet/keaton"
BOX="${FLEET_BOX_ID:-$(cat "$HOME/.stan/FLEET_BOX_ID" 2>/dev/null || echo unknown)}"
BOXFILE="${ROOT}/boxes/${BOX}.txt"
INDEX="${ROOT}/INDEX.txt"
ONE="${1:-all}"

[[ -f "$BOXFILE" ]] || { echo "NO BOX FILE: $BOXFILE"; exit 1; }

allowed() {
  grep -E '^may_start:' "$BOXFILE" | sed 's/may_start: //'
}

start_project() {
  local id="$1" port cmd
  case "$id" in
    cards)
      port=8002
      cmd="bash ${DRIVE}/lester/baseball_cards/start_baseball.sh"
      ;;
    hitme)
      port=8770
      cmd="python3 ${HOME}/.stan/hitme_who_server.py"
      ;;
    sarah)
      port=8766
      cmd="python3 ${HOME}/.stan/sarah_voice_sample.py"
      ;;
    gem-studio)
      port=8888
      cmd="python3 ${HOME}/gem-studio/server.py"
      ;;
    *)
      echo "  skip unknown: $id"
      return 0
      ;;
  esac
  if curl -sf -m 2 "http://127.0.0.1:${port}/" >/dev/null 2>&1 || \
     curl -sf -m 2 "http://127.0.0.1:${port}/health" >/dev/null 2>&1 || \
     curl -sf -m 2 "http://127.0.0.1:${port}/api/health" >/dev/null 2>&1; then
    echo "  $id:$port already UP"
    return 0
  fi
  echo "  starting $id:$port"
  nohup bash -c "$cmd" >>"${HOME}/.stan/logs/keaton_${id}.log" 2>&1 &
}

echo "KEATON load box=$BOX one=$ONE"
MAY=$(allowed)
if [[ "$ONE" != "all" ]]; then
  echo "$MAY" | grep -qw "$ONE" || { echo "FORBIDDEN: $ONE on $BOX"; exit 1; }
  start_project "$ONE"
  exit 0
fi
for id in $MAY; do
  [[ "$id" == "—" || "$id" == "tunnel_only" ]] && continue
  start_project "$id"
done
echo "done — see fleet/keaton/HITME_LOCK.txt before hitme changes"
