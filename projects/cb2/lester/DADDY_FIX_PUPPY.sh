#!/usr/bin/env bash
# Daddy pushed this to puppy uploaded_files via :8002 — run on puppy ONLY
set -euo pipefail
DIR="/mnt/shared/GoogleDrive/MyDrive/lester/uploaded_files"
[[ -d "$DIR" ]] || DIR="$(dirname "$0")"
bash "$DIR/PUPPY_ONE_COMMAND.sh"
