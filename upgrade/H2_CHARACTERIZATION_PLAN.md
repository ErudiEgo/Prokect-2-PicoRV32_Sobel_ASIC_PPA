# H2 characterization — nhóm A, chưa có số đo mới

Baseline: H2_LINEBUFFER_BASELINE, commit a5b8f2317589a90a599ea37d5bc2a782d71e99f0. Manifest SHA256 d41639057c7ee48e10f86284a558ad43682fe8c741f1ff3d4e34c2a974299eb6. RTL, firmware, TB chức năng và checker/runner M3 giữ nguyên; không thay bus, capacity, operator hoặc baseline.

Giả thuyết cần đo: lợi ích reuse thay đổi theo kích thước, halo/tile overhead và memory wait. Không giả định H2 luôn thắng hoặc tile64 luôn tốt nhất. PASS chức năng không yêu cầu speedup định trước.

## Ma trận kiểm soát, không Cartesian product

Mọi case là Gray8, cùng bốn cấu hình s1_v1/h1/s1_v2/h2. Scaling giữ tile32/wait1. Tile/wait sensitivity dùng đúng một input gray64×64, cùng hash. Điểm gray64/tile32/wait1 dùng chung, không chạy lặp.

| Phase | RUN | Kích thước | Tile | Wait | Vai trò |
|---|---|---|---:|---:|---|
| pilot | s2_m3_soc_h2char_g32x32_t32_w1_01 | 32×32 | 32 | 1 | scaling |
| pilot | s2_m3_soc_h2char_g64x64_t32_w1_01 | 64×64 | 32 | 1 | scaling + tâm sensitivity |
| pilot | s2_m3_soc_h2char_g128x128_t32_w1_01 | 128×128 | 32 | 1 | scaling |
| pilot | s2_m3_soc_h2char_g64x64_t16_w1_01 | 64×64 | 16 | 1 | tile sensitivity |
| pilot | s2_m3_soc_h2char_g64x64_t64_w1_01 | 64×64 | 64 | 1 | tile sensitivity |
| pilot | s2_m3_soc_h2char_g64x64_t32_w0_01 | 64×64 | 32 | 0 | wait sensitivity |
| pilot | s2_m3_soc_h2char_g64x64_t32_w3_01 | 64×64 | 32 | 3 | wait sensitivity |
| large | s2_m3_soc_h2char_g256x256_t32_w1_01 | 256×256 | 32 | 1 | scaling |
| large | s2_m3_soc_h2char_g320x240_t32_w1_01 | 320×240 | 32 | 1 | scaling/partial tile |
| large | s2_m3_soc_h2char_g480x320_t32_w1_01 | 480×320 | 32 | 1 | scaling480-class |

480×480 là tùy chọn về sau, chưa trong batch này. RGB480 không yêu cầu. Irregular37×35/RGB17×19 và các ca suy biến đã có trong17 ZIP frozen; giữ chúng trong kết luận, không bỏ vì chậm và không chạy lại chỉ để làm bảng mới.

## Input và bộ nhớ

Sáu fixture inputs/h2_char_grayWxH_v1 được tạo bởi prepare_h2_characterization.py, INPUT_ONLY. Mẫu coordinate field gồm gradient, cạnh ô và vòng tròn, cùng công thức tại cùng tọa độ; kích thước nhỏ là crop trên-trái của field lớn, không resize. Có generator hash, formula, HEX hash và PGM preview. Mục đích chẩn đoán/scaling; chưa gọi natural-image dataset hoặc bằng chứng chất lượng ảnh ứng dụng. Không tạo output Sobel/cycle/event giả.

Frame lớn nhất480×320 có153600byte mỗi input/output, nằm trong mỗi vùng256KiB. Không tăng frame RAM hoặc bus32. Testbench memory vẫn nằm ngoài ASIC top. Khả năng capacity chưa phải functional PASS ở480; chỉ công nhận sau chạy thật và audit.

## Gate và bằng chứng

Precheck xác minh package H2 theo manifest đã pin, nguồn RTL/TB/firmware/checker/runner khớp baseline; copy wrapper có thể cập nhật riêng. Fixture phải khớp công thức và hash, không chỉ kích thước. Mỗi RUN vẫn dùng runner/checker M3 đã freeze, snapshot toàn nguồn/checker/input và firmware, năm unit tests, bốn CPU execution, golden pixel/tile/traffic. Định nghĩa experiment mới cũng nằm trong snapshot scripts của RUN.

Audit kiểm tra RUN config, image bytes/metadata, snapshot functional hashes, experiment definition, archive so với directory và audit M3. S1 profile v1/v2 phải khớp. Lưu cycles, transactions, bus bytes, wait/arbitration, first/last region latency và simulation wall time từ evidence. Không cộng counters chồng lấn; không suy useful bytes từ toàn bộ word response. Chưa có ASIC clock/power mới để suy FPS/energy.

Timeout mỗi subprocess: pilot1800s, large7200s; watchdog500000000 target cycles. Đây là giới hạn thực thi để tránh timeout mặc định ở ảnh lớn, không phải ước tính kết quả hoặc tốc độ. Không sửa timing model/RTL. Nếu timeout/fail, batch dừng, export archive lỗi nếu có; giữ nguyên RUN để chẩn đoán, không tự retry hoặc ghi đè.

## Lệnh cho người dùng — Ubuntu

```bash
bash "/mnt/e/aa. PPA_Project_List/aaa.PicoRV32_Sobel_ASIC_PPA/upgrade/scripts/00_copy_to_ubuntu.sh"
```

```bash
cd "$HOME/openlane_projects/picorv32_sobel_stage2"
```

```bash
bash scripts/26_run_h2_characterization.sh pilot
```

Mong đợi: H2 CHARACTERIZATION PILOT AUDIT PASS:7 RUNs (khoảng trắng theo terminal). ZIP tự export về upgrade/reports Windows. RUN có sẵn chỉ dùng lại sau khi audit/binding/config/archive khớp; failed/incomplete RUN không overwrite.

Sau khi pilot được xem xét, lượt lớn đã chuẩn bị bằng lệnh dưới. Script tự audit đủ bảy pilot trước khi cho chạy; người dùng không cần chạy ngay khi chưa xem thời gian/log pilot:

```bash
bash scripts/26_run_h2_characterization.sh large
```

Mong đợi: H2 CHARACTERIZATION LARGE AUDIT PASS:3 RUNs. Đây là benchmark RTL, không phải OpenLane78/81stage. Trợ lý không thực thi các lệnh simulation này.

## Trạng thái và bước sau

Hiện: INPUT_ONLY và precheck tĩnh được chuẩn bị; mười RUN characterization USER_RUN_REQUIRED. Không tạo số liệu mới. Freeze H2/tag/evidence cũ bất biến. Sau audit hai phase, tổng hợp bảng scaling/tile/wait gắn exact hashes, kể cả kết quả bất lợi; sau đó mới chuẩn bị task B H1/H2 PPA có kiểm soát. H3/FPGA không nằm trong task này.
