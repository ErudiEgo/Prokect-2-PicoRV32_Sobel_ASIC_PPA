# TinyTapeout porting plan

## What is ready

- SKY130 synthesizable PicoRV32–H3 RTL.
- A clean 40 ns physical configuration and final GDS.
- A GitHub Pages workflow that converts the verified GDS to glTF and opens it
  in the TinyTapeout 3D GDS Viewer.

## What is not ready

The final 40 ns GDS is not directly a TinyTapeout submission:

1. The top is `picorv32_h3_logic_ppa`, not a TinyTapeout `tt_um_*` wrapper.
2. The interface exposes the project's external memory transaction signals;
   it has not been mapped to TinyTapeout's fixed digital I/O contract.
3. Program/image SRAM, UART, camera and pads are outside this physical top.
4. The die is about 1.0794 mm × 1.09012 mm. Tile availability and maximum
   permitted macro size must be checked against the chosen shuttle.
5. The current 40 ns PASS belongs to the standalone top. Adding a wrapper,
   memories or changing the floorplan requires fresh functional verification
   and a new physical RUN.

## Required porting sequence

1. Select the exact TinyTapeout SKY130 shuttle and allowed multi-tile size.
2. Freeze the interface contract and decide whether PicoRV32 program/image RAM
   is external, serialized, or implemented using permitted memory resources.
3. Create a `tt_um_*` wrapper with safe reset behavior and deterministic unused
   outputs.
4. Add TinyTapeout cocotb tests using real firmware/data transactions.
5. Run the official TinyTapeout precheck and GDS action.
6. Re-measure timing, DRC, LVS, antenna, area and power for the wrapped design.

Do not present the existing 40 ns standalone GDS as a shuttle-accepted macro.

