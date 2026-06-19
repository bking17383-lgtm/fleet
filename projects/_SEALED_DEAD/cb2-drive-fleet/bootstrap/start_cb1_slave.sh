#!/usr/bin/env bash
# CB1 slave — already on cb1 · idempotent start
set -euo pipefail
bash "${HOME}/.stan/cb1_slave_loop.sh"
bash "${HOME}/.stan/gem_bunny_ears.sh"
