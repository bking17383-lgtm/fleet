#!/usr/bin/env bash
# Pull any MyDrive file via penguin HTTP drop lane (no fuse required on this box).
# Usage: fleet_fetch.sh <path-under-MyDrive> [outfile]
set -euo pipefail
REL="${1:?path under MyDrive — e.g. drop_pile/from_bbbunny/foo.mp3}"
OUT="${2:-$(basename "$REL")}"
BASE="${FLEET_FETCH_BASE:-https://hitme.dev/f}"
URL="${BASE}/${REL#/}"
echo "GET $URL -> $OUT"
curl -fL "$URL" -o "$OUT"
ls -lh "$OUT"
