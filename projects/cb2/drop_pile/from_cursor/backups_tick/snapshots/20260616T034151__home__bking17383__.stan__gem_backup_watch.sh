#!/usr/bin/env bash
# Gem interrupt-safe backup — rolling copy every few seconds to Drive.
set -euo pipefail

STAN="${HOME}/.stan"
MANIFEST="${STAN}/gem_backup_manifest.txt"
INTERVAL="${GEM_BACKUP_SEC:-5}"
BUS="/mnt/shared/GoogleDrive/MyDrive"
[[ -d "${BUS}" ]] || BUS="${HOME}/GoogleDrive/MyDrive"
DEST="${BUS}/drop_pile/from_cursor/backups_tick"
LOG="${STAN}/logs/gem_backup_watch.log"
PIDFILE="${STAN}/gem_backup_watch.pid"

mkdir -p "${STAN}/logs" "${DEST}/latest" "${DEST}/snapshots"

if [[ "${1:-}" == "stop" ]]; then
  if [[ -f "${PIDFILE}" ]] && kill -0 "$(cat "${PIDFILE}")" 2>/dev/null; then
    kill "$(cat "${PIDFILE}")" && rm -f "${PIDFILE}"
    echo "stopped gem_backup_watch pid $(cat "${PIDFILE}" 2>/dev/null || echo ?)"
  else
    rm -f "${PIDFILE}"
    echo "not running"
  fi
  exit 0
fi

if [[ "${1:-}" == "status" ]]; then
  if [[ -f "${PIDFILE}" ]] && kill -0 "$(cat "${PIDFILE}")" 2>/dev/null; then
    echo "running pid=$(cat "${PIDFILE}") interval=${INTERVAL}s dest=${DEST}"
    tail -3 "${LOG}" 2>/dev/null || true
  else
    echo "not running"
  fi
  exit 0
fi

if [[ -f "${PIDFILE}" ]] && kill -0 "$(cat "${PIDFILE}")" 2>/dev/null; then
  echo "already running pid=$(cat "${PIDFILE}")" >&2
  exit 0
fi

backup_once() {
  local now tick src base rel
  now="$(date -Iseconds)"
  tick="$(date +%Y%m%dT%H%M%S)"
  [[ -f "${MANIFEST}" ]] || return 0
  while IFS= read -r src || [[ -n "${src}" ]]; do
    src="${src%%#*}"
    src="$(echo "${src}" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
    [[ -z "${src}" ]] && continue
    [[ -f "${src}" ]] || continue
    base="$(basename "${src}")"
    rel="${src#/}"
    rel="${rel//\//__}"
    cp -f "${src}" "${DEST}/latest/${rel}"
    cp -f "${src}" "${DEST}/snapshots/${tick}__${rel}"
  done < "${MANIFEST}"
  printf '%s ok tick=%s files=%s\n' "${now}" "${tick}" "$(find "${DEST}/latest" -type f 2>/dev/null | wc -l | tr -d ' ')" >> "${LOG}"
  find "${DEST}/snapshots" -type f -mmin +120 2>/dev/null | head -n -500 | xargs -r rm -f
}

echo $$ > "${PIDFILE}"
echo "$(date -Iseconds) start interval=${INTERVAL}s dest=${DEST}" >> "${LOG}"
trap 'rm -f "${PIDFILE}"; exit 0' INT TERM EXIT

while true; do
  backup_once || echo "$(date -Iseconds) backup error" >> "${LOG}"
  sleep "${INTERVAL}"
done
