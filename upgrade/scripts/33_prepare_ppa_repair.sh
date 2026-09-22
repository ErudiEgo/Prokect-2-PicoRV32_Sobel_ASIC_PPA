#!/usr/bin/env bash
# Static-only preparation; the separate 31_run_ppa.sh launches the user flow.
set -euo pipefail
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
exec python3 -B "$ROOT/physical/prepare_repair_pair.py" "$@"
