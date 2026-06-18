#!/usr/bin/env bash
# One command to talk to the fleet — no app store needed.
TALK="${HOME}/GoogleDrive/MyDrive/TALK.txt"
[[ -f "$TALK" ]] || TALK="/mnt/shared/GoogleDrive/MyDrive/TALK.txt"
[[ -f "$TALK" ]] || { echo "TALK.txt not found on Drive"; exit 1; }
exec nano "$TALK"
