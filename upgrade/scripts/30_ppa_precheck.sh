#!/usr/bin/env bash
# Static preparation only. No RTL simulation, synthesis or physical flow.
set -euo pipefail
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
exec python3 -B "$ROOT/physical/ppa.py" precheck "$@"
