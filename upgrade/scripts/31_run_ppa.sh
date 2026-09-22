#!/usr/bin/env bash
# USER RUN ONLY. Full OpenLane Classic execution, no automatic resume.
set -euo pipefail
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
exec python3 -B "$ROOT/physical/ppa.py" run "$@"
