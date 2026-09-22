# M3 RGB32 — audit bằng chứng thực tế

RUN s2_m3_soc_rgb32_w1_01 đã được người dùng chạy và export. Audit ZIP ngày2026-09-21 đạt M3_SINGLE_RUN_AUDIT_PASS; không mô phỏng lại.

| Cấu hình | Chu kỳ | DMA đọc ảnh |
|---|---:|---:|
| S1 trên v1 | 959.301 | 0 |
| H1 | 206.960 | 23.436 |
| S1 trên v2 | 959.301 | 0 |
| H2 | 57.515 | 3.468 |

Ảnh RGB32, tile16, memory_wait1. H1/H2=3,598366×; S1v2/H2=16,679145×. S1 profile giống nhau trên v1/v2. Golden pixel, tile events, traffic và binding nguồn/firmware/architecture đều đạt. Các tỷ số mô tả chu kỳ của workload này, không phải speedup ASIC đã đo. Chưa có PPA, power, energy hoặc RGB480.

- archive_sha256: `575f4ca3e7ec995412b3935d7143cd052151a4cea6f40fe4dc0f6ad3688d376a`.
- snapshot_sha256: `9d52aee1f8fee8ad1dc9622358e286274aede6b8f041a8c5fcec60639efd99c1`.
- comparison_sha256: `b933e9e03f4acd094cca7985ad33464e86f2f4a37e344113cdc74e8d9b79e583`.

Bằng chứng gốc: reports/s2_m3_soc_rgb32_w1_01.zip. Audit: build/m3_rgb32_exported_audit_01.json. Sáu regression tiếp theo vẫn USER_RUN_REQUIRED; chưa nghiệm thu toàn M3.
