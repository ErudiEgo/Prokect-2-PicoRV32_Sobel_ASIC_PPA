#!/usr/bin/env bash
# Compile only. Rebuild S0/H1 into a fresh build directory for byte comparison.
set -euo pipefail
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
export PYTHONDONTWRITEBYTECODE=1
[[ ! -e "$ROOT/firmware/h2/generated" ]] || { echo 'H2 generated revision exists; refusing overwrite.' >&2; exit 1; }
if command -v "${RISCV_PREFIX:-riscv64-unknown-elf-}gcc" >/dev/null; then
    PREFIX=${RISCV_PREFIX:-riscv64-unknown-elf-}
elif [[ -x "$ROOT/../build/toolchain/root/usr/bin/riscv64-unknown-elf-gcc" ]]; then
    # Read-only use of the existing compiler; stage1 sources/results are untouched.
    PREFIX="$ROOT/../build/toolchain/root/usr/bin/riscv64-unknown-elf-"
    export PATH="$ROOT/../build/toolchain/root/usr/bin:$PATH"
else
    echo 'RISC-V compiler missing; prebuilt H2 HEX is sufficient for user simulations.' >&2; exit 1
fi
mkdir -p "$ROOT/build"
OUT=$(mktemp -d "$ROOT/build/h2_compile_XXXXXXXX")
cp "$ROOT/firmware/h2/main.c" "$ROOT/firmware/start.S" "$ROOT/firmware/link.ld" "$OUT/"
cp "$ROOT/firmware/main.c" "$OUT/baseline_main.c"
"${PREFIX}gcc" --version > "$OUT/compiler.txt"
FLAGS=(-march=rv32i -mabi=ilp32 -O2 -g -Wall -Wextra -Werror -ffreestanding -fno-builtin -fno-pic -msmall-data-limit=0 -nostdlib -nostartfiles -Wl,--no-relax)
for mode in sw hw h2; do
    MAIN="$OUT/baseline_main.c"; DEFINE=(-DUSE_ACCEL=0)
    if [[ "$mode" == hw ]]; then DEFINE=(-DUSE_ACCEL=1); fi
    if [[ "$mode" == h2 ]]; then MAIN="$OUT/main.c"; DEFINE=(-DUSE_ACCEL=1); fi
    "${PREFIX}gcc" "${FLAGS[@]}" -Wl,-T,"$OUT/link.ld" -Wl,-Map,"$OUT/$mode.map" "${DEFINE[@]}" "$OUT/start.S" "$MAIN" -lgcc -o "$OUT/$mode.elf"
    "${PREFIX}objcopy" -O binary "$OUT/$mode.elf" "$OUT/$mode.bin"
    "${PREFIX}objdump" -d "$OUT/$mode.elf" > "$OUT/$mode.disassembly.txt"
done
python3 "$ROOT/scripts/h2_firmware.py" "$OUT"
printf 'H2 build evidence: %s\nNo simulator or physical flow executed.\n' "$OUT"
