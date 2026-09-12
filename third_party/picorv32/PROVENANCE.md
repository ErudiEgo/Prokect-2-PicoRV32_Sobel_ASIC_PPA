# PicoRV32 source provenance

- Upstream: https://github.com/YosysHQ/picorv32
- Commit: `ef203c2b0a3fb793280f5114941416c425c5b461`
- Retrieved: 2026-09-11.
- Files: `picorv32.v`, `COPYING`, `README.md`, retrieved directly from the frozen commit.
- License: ISC; original notices preserved. See COPYING.
- No upstream RTL changes made. The core is instantiated by rtl/picorv32_sobel_soc.v; both configurations compile with Icarus 12.0. Functional execution remains pending the user's simulation.
- The upstream repository currently states that active development has stopped. This project therefore uses a pinned source version and must provide its own integration evidence.
- Original source: https://github.com/YosysHQ/picorv32/blob/ef203c2b0a3fb793280f5114941416c425c5b461/picorv32.v

The local sobel_core.v and testbench are new project code, not copied from the earlier FPGA vision demonstration repository. That repository was examined as an architectural reference only.
