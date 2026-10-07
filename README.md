# H3_40ns_final

Clean publication branch for the final 40 ns PicoRV32–H3 ASIC logic result.

## Provenance

- Frozen physical RUN: `s2_h3_c40_monolithic_06`
- Flow: OpenLane Classic 29.7.2
- PDK/library: `sky130A / sky130_fd_sc_hd`
- Clock constraint: 40 ns (25 MHz)
- Evidence status: `C40_MONOLITHIC_79_CLASSIC_PASS_WITH_DOCUMENTED_GUIDANCE`
- Evidence SHA-256: `f2e782836919896c9a740b6d05a8f27f82beb15b91d9a0f716c2f983b9e9633d`

The frozen source was recovered from the immutable RUN evidence archive rather
than copied from a later working tree.

## Final measured result

- Worst extracted setup slack: +7.542642 ns
- Worst extracted hold slack: +0.116533 ns
- Nine-corner setup/hold/slew/capacitance/fanout violations: 0
- Route DRC: 0; disconnected pins: 0; antenna nets/pins: 0/0
- Magic DRC: 0; KLayout DRC: 0; XOR: 0; LVS errors: 0
- Die area: 1.176680 mm²
- Core area: 1.138870 mm²
- Instance area: 0.477911 mm²
- Utilization: 41.9635%; instances: 64,421
- Vectorless total power: 14.942068 mW

Read `FULL_TECHNICAL_REPORT.md` for assumptions and limits.

## Repository structure

- `rtl/`: exact synthesizable RTL from the final RUN.
- `build/asic_sources/`: exact source staging used by `config.json`.
- `flow/`: exact custom OpenLane flow source frozen by the RUN.
- `config.json`, `constraints.sdc`, `pin_order.cfg`: final physical inputs.
- `guidance_archives/`: compressed, hash-pinned OpenDB guidance checkpoints.
- `release/picorv32_h3_logic_ppa.gds`: verified KLayout GDS stream-out.
- `release/evidence/`: compact report package.
- `.github/workflows/gds3d.yml`: GitHub Pages/TinyTapeout 3D viewer deployment.

## Restore the exact guidance inputs

Ubuntu:

```bash
bash scripts/restore_guidance.sh
python3 scripts/verify_frozen_source.py
```

Windows PowerShell:

```powershell
.\scripts\restore_guidance.ps1
python .\scripts\verify_frozen_source.py
```

Expected result: `H3_C40_FROZEN_SOURCE_PASS`.

## Physical-flow reproduction

The user owns heavy OpenLane execution. Static source verification is separate
from rerunning physical design. After restoring guidance and verifying the
installed Docker image/PDK, see `REPRODUCE_OPENLANE.md`.

## TinyTapeout status

The 3D web publication is ready. A real TinyTapeout submission is **not yet
ready**: the current top has the project-specific memory bus rather than a
`tt_um_*` wrapper, excludes SRAM/pads, and is much larger than a normal single
TinyTapeout tile. See `TINY_TAPEOUT_PORTING.md`.

## Scope

The physical top contains PicoRV32 and H3 logic/control/datapath. External
program/image SRAM, UART, camera, pads and package are outside the measured top.
This is a laboratory ASIC implementation result, not a fabricated chip or an
industrial tape-out approval.

