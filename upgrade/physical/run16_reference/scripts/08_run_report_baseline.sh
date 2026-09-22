#!/usr/bin/env bash
# USER RUN: fixed fresh report baseline, no parent argument accepted.
set -euo pipefail
[[ $# == 0 ]] || { echo 'No arguments: this baseline always starts from scratch.' >&2; exit 2; }
exec bash "$(dirname -- "$0")/06_run_openlane.sh" picorv32_sobel_dma_clk50_baseline_06
