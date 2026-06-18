#!/usr/bin/env bash
# One-time AWS sandbox deps + probe (after aws_sandbox.env filled)
set -euo pipefail
pip3 install --user boto3 botocore 2>/dev/null || pip3 install boto3 botocore
python3 "${HOME}/.stan/aws_sandbox_probe.py"
