# M2 — người dùng chạy trong Ubuntu

M1 đã được nghiệm thu, không chạy lại các tên RUN M1. M2 thêm firmware S1 và đo S0/S1/H1 trên cùng SoC có bộ tăng tốc. Đây là simulation RTL, chưa phải OpenLane.

## Copy và precheck

```bash
bash "/mnt/e/aa. PPA_Project_List/aaa.PicoRV32_Sobel_ASIC_PPA/upgrade/scripts/00_copy_to_ubuntu.sh"
```

```bash
cd "$HOME/openlane_projects/picorv32_sobel_stage2"
```

```bash
bash scripts/10_precheck_m2.sh
```

Cần `M2 STATIC CHECK PASS`. Có sẵn HEX S1 nên không cần build firmware/compiler RISC-V trên Ubuntu. Precheck cần gcc native để kiểm tra hàm S1 trên host, không thực thi CPU RV32; gcc đã được xác minh có trên Ubuntu của dự án. Các warning sensitivity cpuregs upstream giữ nguyên. Wrapper RUN cũng precheck để tránh chạy nguồn vừa sửa chưa kiểm tra.

## RUN đầu — RGB32

```bash
bash scripts/11_run_m2_tests.sh s2_m2_rgb32_w1_01 --image inputs/rgb_smoke32_v1 --tile 16 --memory-wait 1 --timeout-seconds 600 --max-cycles 100000000
```

Cần unit tests PASS, `M2 PIXEL/PROFILE CHECK PASS` cho s0/s1/h1, rồi `M2 FUNCTIONAL TEST PASS`. Mỗi biến thể đúng3072mẫu/4vùng. Không yêu cầu chu kỳ S0 bằng M1 vì hardware bus topology nay giống H1. Không dự đoán/ép tốc độ S1 trước khi chạy.

```bash
bash scripts/04_export_sim.sh s2_m2_rgb32_w1_01
```

Export cả khi FAIL; dừng nếu lỗi và gửi bằng chứng. Nếu PASS:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 scripts/audit_m2.py reports/s2_m2_rgb32_w1_01
```

Cần `M2_SINGLE_RUN_AUDIT_PASS`; đây là đọc lại evidence, không chạy lại simulation. Gửi ZIP ở Windows upgrade/reports để đánh giá trước khi chạy ma trận lớn.

## Ca tiếp theo sau smoke đạt

```bash
bash scripts/11_run_m2_tests.sh s2_m2_rgb17x19_w3_01 --image inputs/rgb_partial17x19_v1 --tile 16 --memory-wait 3 --timeout-seconds 600 --max-cycles 100000000
```

```bash
bash scripts/04_export_sim.sh s2_m2_rgb17x19_w3_01
```

```bash
bash scripts/11_run_m2_tests.sh s2_m2_gray37x35_w1_01 --image inputs/demo --tile 16 --memory-wait 1 --timeout-seconds 600 --max-cycles 100000000
```

```bash
bash scripts/04_export_sim.sh s2_m2_gray37x35_w1_01
```

Ca RGB17x19 cần969mẫu/4vùng; gray37x35 cần1295mẫu/9vùng ở cả ba biến thể. Chạy audit_m2.py tương ứng từng thư mục RUN sau PASS.

## Ca suy biến để nghiệm thu S1, chỉ sau các ca trên đạt

```bash
bash scripts/11_run_m2_tests.sh s2_m2_rgb1x1_w0_01 --image inputs/m2_1x1_c3 --tile 1 --memory-wait 0
```

```bash
bash scripts/04_export_sim.sh s2_m2_rgb1x1_w0_01
```

```bash
bash scripts/11_run_m2_tests.sh s2_m2_rgb1x7_w3_01 --image inputs/m2_1x7_c3 --tile 2 --memory-wait 3
```

```bash
bash scripts/04_export_sim.sh s2_m2_rgb1x7_w3_01
```

```bash
bash scripts/11_run_m2_tests.sh s2_m2_gray9x1_w1_01 --image inputs/m2_9x1_c1 --tile 16 --memory-wait 1
```

```bash
bash scripts/04_export_sim.sh s2_m2_gray9x1_w1_01
```

Kỳ vọng số mẫu/vùng mỗi biến thể lần lượt3/1,21/4,9/1; mọi pixel/timestamp/profile phải đạt checker. Khi sửa nguồn, dùng RUN hậu tố mới, không xóa/ghi đè. Audit từng thư mục bằng cùng công cụ.

Không có lệnh OpenLane M2: RTL phần cứng vẫn RUN16. S1 đúng/nhanh hay chậm không tự chứng minh power/PPA mới. Chưa hỗ trợ replay ba biến thể; xem output.pgm/output.ppm trong s0/s1/h1 và bảng cycles từ SUMMARY.txt.
