# Flow metadata

This directory contains frozen audit and ECO metadata from the final C40 design
lineage. These files are retained for provenance and report review; they are not
GitHub Pages assets and most are not direct OpenLane inputs.

The OpenLane inputs that use fixed `/design/...` paths remain at repository
root: `capacity_witness.json`, `padding_config.json`, `eco_plan.json` and
`eco_pins.json`.

Run `python3 scripts/verify_frozen_source.py` after restoring the two guidance
checkpoints to verify every frozen file against `snapshot_sha256.json`.
