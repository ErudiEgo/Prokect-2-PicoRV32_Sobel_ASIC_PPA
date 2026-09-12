#!/usr/bin/env bash
# Existing results only, even if the flow failed.
set -euo pipefail
source "$(dirname -- "$0")/asic_common.sh"
[[ $# == 1 ]] || { echo 'Usage: bash scripts/07_collect_asic.sh ASIC_RUN_TAG' >&2; exit 2; }
check_tag "$1"
cd "$PROJECT_DIR"
exec python3 scripts/collect_asic.py "$1"
