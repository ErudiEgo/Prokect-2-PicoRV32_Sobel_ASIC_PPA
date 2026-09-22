#!/usr/bin/env bash
# USER-RUN ONLY. Six integration regressions; preserves all existing evidence.
set -euo pipefail
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$ROOT"
export PYTHONDONTWRITEBYTECODE=1
python3 scripts/22_precheck_m3.py
python3 scripts/finish_m3.py
