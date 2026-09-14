#!/usr/bin/env bash
set -euo pipefail
SOURCE=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
DEST="$HOME/openlane_projects/picorv32_sobel_asic_ppa"
mkdir -p "$DEST"
for entry in rtl tb scripts firmware inputs third_party README.md RUN16_REPAIR_PLAN.md RUN15_REVIEW.md RUN12_PRESERVATION_AND_FANOUT.md ASIC_DMA_BASELINE_GUIDE.md STANDARD_IMAGE_TEST_COMMANDS.md TILE_DMA_RUN_GUIDE.md PERFORMANCE_OPTIMIZATION_PLAN.md SMALL_IMAGE_TEST_PLAN.md IMAGE_TEST_PLAN.md ARCHITECTURE.md ASIC_RUN_GUIDE.md ASIC_BASE01_REVIEW.md ASIC_REPAIR02_REVIEW.md ASIC_REPAIR03_REVIEW.md ASIC_REPAIR04_REVIEW.md ASIC_REPAIR06_REVIEW.md ASIC_REPAIR07_REVIEW.md ASIC_REPAIR08_REVIEW.md ASIC_REPAIR09_REVIEW.md FIRST_RUN_REVIEW.md config.json constraints.sdc pin_order.cfg AGENTS.md OPENLANE_WORKFLOW_NOTES.md PDK_COMPARISON.md; do
    cp -a -- "$SOURCE/$entry" "$DEST/"
done
printf 'COPY PASS: %s\nExisting results and RUNs are preserved.\n' "$DEST"
