# Lượt hiện hành: regression sau RGB32

RGB32 đã audit đạt; không chạy lại lệnh smoke trong phần lịch sử bên dưới. Xem [kết quả](M3_RGB32_REVIEW.md).

Sau khi copy nguồn bằng scripts/00_copy_to_ubuntu.sh và cd vào workspace stage2, chạy:

```bash
bash scripts/24_finish_m3.sh
```

Wrapper chạy precheck một lần rồi tuần tự sáu RUN mới:

| RUN | Input | Tile / memory_wait |
|---|---|---|
| s2_m3_soc_rgb17x19_w3_01 | rgb_partial17x19_v1 | 16 / 3 |
| s2_m3_soc_gray37x35_w1_01 | demo | 16 / 1 |
| s2_m3_soc_rgb1x1_w0_01 | m2_1x1_c3 | 1 / 0 |
| s2_m3_soc_rgb1x7_w3_01 | m2_1x7_c3 | 2 / 3 |
| s2_m3_soc_gray9x1_w1_01 | m2_9x1_c1 | 16 / 1 |
| s2_m3_soc_gray64_t64_w1_01 | shapes64_00_01 | 64 / 1 |

Mỗi RUN vẫn có unit checks và bốn lần CPU thực thi. ZIP tự export về Windows upgrade/reports, cả khi simulation thất bại có archive. Điều kiện hoàn tất: `M3 REGRESSION SIX AUDIT PASS`. Nếu lỗi thì dừng, giữ nguyên RUN và gửi lỗi/ZIP; không ghi đè. RUN có sẵn chỉ dùng lại khi audit, source/image/settings và archive khớp. Không chạy lại RGB32.

## Hướng dẫn smoke trước đây — đã hoàn thành

# M3 — tích hợp DMA v2 với RV32

M2 đã có sáu RUN audit đạt. DMA v2 độc lập đã đạt 181 ca trong `s2_m3_unit_01`; xem M2_M3_UNIT_ACCEPTANCE.md. M3 SoC hiện mới biên dịch thành công, chưa chạy CPU. Không có PPA stage2.

Nguồn mới: `candidate/picorv32_sobel_soc_m3.v`, `candidate/tb_sobel_soc_m3.sv`, `firmware/h2/`. Core, CPU, arbiter, DMA v1 và firmware S1/H1 được giữ nguyên. Tham số DMA_VERSION chọn một accelerator tại elaboration: v1 hoặc v2; không ghép cả hai engine vào cùng physical top. CPU/program RAM/image RAM vẫn là bộ nhớ ngoài được mô hình hóa bởi testbench.

| Thư mục đo | Firmware identity | DMA_VERSION | Mục đích |
|---|---:|---:|---|
| s1_v1 | 2 | 1 | Phần mềm S1 trên SoC v1 |
| h1 | 1 | 1 | DMA v1 làm đối chứng |
| s1_v2 | 2 | 2 | Cùng binary S1 trên SoC v2 |
| h2 | 3 | 2 | Firmware H2 điều khiển DMA v2 |

H2 phát triển từ H1: đổi kiểm tra TIL1 sang TIL2 và identity sang3; trình tự điều khiển, thuật toán, tile, channel và memory map giữ nguyên. Binary H2 808 byte; build RV32I/ILP32 -O2 bằng cùng compiler, có rebuild S0/H1 và đối chiếu byte-identical. HEX, ELF, disassembly, sources và compiler/options được lưu trong manifest/build_evidence.zip.

Mỗi RUN đóng băng nguồn, chạy năm unit test rồi bốn lần CPU thực thi. So từng pixel với golden độc lập; xác minh tile events, cycles, hash firmware, DMA_VERSION và traffic. H1 phải đọc đúng số hàng xóm của v1; H2 phải đọc đúng tổng diện tích halo được cắt theo frame cho từng tile/channel. Đây là giá trị kỳ vọng để kiểm tra counter đo, không thay thế counter. S1 trên v1/v2 phải có profile giống nhau; khác biệt sẽ dừng để điều tra. Không ép H2 phải nhanh hơn mới công nhận đúng chức năng.

## Lượt đầu: RGB32, tile16, memory_wait1

Nhập trong Ubuntu, từng lệnh riêng:

```bash
bash "/mnt/e/aa. PPA_Project_List/aaa.PicoRV32_Sobel_ASIC_PPA/upgrade/scripts/00_copy_to_ubuntu.sh"
```

```bash
cd "$HOME/openlane_projects/picorv32_sobel_stage2"
```

```bash
bash scripts/23_run_m3_soc.sh s2_m3_soc_rgb32_w1_01 --image inputs/rgb_smoke32_v1 --tile 16 --memory-wait 1
```

Mong đợi lần lượt `M3 STATIC CHECK PASS`, `M3 SOC FUNCTIONAL TEST PASS`, `M3_SINGLE_RUN_AUDIT_PASS`. Warning Icarus upstream về sensitivity toàn mảng cpuregs được ghi trong compile log, không phải kết quả sign-off. Timeout mỗi subprocess600 giây; watchdog100 triệu chu kỳ. Khi lỗi, giữ nguyên RUN và export để chẩn đoán, không xóa/ghi đè/chạy lại cùng tag.

```bash
bash scripts/04_export_sim.sh s2_m3_soc_rgb32_w1_01
```

ZIP được xuất về `upgrade/reports` Windows. Audit chỉ đọc dữ liệu đã có, không mô phỏng lại. Terminal hiển thị TILE và tiến độ từng cấu hình. Chưa chạy OpenLane trong lượt này.

Sau smoke audit đạt, mở rộng RGB17×19/wait3, gray37×35, ảnh suy biến và tile64. Chỉ sau integration regression mới chốt kiến trúc/memory480 và chuẩn bị PPA. Tỷ số chu kỳ chưa phải tỷ số tốc độ ASIC khi hai thiết kế có timing khác; chưa có area/power/energy của v2. Giữ chi phí CPU/control/transfer trong cửa sổ đo; boot và host decode/replay ở ngoài. Thời gian chạy simulator được ghi riêng.
