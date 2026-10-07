#!/usr/bin/env bash
# Config loading and lint only; never launches physical stages or simulation.
set -euo pipefail
source "$(dirname -- "$0")/asic_common.sh"
cd "$PROJECT_DIR"
python3 scripts/asic_project.py validate
mkdir -p build
OUT=$(mktemp -d "$PROJECT_DIR/build/asic_precheck_XXXXXXXX")
if ! docker info > "$OUT/docker_info.log" 2>&1; then
    cat "$OUT/docker_info.log" >&2
    printf 'ERROR: Docker unavailable. Start Docker Desktop and enable WSL integration for this Ubuntu distro.\nEvidence: %s\n' "$OUT" >&2
    exit 1
fi
IMAGE_ID=$(docker image inspect "$IMAGE" --format '{{.Id}}')
[[ -d "$PDK_STORE/sky130A/libs.tech/openlane" ]] || { echo 'sky130A PDK not found' >&2; exit 1; }
printf 'image=%s\nimage_id=%s\npdk_resolved=%s\n' "$IMAGE" "$IMAGE_ID" "$(readlink -f "$PDK_STORE/sky130A")" | tee "$OUT/environment.txt"
docker run --rm --user "$(id -u):$(id -g)" -e HOME=/tmp -e PYTHONDONTWRITEBYTECODE=1 \
    -v "$PROJECT_DIR:/work:ro" -v "$OUT:/audit" -v "$PDK_STORE:/pdk:ro" -w /work \
    "$IMAGE_ID" python3 scripts/asic_project.py check-openlane /work/config.json /audit \
    2>&1 | tee "$OUT/precheck.log"
printf 'ASIC precheck evidence: %s\n' "$OUT"
