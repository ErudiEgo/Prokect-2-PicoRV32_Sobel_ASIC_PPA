#!/usr/bin/env bash
set -euo pipefail
PROJECT_DIR=$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
IMAGE=${OPENLANE_IMAGE:-ghcr.io/efabless/openlane2:2.3.10}
PDK_STORE=${PDK_ROOT:-"$HOME/.volare"}
export PYTHONDONTWRITEBYTECODE=1
check_tag() {
    [[ "$1" =~ ^[A-Za-z0-9][A-Za-z0-9_-]{0,79}$ ]] || { echo 'Invalid RUN tag' >&2; exit 2; }
}
require_linux_project() {
    [[ "$PROJECT_DIR" != /mnt/* && "$PROJECT_DIR" != *' '* ]] || {
        echo 'Copy sources to ~/openlane_projects/picorv32_sobel_asic_ppa before physical RUN.' >&2; exit 1;
    }
}
