# RUN 9: antenna/LVS/DRC PASS; electrical closure remains

## Evidence verified on 2026-09-12

User-run `picorv32_sobel_clk50_repair_09`, final state
`32-misc-reportmanufacturability/state_out.json`.
Archive: `reports/picorv32_sobel_clk50_repair_09_collect_20260912T094537758061Z.tar.gz`.
SHA256: `6edb399cfa8aa0cf8ea2b5504ace7bc4b66982d8d22e4d00831ab05133f0e8d9`.

- Antenna: 0 violating nets / 0 pins; LVS and DRC PASS.
- Setup/hold checkers report no violations under the configured constraints.
- Max slew: 12 at max_ss_100C_1v60, 1 at nom_ss_100C_1v60.
- Max capacitance: 2 at max_ss and nom_ss.
- Max fanout: 27 at each reported corner; constraint remains 10.
- OpenLane exit 2. This is a manufacturing-check milestone, not full flow PASS.

## Two identified electrical drivers

Actual `12-openroad-stapostpnr/max_ss_100C_1v60/checks.rpt`:

| Driver | Net | Slew / limit (ns) | Cap / limit (pF) |
|---|---|---|---|
| `_07463_/Y` | `_02744_` | 1.589626 / 1.488467 | 0.094761 / 0.086070 |
| `_07515_/Y` | `_02788_` | 1.567682 / 1.488467 | 0.093291 / 0.086070 |

Both are `sky130_fd_sc_hd__o31ai_4`. The installed SS Liberty provides
only o31ai sizes 1, 2, 4. Increasing the strength of the same gate is unavailable.
The 12 max_ss slew entries are these two drivers and their loads.

Read-only inspection of the pre-filler checkpoint found 15014 instances / 89055
terminals. The first net retains four logical loads and two diodes; the second
retains three logical loads and one diode. These are exact ODB connections,
not an inference from instance names.

## RUN 10: controlled output-buffer ECO

Resume RUN 9 with explicit third argument `electrical`. The frozen config records
`SOBEL_OUTPUT_BUFFER_REPAIR=true` and provenance includes this choice. Normal
antenna continuation leaves it false. A zero-antenna parent checkpoint is required.

1. Validate exact two drivers, masters, signal nets, sole output drivers, PG
   connections, and unused ECO instance/net names before any edit.
2. Insert `sky130_fd_sc_hd__buf_8` at each driver, then legalize. Installed SS
   Liberty confirms buffer output function `(A)`. Driver now feeds the buffer
   input on a new short net; buffer output feeds the original net. All original
   loads, diodes, logic masters, firmware and RTL remain present.
3. Verify all expected pin connections. Clear detailed wires only on the two
   edited nets/new nets and signal nets incident to cells moved by legalization.
   Rebuild global guides and run detailed routing. This ECO routing step is not
   claimed to be native incremental GRT; other detailed wires are retained as
   inputs. Exact topology is checked again after routing.
4. Run native antenna closure, with at most three repairs and independent checks,
   followed by existing extraction, STA, LVS, DRC and other Classic checks.

This targets the measured slew/cap failures. It does not claim to solve fanout.
Clock branches have 11-12 actual clock-buffer loads; some signal nets include
multiple protection diodes (e.g. net11: one logic load plus eleven diodes).
Removing diodes or raising the fanout limit is not the chosen repair. Clock-tree
changes must be evaluated separately for skew and setup/hold.

Two buffers add area, capacitance, power and delay. All of these require the new
user-run reports. Antenna PASS from RUN 9 cannot be inherited as RUN 10 PASS.
The expected two-buffer structural identity is not a post-layout timing simulation.

## Static verification

The assistant ran no simulation, insertion, placement or routing. Frozen snapshot
preparation, real ODB read-only target validation, topology mismatch guards,
installed API checks, config loading, Verilator lint and SDC loading passed.
Audit: `build/resume10_frozen_check_iTdNizWE` (local, excluded from Git).
User command and collection procedure are in `ASIC_RUN_GUIDE.md`.

After this run, compare final slew/cap and all three manufacturing checks against
RUN 9; then address remaining fanout from exact net reports. Only after closure
assemble the final timing/area/utilization/power table. Power remains vectorless;
external RAM, pads and package remain outside this physical top. The existing
image workload has HW 774758 cycles vs SW 573713 cycles; ASIC closure does not
establish an image speedup.
