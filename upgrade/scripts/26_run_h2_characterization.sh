#!/usr/bin/env bash
# USER-RUN ONLY. No physical flow. pilot first; large requires audited pilot RUNs.
set -euo pipefail
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$ROOT"
export PYTHONDONTWRITEBYTECODE=1
python3 scripts/h2_characterization.py --precheck
python3 scripts/22_precheck_m3.py
exec python3 scripts/h2_characterization.py "${1:-pilot}"
