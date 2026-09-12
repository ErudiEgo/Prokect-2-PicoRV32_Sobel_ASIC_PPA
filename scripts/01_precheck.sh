#!/usr/bin/env bash
# Static compilation only. Does not execute vvp, firmware or OpenLane.
set -euo pipefail
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
command -v iverilog >/dev/null || { echo 'ERROR: iverilog missing.' >&2; exit 1; }
mkdir -p "$ROOT/build"
OUT=$(mktemp -d "$ROOT/build/static_XXXXXXXX")
cd "$ROOT"
iverilog -g2012 -Wall -Wno-timescale -s tb_sobel_core -o "$OUT/sobel_compile.vvp" \
    rtl/sobel_core.v tb/tb_sobel_core.sv 2>&1 | tee "$OUT/sobel_compile.log"
iverilog -g2012 -Wall -Wno-timescale -s tb_sobel_mmio -o "$OUT/mmio_compile.vvp" \
    rtl/sobel_core.v rtl/sobel_mmio.v tb/tb_sobel_mmio.sv 2>&1 | tee "$OUT/mmio_compile.log"
for variant in 0 1; do
    iverilog -g2012 -Wall -Wno-timescale -s tb_sobel_soc \
        -Ptb_sobel_soc.ENABLE_SOBEL="$variant" -o "$OUT/soc_$variant.vvp" \
        rtl/sobel_core.v rtl/sobel_mmio.v rtl/picorv32_sobel_soc.v \
        third_party/picorv32/picorv32.v tb/tb_sobel_soc.sv 2>&1 | tee "$OUT/soc_$variant.log"
done
for script in scripts/*.sh; do bash -n "$script"; done
python3 scripts/static_check.py 2>&1 | tee "$OUT/python_and_inputs.log"
sha256sum rtl/*.v tb/*.sv firmware/main.c firmware/start.S firmware/link.ld \
    firmware/generated/*.hex firmware/generated/manifest.json third_party/picorv32/picorv32.v \
    scripts/*.py scripts/*.sh > "$OUT/inputs.sha256"
printf 'STATIC CHECK PASS: core, MMIO, both CPU variants compile; firmware/input hashes valid.\n'
printf 'No simulation or physical flow executed.\n'
printf 'Evidence: %s\n' "$OUT"
