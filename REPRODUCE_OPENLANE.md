# Reproduce the frozen 40 ns OpenLane flow

The final RUN used Docker image:

`sha256:37c3bd4ea0534a276cb2deb88d601044857bad2807b9bc5b36efe9d02c62624e`

It also used the locally installed `sky130A` PDK managed under `.volare`.
Tool/PDK availability must be verified before any new physical execution.

After `scripts/restore_guidance.sh` and
`scripts/verify_frozen_source.py` pass, the equivalent container entry point is:

```bash
docker run --rm --network none --user "$(id -u):$(id -g)" \
  -e HOME=/tmp -e PYTHONDONTWRITEBYTECODE=1 -e TERM=xterm-256color \
  -v "$PWD:/design:ro" \
  -v "$HOME/.volare:/pdk:ro" \
  -v "$PWD:/work" \
  -w /work -it \
  sha256:37c3bd4ea0534a276cb2deb88d601044857bad2807b9bc5b36efe9d02c62624e \
  python3 /design/flow/openlane_with_repairs.py \
  --manual-pdk --pdk-root /pdk --pdk sky130A \
  --design-dir /work --run-tag h3_40ns_final_rebuild_01 -j 4 \
  /design/config.json
```

This is a heavy full physical flow. Do not overwrite the published RUN or call
a rebuild PASS without collecting its own reports. The historical result is
preserved in `release/evidence`; a new RUN is new evidence.

