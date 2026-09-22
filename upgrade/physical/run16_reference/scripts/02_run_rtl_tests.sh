#!/usr/bin/env bash
# USER-RUN entry point. Never invoked automatically by precheck or copy.
set -euo pipefail
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
command -v iverilog >/dev/null || { echo 'ERROR: Install iverilog in Ubuntu first.' >&2; exit 1; }
command -v vvp >/dev/null
mkdir -p "$ROOT/build"
OUT=$(mktemp -d "$ROOT/build/sobel_unit_XXXXXXXX")
mkdir "$OUT/inputs"
cp -- "$ROOT/rtl/sobel_core.v" "$ROOT/tb/tb_sobel_core.sv" "$OUT/inputs/"
cd "$OUT"
sha256sum inputs/* > inputs.sha256
iverilog -g2012 -Wall -Wno-timescale -s tb_sobel_core -o sim.vvp inputs/sobel_core.v inputs/tb_sobel_core.sv 2>&1 | tee compile.log
vvp sim.vvp "$@" 2>&1 | tee simulation.log
grep -qx 'TEST PASS: sobel_core 1283 vectors; latency, busy, done, reset checked' simulation.log
printf 'UNIT TEST evidence: %s\nThis is Sobel-only evidence, not a CPU or ASIC PASS.\n' "$OUT"
