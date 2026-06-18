#!/usr/bin/env bash
# Standard Camel — terminal edition (Drive-safe launcher)
cd "$(dirname "$(readlink -f "$0" 2>/dev/null || echo "$0")")"
exec python3 camel_clicker.py "$@"
