#!/usr/bin/env bash
# Existing reports only; never rerun the flow to collect evidence.
set -euo pipefail
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
exec python3 -B "$ROOT/physical/ppa.py" collect "$@"
