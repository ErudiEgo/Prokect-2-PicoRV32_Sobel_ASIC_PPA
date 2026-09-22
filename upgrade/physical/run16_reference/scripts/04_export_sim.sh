#!/usr/bin/env bash
# Collects EXISTING evidence only; never launches a simulation.
set -euo pipefail
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
TAG=${1:?Usage: bash scripts/04_export_sim.sh RUN_NAME}
[[ "$TAG" =~ ^[A-Za-z0-9][A-Za-z0-9_-]{0,79}$ ]] || { echo 'Invalid RUN name' >&2; exit 1; }
DEST='/mnt/e/aa. PPA_Project_List/aaa.PicoRV32_Sobel_ASIC_PPA/reports'
[[ -f "$ROOT/reports/$TAG.zip" ]] || { echo 'Archive missing. Check the simulation command first.' >&2; exit 1; }
mkdir -p "$DEST"
[[ ! -e "$DEST/$TAG.zip" ]] || { echo 'Destination exists; refusing overwrite.' >&2; exit 1; }
# Exclusive destination creation also protects against an intervening copy.
python3 - "$ROOT/reports/$TAG.zip" "$DEST/$TAG.zip" <<'PY'
import shutil, sys
with open(sys.argv[1], 'rb') as source, open(sys.argv[2], 'xb') as target:
    shutil.copyfileobj(source, target)
PY
printf 'EXPORTED: %s/%s.zip\nNo simulation rerun.\n' "$DEST" "$TAG"
