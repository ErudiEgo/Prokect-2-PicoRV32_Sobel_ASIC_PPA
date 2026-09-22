# M2 — kết quả RGB32 đã audit, 2026-09-21

RUN `s2_m2_rgb32_w1_01`, ảnh RGB 32×32, tile16, memory_wait1, người dùng chạy RTL. Audit lại ZIP có sẵn, không chạy lại simulation.

| Biến thể | Chu kỳ đo | CPU đọc ảnh | DMA đọc | DMA ghi |
|---|---:|---:|---:|---:|
| S0 phần mềm gốc | 1.633.906 | 23.436 | 0 | 0 |
| S1 phần mềm tái sử dụng cửa sổ | 959.301 | 9.588 | 0 | 0 |
| H1 DMA v1 | 206.960 | 0 | 23.436 | 3.072 |

Cả ba dùng cùng RTL với ENABLE_SOBEL=1. S0/S1 không sử dụng accelerator. Checker đối chiếu output với golden, sự kiện tile, profile, firmware và snapshot; kết quả `M2_SINGLE_RUN_AUDIT_PASS`. S0/S1 = 1,703226×; S1/H1 = 4,635200×. Không dùng SW M1 làm S0 M2 vì topology bus của phép đo M1 khác.

Đây là kết quả một workload; chưa nghiệm thu toàn bộ M2. Còn RGB17×19/wait3, gray37×35 và ba ảnh suy biến 1×1, 1×7, 9×1. Chu kỳ là cửa sổ xử lý theo contract M2, có transfer/control/tile overhead; không bao gồm boot, host decode và replay. Chưa có PPA/power stage2, không suy ra năng lượng từ speedup.

Bằng chứng:

- `reports/s2_m2_rgb32_w1_01.zip`, SHA256 `e9fd57a42741810b9f338ff29d82cb1fe501a48ff07ee1707e2d7906da238560`.
- `inputs.sha256.json`: `18d30221cbf2acf971517601651f9c27427e85a6e9d2c7edbe5de5165b2bc683`.
- `comparison.json`: `147ba2aead9cbad020558acd309f29762b8c0f0811bc7f2aa67689388d65ffff`.
- Audit cục bộ: `build/m2_rgb32_exported_audit_01.json`. Báo cáo này không thay thế ZIP gốc.
