# H3 40 ns final branch rules

- Treat `rtl/`, `config.json`, `constraints.sdc`, `pin_order.cfg`, `flow/`,
  `snapshot_sha256.json` and the guidance archives as the frozen source of
  `s2_h3_c40_monolithic_06`.
- Do not change the frozen result in place. New RTL, wrappers, memory or floorplan
  work belongs in a new branch/RUN with new functional and physical evidence.
- The user runs RTL simulation and OpenLane. Static hash/config/lint checks are
  allowed; do not launch heavy flows without explicit authorization.
- Do not call the standalone physical top TinyTapeout-ready. Follow
  `TINY_TAPEOUT_PORTING.md` and verify the selected shuttle contract.
- Preserve the distinction between FPGA board measurements, functional
  simulation, and ASIC PPA.
- Never claim that external SRAM, UART, camera, pads or package are included in
  the final 40 ns PPA.
