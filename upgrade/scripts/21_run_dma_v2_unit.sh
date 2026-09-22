#!/usr/bin/env bash
# USER-RUN ONLY: independent candidate unit simulation, no CPU or OpenLane.
set -euo pipefail
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$ROOT"
export PYTHONDONTWRITEBYTECODE=1
bash scripts/20_precheck_dma_v2.sh
exec python3 scripts/run_dma_v2_unit.py "$@"
