#!/usr/bin/env bash
# USER-RUN ONLY: Classic 78 original steps + 3 reviewed repair additions.
set -euo pipefail
source "$(dirname -- "$0")/asic_common.sh"
require_linux_project
[[ $# == 1 || $# == 2 ]] || { echo 'Usage: bash scripts/06_run_openlane.sh NEW_RUN_TAG [PARENT_DRT_RUN]' >&2; exit 2; }
TAG=$1
check_tag "$TAG"
PARENT=${2:-}
if [[ -n "$PARENT" ]]; then check_tag "$PARENT"; fi
cd "$PROJECT_DIR"
[[ ! -e "runs/$TAG" && ! -e "run_inputs/$TAG" ]] || { echo 'RUN/snapshot exists; choose a NEW tag.' >&2; exit 1; }
# Check actual functional evidence and current config without rerunning simulation.
bash scripts/05_asic_precheck.sh
IMAGE_ID=$(docker image inspect "$IMAGE" --format '{{.Id}}')
PDK_RESOLVED=$(readlink -f "$PDK_STORE/sky130A")
mkdir -p runs run_inputs reports
python3 scripts/asic_project.py freeze "$TAG"
SNAPSHOT="$PROJECT_DIR/run_inputs/$TAG"
printf 'image=%s\nimage_id=%s\npdk_root=%s\npdk_resolved=%s\n' \
    "$IMAGE" "$IMAGE_ID" "$PDK_STORE" "$PDK_RESOLVED" > "$SNAPSHOT/environment.txt"
if [[ -n "$PARENT" ]]; then
    python3 "$SNAPSHOT/scripts/resume_checkpoint.py" "$PARENT" "$TAG"
fi
CHECK=$(mktemp -d "$PROJECT_DIR/build/frozen_precheck_XXXXXXXX")
# Load and lint the exact frozen config before launching the real flow.
docker run --rm --user "$(id -u):$(id -g)" -e HOME=/tmp -e PYTHONDONTWRITEBYTECODE=1 \
    -v "$PROJECT_DIR:/work:ro" -v "$CHECK:/audit" -v "$PDK_STORE:/pdk:ro" -w /work \
    "$IMAGE_ID" python3 "/work/run_inputs/$TAG/scripts/asic_project.py" \
    check-openlane "/work/run_inputs/$TAG/config.frozen.json" /audit \
    2>&1 | tee "$CHECK/precheck.log"
cp -a "$CHECK" "$SNAPSHOT/frozen_precheck"
START=$(date +%s)
printf 'start_epoch=%s\nstatus=RUNNING\n' "$START" > "$SNAPSHOT/runtime.txt"
finish() {
    code=$?
    END=$(date +%s)
    printf 'start_epoch=%s\nend_epoch=%s\nelapsed_seconds=%s\nopenlane_exit_status=%s\n' \
        "$START" "$END" "$((END - START))" "$code" > "$SNAPSHOT/runtime.txt"
    printf '\nOpenLane exit status=%s. Collect existing results: bash scripts/07_collect_asic.sh %s\n' "$code" "$TAG"
}
trap finish EXIT
printf '\nPHYSICAL RUN: %s | PicoRV32 + Sobel | SKY130 HD | clk 50 ns\n' "$TAG"
DOCKER_ARGS=(--rm --user "$(id -u):$(id -g)" -e HOME=/tmp -e PYTHONDONTWRITEBYTECODE=1
    -v "$PROJECT_DIR:/work" -v "$SNAPSHOT:/work/run_inputs/$TAG:ro"
    -v "$PDK_STORE:/pdk:ro" -w /work)
FLOW_ARGS=(python3 "/work/run_inputs/$TAG/scripts/openlane_with_repairs.py" --manual-pdk --pdk-root /pdk --pdk sky130A
    --design-dir /work --run-tag "$TAG" -j "${OPENLANE_JOBS:-4}"
    "/work/run_inputs/$TAG/config.frozen.json")
if [[ -n "$PARENT" ]]; then
    FLOW_ARGS+=(--from Sobel.AntennaClosure --with-initial-state "/work/run_inputs/$TAG/resume_checkpoint/state.json")
    printf 'CONTINUATION: %s checkpoint -> %s; starting at Sobel.AntennaClosure\n' "$PARENT" "$TAG"
fi
# Flow comes from frozen meta.flow=Classic plus its three additive steps.
# In OpenLane 2.3.10 an explicit --flow Classic discards meta substitutions.
set +e
if [[ -t 0 && -t 1 ]]; then
    # Preserve native colors, progress bar and terminal resizing. Logs in runs/TAG.
    docker run "${DOCKER_ARGS[@]}" -it -e "TERM=${TERM:-xterm-256color}" "$IMAGE_ID" "${FLOW_ARGS[@]}"
    STATUS=$?
else
    docker run "${DOCKER_ARGS[@]}" "$IMAGE_ID" "${FLOW_ARGS[@]}" 2>&1 | tee "reports/${TAG}_console.log"
    RESULTS=("${PIPESTATUS[@]}")
    STATUS=${RESULTS[0]}
    if [[ "$STATUS" == 0 && "${RESULTS[1]}" != 0 ]]; then STATUS=${RESULTS[1]}; fi
fi
set -e
exit "$STATUS"
