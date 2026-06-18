#!/usr/bin/env bash
# Install Google Cloud SDK on penguin (once)
set -euo pipefail
DEST="${HOME}/google-cloud-sdk"
if [[ -x "${DEST}/google-cloud-sdk/bin/gcloud" ]]; then
  echo "gcloud already installed"
  exit 0
fi
curl -fsSL https://sdk.cloud.google.com | bash -s -- --disable-prompts --install-dir="${DEST}"
echo "OK — use: ${HOME}/.stan/gcloud"
