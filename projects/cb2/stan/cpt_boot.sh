#!/usr/bin/env bash
# CPT boot + slave (one shot)
set -euo pipefail
python3 "${HOME}/.stan/cpt_slave.py"
