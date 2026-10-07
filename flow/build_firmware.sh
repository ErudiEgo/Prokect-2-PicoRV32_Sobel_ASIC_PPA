#!/usr/bin/env bash
# Compilation only. No simulator or physical flow is started.
set -euo pipefail
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$ROOT"
if command -v "${RISCV_PREFIX:-riscv64-unknown-elf-}gcc" >/dev/null; then
    PREFIX=${RISCV_PREFIX:-riscv64-unknown-elf-}
elif [[ -x "$ROOT/build/toolchain/root/usr/bin/riscv64-unknown-elf-gcc" ]]; then
    PREFIX="$ROOT/build/toolchain/root/usr/bin/riscv64-unknown-elf-"
    export PATH="$ROOT/build/toolchain/root/usr/bin:$PATH"
else
    echo 'ERROR: RISC-V compiler missing. Ubuntu: sudo apt install gcc-riscv64-unknown-elf binutils-riscv64-unknown-elf' >&2
    exit 1
fi
mkdir -p build firmware/generated
OUT=$(mktemp -d "$ROOT/build/firmware_XXXXXXXX")
cp firmware/main.c firmware/start.S firmware/link.ld "$OUT/"
"${PREFIX}gcc" --version > "$OUT/compiler.txt"
for mode in sw hw; do
    ENABLE=0; [[ "$mode" != hw ]] || ENABLE=1
    "${PREFIX}gcc" -march=rv32i -mabi=ilp32 -O2 -g -Wall -Wextra -Werror \
        -ffreestanding -fno-builtin -fno-pic -msmall-data-limit=0 \
        -nostdlib -nostartfiles -Wl,--no-relax -Wl,-T,"$OUT/link.ld" \
        -Wl,-Map,"$OUT/$mode.map" -DUSE_ACCEL="$ENABLE" \
        "$OUT/start.S" "$OUT/main.c" -lgcc -o "$OUT/$mode.elf"
    "${PREFIX}objcopy" -O binary "$OUT/$mode.elf" "$OUT/$mode.bin"
    "${PREFIX}objdump" -d "$OUT/$mode.elf" > "$OUT/$mode.disassembly.txt"
done
python3 scripts/firmware_manifest.py "$OUT"
printf 'FIRMWARE BUILD PASS: %s\nNo firmware execution performed.\n' "$OUT"
