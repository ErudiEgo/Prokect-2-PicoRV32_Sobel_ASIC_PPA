#!/usr/bin/env bash
# USER-RUN ONLY. Five remaining M2 workloads, sequential, never overwrite.
set -euo pipefail
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$ROOT"
export PYTHONDONTWRITEBYTECODE=1
bash scripts/10_precheck_m2.sh
python3 scripts/finish_m2.py
