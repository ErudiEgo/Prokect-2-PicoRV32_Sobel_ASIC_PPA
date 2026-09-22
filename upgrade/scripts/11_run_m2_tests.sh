#!/usr/bin/env bash
# USER-RUN ONLY: executes actual CPU RTL after precheck.
set -euo pipefail
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$ROOT"
export PYTHONDONTWRITEBYTECODE=1
bash scripts/10_precheck_m2.sh
exec python3 scripts/run_m2_tests.py "$@"
