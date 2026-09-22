#!/usr/bin/env bash
# Compile/static/host algorithm checks only; no vvp/firmware/OpenLane execution.
set -euo pipefail
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
export PYTHONDONTWRITEBYTECODE=1
cd "$ROOT"
bash scripts/01_precheck.sh
OUT=$(mktemp -d "$ROOT/build/m2_static_XXXXXXXX")
python3 scripts/s1_firmware.py > "$OUT/s1_manifest_check.json"
for mode in 0 2 1; do
    iverilog -g2012 -Wall -Wno-timescale -s tb_sobel_soc_m2 \
        -Ptb_sobel_soc_m2.ENABLE_SOBEL=1 -Ptb_sobel_soc_m2.FIRMWARE_MODE="$mode" \
        -o "$OUT/soc_m2_$mode.vvp" rtl/sobel_core.v rtl/sobel_mmio.v rtl/sobel_tile.v \
        rtl/native_bus_arbiter.v rtl/picorv32_sobel_soc.v third_party/picorv32/picorv32.v \
        tb/tb_sobel_soc_m2.sv 2>&1 | tee "$OUT/soc_m2_$mode.log"
done
python3 scripts/test_s1_host.py 2>&1 | tee "$OUT/s1_host_algorithm.log"
python3 scripts/test_m2_contract.py 2>&1 | tee "$OUT/m2_contract_tests.log"
sha256sum rtl/*.v tb/*.sv firmware/s1/*.c firmware/s1/*.h firmware/s1/generated/* \
    scripts/*.py scripts/*.sh > "$OUT/inputs.sha256"
printf 'M2 STATIC CHECK PASS: S1 manifest, S0/S1/H1 compile, host algorithm tests.\nNo RTL or RV32 execution; ASIC NOT_RUN.\nEvidence: %s\n' "$OUT"
