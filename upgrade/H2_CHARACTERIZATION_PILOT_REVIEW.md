# H2 characterization pilot — audit bảy ZIP

Trạng thái: EXPORTED_PILOT_AUDIT_PASS. Nguồn khớp H2_LINEBUFFER_BASELINE commit a5b8f2317589a90a599ea37d5bc2a782d71e99f0; archive/config/input/experiment definition/pixel/tile/profile đều được kiểm tra lại từ ZIP. Không chạy lại simulation. ASIC NOT_RUN.

| Gray | Tile | Wait | S1 cycles (cả v1/v2) | H1 cycles | H2 cycles | H2 DMA reads | H2 first-region cycles |
|---|---:|---:|---:|---:|---:|---:|---:|
| 32×32 | 32 | 1 | 310052 | 68987 | 18044 | 1024 | 18003 |
| 64×64 | 32 | 1 | 1247066 | 279162 | 71435 | 4356 | 18403 |
| 128×128 | 32 | 1 | 5002475 | 1125450 | 286501 | 17956 | 18443 |
| 64×64 | 16 | 1 | 1296502 | 283270 | 80071 | 4900 | 5562 |
| 64×64 | 64 | 1 | 1224030 | 278200 | 68287 | 4096 | 68246 |
| 64×64 | 32 | 0 | 1034261 | 210844 | 58484 | 4356 | 15061 |
| 64×64 | 32 | 3 | 1672676 | 436109 | 104596 | 4356 | 26968 |

Trên cùng input64×64/wait1, tile16→32→64 giảm H2 cycles80071→71435→68287 và reads4900→4356→4096. Đồng thời first-region latency tăng5562→18403→68246cycles; kích thước vùng đầu khác nhau nên đây là trade-off granularity/latency, không phải cùng một output region. Không kết luận tile64 tốt nhất cho mọi yêu cầu.

Trên cùng input64×64/tile32, wait0→1→3 làm H2 cycles58484→71435→104596; H1 cũng tăng210844→279162→436109. Read count mỗi kiến trúc giữ nguyên theo wait. Không diễn giải tăng tỷ số H1/H2 thành H2 chạy nhanh hơn tuyệt đối khi RAM chậm.

Scaling32/64/128 giữ tile32/wait1 và cùng coordinate-field generator. Đây là synthetic input, chưa là natural-image benchmark. Bộ irregular/degenerate frozen giữ nguyên, không loại ca xấu.

Ở128×128, wall time bốn lần CPU simulation lần lượt khoảng134,64s/31,88s/137,19s/8,93s. Nếu chi phí host tăng tuyến tính theo pixel thì ba RUN lớn kế tiếp cộng khoảng94phút cho bốn CPU executions, chưa kể unit/compile/audit/export. Đây chỉ là dự phóng lập lịch, không số đo large hoặc target processing time; còn phụ thuộc tải máy và I/O. Timeout7200s mỗi subprocess và watchdog500triệu cycles đã có trong kế hoạch, không sửa để tạo PASS.

Lượt tiếp theo được phép chạy theo gate có sẵn: bash scripts/26_run_h2_characterization.sh large, gồm256×256,320×240,480×320, tile32/wait1. Script audit lại pilot rồi mới chạy; không rerun pilot. Chưa có kết quả large. Không cần copy nguồn vì không thay script/RTL/firmware trong lần review này.

Audit chi tiết: build/h2_characterization_pilot_audit_01.json. Archive hashes:

- s2_m3_soc_h2char_g32x32_t32_w1_01.zip: `117df1f8821ab87115a90f9a84fd50da02a9020f2c727e7d1241813f868e72e2`.
- s2_m3_soc_h2char_g64x64_t32_w1_01.zip: `cbbcd482384f7b4886dad7513c3272a62e4e05df4f64080c78eb13961480c266`.
- s2_m3_soc_h2char_g128x128_t32_w1_01.zip: `6bc188bd0b304b0af68bfa40595a58d0343adb17b0ea904824b5cb76fd70a13a`.
- s2_m3_soc_h2char_g64x64_t16_w1_01.zip: `e9b220f9a0e5a7cee08883165aae4b0c657eb3aa296469d5ff287a88e8339ead`.
- s2_m3_soc_h2char_g64x64_t64_w1_01.zip: `774692317528ff1b455d5702a011581f2af14b3f70f6c3b40a3261b87969338c`.
- s2_m3_soc_h2char_g64x64_t32_w0_01.zip: `18a812aa16ccc2eecdf92b5edc41a2321ba2eff5c6a93c5a30ac6c8c8c4254c9`.
- s2_m3_soc_h2char_g64x64_t32_w3_01.zip: `b909fca08ec99d4edefd72855389113704076129e9eeb582290d6b5d110e5814`.
