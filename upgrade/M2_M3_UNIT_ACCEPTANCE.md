# M2 và DMA v2 unit — nghiệm thu bằng chứng ngày 2026-09-21

Sáu ZIP M2 được audit lại từ nguồn đóng băng, firmware, pixel/tile/profile và hash; tất cả đạt M2_SINGLE_RUN_AUDIT_PASS. Đây là nghiệm thu cổng M2, chưa phải hoàn thành stage2.

| RUN | S0 cycles | S1 cycles | H1 cycles |
|---|---:|---:|---:|
| s2_m2_gray37x35_w1_01 | 700863 | 421749 | 90106 |
| s2_m2_gray9x1_w1_01 | 3993 | 3834 | 1134 |
| s2_m2_rgb17x19_w3_01 | 693266 | 430613 | 101421 |
| s2_m2_rgb1x1_w0_01 | 2076 | 2414 | 864 |
| s2_m2_rgb1x7_w3_01 | 18664 | 21378 | 5116 |
| s2_m2_rgb32_w1_01 | 1633906 | 959301 | 206960 |

S1 chậm hơn S0 ở RGB1×1 và RGB1×7; giữ nguyên số liệu này. Không khái quát speedup cho mọi ảnh.

DMA v2 unit: s2_m3_unit_01 audit hash/source/log/command exit và181 dòng kết quả đạt DMA_V2_EXPORTED_UNIT_AUDIT_PASS. Wall time simulator6,176715 giây; không phải thời gian thực thi ASIC. Unit chưa có CPU. SoC H2 vẫn USER_RUN_REQUIRED.

## SHA256 archive gốc

- `s2_m2_gray37x35_w1_01.zip`: `6ee80154f78f6cd097e3f88e3e262e5e06f5cb4ee35320d4dcc701f9389d5384`.
- `s2_m2_gray9x1_w1_01.zip`: `5f1c1d22bbcbf15e579b81806dc4fef9ab7d3f0a2abf18cf4807912d1691a0c2`.
- `s2_m2_rgb17x19_w3_01.zip`: `6d982f47513f7032e1f82eb854658a81b3bc33ce0b253bf72689d37f2c4fd48c`.
- `s2_m2_rgb1x1_w0_01.zip`: `1e8638804fcbf3c62e560e0d3fc5b07e18aac7b9940585919df2868b514da78c`.
- `s2_m2_rgb1x7_w3_01.zip`: `ac6280046b911c4155742573185259c66c56140cd211fa707c093552b250ab98`.
- `s2_m2_rgb32_w1_01.zip`: `e9fd57a42741810b9f338ff29d82cb1fe501a48ff07ee1707e2d7906da238560`.
- `s2_m3_unit_01.zip`: `b1a769705ff7686e4e33ccf9a624200dea26a0135546a878d8a821b1a8b5caf8`.

Audit cục bộ: build/received_m2_m3_audit_20260921_01.json. Không sửa ZIP và không mô phỏng lại để audit.
