# RGB32 first functional result — 2026-09-15

RUN `soc_rgb32_smoke_01`: FUNCTIONAL PASS on the original RGB32 diagnostic input, tile16, memory_wait1. User executed the simulation and exported the ZIP. Assistant rechecked existing evidence; no simulation/physical flow was rerun.

| Measurement | CPU software | CPU + tile DMA Sobel |
|---|---:|---:|
| Target cycles, complete RGB task | 1352946 | 206960 |
| Simulator wall seconds | 36.800830 | 6.378918 |
| Spatial pixels | 1024 | 1024 |
| Verified channel samples | 3072 | 3072 |
| Verified full RGB tile events | 4 | 4 |
| DMA writes | 0 | 3072 |
| DMA tile starts | 0 | 12 |

Cycle speedup 6.537234x; time reduction 84.703% at equal target clock. This is measured for this image, compiler/firmware and shared memory model, not a universal RGB speedup or a comparison with fully optimized software. No image-specific delay was added to software. Measured interval includes all channel loops, CPU arithmetic/control, transfers, MMIO, stores and tile events; host decoding and replay are excluded equally.

Audit: all 73 frozen file hashes and 11 output/basis evidence hashes match. Recomputed independent 3x3 golden RGB convolution, checked all 3072 samples in each variant and all tile timestamps, regenerated PPM in a temporary audit directory and compared byte-for-byte with archived outputs. Original decoded RGB matches the planar input. 988/1024 output pixels have unequal channel values, confirming these are per-channel RGB edges. Current RTL/CPU/firmware/testbench sources match this RUN's snapshots.

Original ZIP: `reports/soc_rgb32_smoke_01.zip`, 286596 bytes.
SHA256: `4ab84bd6295ae18c17e9669e96bb7ee4b5a96fbc8fc4945bb9e26d26e6668d52`.
Ubuntu evidence: `/home/koika/openlane_projects/picorv32_sobel_rgb_asic_ppa/reports/soc_rgb32_smoke_01`.

User reports that replay displayed color; audit verifies archived color pixels and timestamps, not a new GUI visual inspection. The original input and output are RGB8; Sobel produces colored edges, not reconstruction of source colors.

Remaining validation: RGB17x19 partial tiles / unaligned planes / memory_wait3, grayscale regression using updated firmware, then real RGB images and larger dimensions. See RGB_RUN_GUIDE.md. RGB512 remains outside this implementation's DMA address limits.

ASIC scope: no new physical run. RUN16 RTL is unchanged; historical antenna/LVS/DRC results remain their original evidence, including one remaining fanout violation. RGB workload power/energy is NOT_MEASURED; RUN16 vectorless power is not RGB activity-based power.
