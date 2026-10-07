#!/usr/bin/env bash
# USER VIEW ONLY: read final ODB; no synthesis, placement, routing, or flow runner.
set -euo pipefail
source "$(dirname -- "$0")/asic_common.sh"
require_linux_project
[[ $# == 1 || ( $# == 2 && "$2" == --latest-state ) ]] || { echo 'Usage: bash scripts/09_open_final_openroad.sh RUN_TAG [--latest-state]' >&2; exit 2; }
TAG=$1
check_tag "$TAG"
cd "$PROJECT_DIR"
VIEW_OPTIONS=()
if [[ "${2:-}" == --latest-state ]]; then VIEW_OPTIONS+=(--latest-state); fi
[[ -n "${DISPLAY:-}" && -d /tmp/.X11-unix ]] || { echo 'WSLg DISPLAY/X11 is unavailable. Open a WSLg-enabled Ubuntu terminal.' >&2; exit 1; }
SNAPSHOT="$PROJECT_DIR/run_inputs/$TAG"
PINNED_IMAGE=$(sed -n 's/^image_id=//p' "$SNAPSHOT/environment.txt")
PDK_RESOLVED=$(sed -n 's/^pdk_resolved=//p' "$SNAPSHOT/environment.txt")
[[ "$PINNED_IMAGE" =~ ^sha256:[a-f0-9]{64}$ && -d "$PDK_RESOLVED" ]] || { echo 'Missing pinned image/PDK metadata.' >&2; exit 1; }
OUT=$(mktemp -d "$PROJECT_DIR/build/openroad_view_${TAG}_XXXXXXXX")
python3 "$PROJECT_DIR/scripts/prepare_openroad_view.py" "$TAG" "$OUT" "${VIEW_OPTIONS[@]}"
VIEW_ARGS=(--rm --user "$(id -u):$(id -g)" -e HOME=/tmp -e "DISPLAY=$DISPLAY"
    -e QT_X11_NO_MITSHM=1 -e LIBGL_ALWAYS_SOFTWARE=1
    -v "$PROJECT_DIR:/work:ro" -v "$PDK_STORE:/pdk:ro" -v /tmp/.X11-unix:/tmp/.X11-unix:ro)
if [[ -d /mnt/wslg ]]; then VIEW_ARGS+=(-v /mnt/wslg:/mnt/wslg:ro); fi
if [[ -t 0 && -t 1 ]]; then VIEW_ARGS+=(-it); fi
printf 'VIEW EXISTING ODB: %s; project mounted read-only.\n' "$TAG"
exec docker run "${VIEW_ARGS[@]}" "$PINNED_IMAGE" openroad -gui "/work/${OUT#"$PROJECT_DIR/"}/view.tcl"
