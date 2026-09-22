# Stage2 M1 — lệnh người dùng chạy trong Ubuntu

Đây là các RUN mới để nghiệm thu baseline/profiling, không phải lệnh OpenLane. Mỗi tên dùng một lần; khi sửa nguồn dùng hậu tố02 và đổi tương ứng mọi lệnh. Stage1 giữ nguyên. Không dùng launcher lịch sử trong tài liệu RGB/RUN16.

## 1. Copy nguồn riêng

```bash
bash "/mnt/e/aa. PPA_Project_List/aaa.PicoRV32_Sobel_ASIC_PPA/upgrade/scripts/00_copy_to_ubuntu.sh"
```

Cần `COPY PASS` và đích `picorv32_sobel_stage2`. Script từ chối thư mục đích có nội dung nhưng không mang identity stage2; giữ reports/build/RUN có sẵn.

```bash
cd "$HOME/openlane_projects/picorv32_sobel_stage2"
```

```bash
bash scripts/01_precheck.sh
```

Cần `STATIC CHECK PASS`; đây là compile và checker host, không chạy RTL. HEX có sẵn nên chưa cần build firmware. Hai warning sensitivity `cpuregs` upstream mỗi SoC variant được giữ nguyên, không gọi là simulation PASS. Wrapper chạy RUN sẽ thực hiện lại precheck để tránh dùng trạng thái kiểm tra cũ sau sửa nguồn.

## 2. RUN RGB32 — kiểm tra observer không đổi kết quả

```bash
bash scripts/03_run_soc_tests.sh s2_m1_rgb32_w1_01 --image inputs/rgb_smoke32_v1 --tile 16 --memory-wait 1 --timeout-seconds 600 --max-cycles 100000000
```

Cần unit tests PASS, `PIXEL CHECK PASS` và `STAGE2 PROFILE CHECK PASS` cả SW/HW, `FUNCTIONAL TEST PASS`. Sau chạy mới đối chiếu SW1352946/HW206960 với RUN RGB32 lịch sử; chưa gán số này làm kết quả RUN mới.

Export cả khi FAIL; nếu FAIL thì dừng các bước phụ thuộc và gửi ZIP:

```bash
bash scripts/04_export_sim.sh s2_m1_rgb32_w1_01
```

## 3. RUN RGB17x19 — partial tile và memory wait3

```bash
bash scripts/03_run_soc_tests.sh s2_m1_rgb17x19_w3_01 --image inputs/rgb_partial17x19_v1 --tile 16 --memory-wait 3 --timeout-seconds 600 --max-cycles 100000000
```

Cần FUNCTIONAL/PROFILE PASS; 969 samples và4 vùng; HW969writes/12starts. Không có expected speedup áp đặt.

```bash
bash scripts/04_export_sim.sh s2_m1_rgb17x19_w3_01
```

## 4. RUN gray37x35 — hồi quy gray trên firmware RGB

```bash
bash scripts/03_run_soc_tests.sh s2_m1_gray37x35_w1_01 --image inputs/demo --tile 16 --memory-wait 1 --timeout-seconds 600 --max-cycles 100000000
```

Cần FUNCTIONAL/PROFILE PASS;1295samples,9vùng; HW1295writes/9starts.

```bash
bash scripts/04_export_sim.sh s2_m1_gray37x35_w1_01
```

## 5. Audit nghiệm thu M1, không chạy lại simulation

```bash
PYTHONDONTWRITEBYTECODE=1 python3 scripts/audit_m1.py reports/s2_m1_rgb32_w1_01 reports/s2_m1_rgb17x19_w3_01 reports/s2_m1_gray37x35_w1_01
```

Cần `STAGE2_M1_ACCEPTANCE_PASS`. Các ZIP chứa snapshot, comparison, trace, profile và stage2_metrics; file được export về Windows `upgrade/reports/`. Gửi ba ZIP hoặc báo export xong để đọc bằng chứng. Không chạy lại RUN chỉ để xem báo cáo.

Tùy chọn replay từ dữ liệu đã kiểm chứng:

```bash
python3 scripts/replay.py reports/s2_m1_rgb32_w1_01
```

Đây là phát lại trace theo mốc chu kỳ, không phải chip/CPU đang chạy trực tiếp. Chưa có lệnh OpenLane stage2: cần hoàn tất các cổng chức năng và chọn kiến trúc trước.
