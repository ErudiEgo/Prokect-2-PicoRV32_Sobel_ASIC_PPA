#!/usr/bin/env bash
# USER-RUN ONLY: frozen inputs, five units and four real CPU executions.
set -euo pipefail
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$ROOT"
export PYTHONDONTWRITEBYTECODE=1
python3 scripts/22_precheck_m3.py
python3 scripts/run_m3_tests.py "$@"
python3 scripts/audit_m3.py "reports/${1:?RUN name required}"
