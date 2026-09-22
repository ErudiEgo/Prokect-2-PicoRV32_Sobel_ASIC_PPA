#!/usr/bin/env bash
# USER-RUN ONLY: launches real RTL simulation, then checks real output.
set -euo pipefail
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$ROOT"
export PYTHONDONTWRITEBYTECODE=1
exec python3 scripts/run_soc_tests.py "$@"
