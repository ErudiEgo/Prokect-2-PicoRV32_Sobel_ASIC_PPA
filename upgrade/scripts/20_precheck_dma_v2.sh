#!/usr/bin/env bash
# Compile only: no vvp, CPU execution, synthesis or OpenLane.
set -euo pipefail
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$ROOT"
export PYTHONDONTWRITEBYTECODE=1
python3 scripts/static_check.py
mkdir -p build
OUT=$(mktemp -d "$ROOT/build/dma_v2_static_XXXXXXXX")
iverilog -g2012 -Wall -Wno-timescale -s tb_sobel_tile_v2 \
    -o "$OUT/unit.vvp" rtl/sobel_core.v candidate/sobel_tile_v2.v \
    candidate/tb_sobel_tile_v2.sv 2>&1 | tee "$OUT/compile.log"
sha256sum rtl/sobel_core.v candidate/*.v candidate/*.sv > "$OUT/inputs.sha256"
printf 'DMA V2 COMPILE PASS; functional status NOT_RUN.\nEvidence: %s\n' "$OUT"
