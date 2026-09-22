# H2 characterization — nghiệm thu ma trận ngày2026-09-22

Bảy pilot và ba large RUN đã audit ZIP đạt, khớp baseline H2_LINEBUFFER_BASELINE commit a5b8f2317589a90a599ea37d5bc2a782d71e99f0. Audit kiểm tra archive/source/firmware/input/config/pixel/tile/profile và experiment definition, không chạy lại simulation.

Trạng thái: H2_CHARACTERIZATION_DEFINED_MATRIX_ACCEPTED. Hoàn tất ma trận synthetic đã định, không phải mọi ảnh/kích thước/memory model. Gray480×320 được kiểm chứng trên RTL với external TB memory; RGB480/H2 PPA/H3/FPGA chưa có kết quả mới.

| Gray | S1 cycles (cả hai SoC) | H1 cycles | H2 cycles | H1/H2 | S1/H2 | DMA reads H1→H2 |
|---|---:|---:|---:|---:|---:|---|
| 256×256 | 20039142 | 4521530 | 1150057 | 3.931570 | 17.424477 | 521220→72900 |
| 320×240 | 23490947 | 5302041 | 1352571 | 3.919972 | 17.367626 | 611044→85852 |
| 480×320 | 46994735 | 10613703 | 2699463 | 3.931783 | 17.408920 | 1224004→171704 |

Cùng tile32/memory_wait1, cùng bộ generator đã định. S1 v1/v2 có profile giống nhau. Giữ nguyên các ca bất lợi H2 ở regression M3; scaling tốt không xóa kết quả âm.

## Thời gian host thực tế

Tổng bốn CPU simulations của ba large RUN: 90.29phút. Hai cấu hình S1 chiếm 78.73phút (87.19%). Chưa cộng compile/unit/audit/export; không gọi đây là toàn bộ elapsed batch.

| Gray | S1_v1 (s) | H1 (s) | S1_v2 (s) | H2 (s) |
|---|---:|---:|---:|---:|
| 256×256 | 524.51 | 116.70 | 502.55 | 30.98 |
| 320×240 | 616.26 | 139.50 | 628.53 | 38.94 |
| 480×320 | 1227.01 | 283.86 | 1225.02 | 83.77 |

S1 chạy hai lần để kiểm tra cùng binary trên hai kiến trúc DMA nghỉ. Không phải simulation bị chạy lặp ngoài kế hoạch. Wall seconds là thời gian simulator trên host, không phải thời gian xử lý chip hoặc FPS ASIC. Lượt sau không rerun chỉ để xem báo cáo; nếu muốn giảm matrix/đổi simulator phải là thay đổi methodology có lý do và validation riêng, không sửa số liệu hoặc bỏ check âm thầm.

## Gate tiếp theo

Theo định hướng dự án, bước sau là task B chuẩn bị physical experiment H1/H2 cùng PDK/library/flow/constraints/scope, xác minh tool/PDK và memory boundary trước khi giao lệnh. Chưa chạy physical flow trong task audit này. Không dùng area/power RUN16 làm số H2; không suy energy/FPS thực khi chưa có timing/power thích hợp. H3 vẫn chưa bắt đầu.

Evidence: build/h2_characterization_pilot_audit_01.json và build/h2_characterization_large_audit_01.json; ba ZIP large vẫn nguyên gốc trong reports. SHA256:

- s2_m3_soc_h2char_g256x256_t32_w1_01.zip: `517ed7185ff653e698c22b44ced186488ae26e169b63d7304ae2243862e13b76`.
- s2_m3_soc_h2char_g320x240_t32_w1_01.zip: `479c34ea32682e8134411c2eff39ab601ef8c52109649c89f9dfb5456040028c`.
- s2_m3_soc_h2char_g480x320_t32_w1_01.zip: `f65e74d54ad09bedba4f1bbe3aae2b8d6a79ef0f62ae6c77648c42da65d2f2bc`.
