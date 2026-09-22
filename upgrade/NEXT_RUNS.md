# Việc tiếp theo — 2026-09-21

M1 đã nghiệm thu. M2 RGB32 đã audit đạt; năm workload còn thiếu được chạy tuần tự bằng một wrapper. DMA v2 đã có candidate và unit test độc lập; chưa thay RTL SoC nền. Không chạy lại RGB32 đã có bằng chứng.

Nhập trong Ubuntu:

```bash
bash "/mnt/e/aa. PPA_Project_List/aaa.PicoRV32_Sobel_ASIC_PPA/upgrade/scripts/00_copy_to_ubuntu.sh"
```

```bash
cd "$HOME/openlane_projects/picorv32_sobel_stage2"
```

```bash
bash scripts/12_finish_m2.sh
```

Wrapper chạy precheck, rồi RGB17×19/wait3, gray37×35/wait1, RGB1×1/wait0, RGB1×7/wait3, gray9×1/wait1. RUN cụ thể là `s2_m2_rgb17x19_w3_01`, `s2_m2_gray37x35_w1_01`, `s2_m2_rgb1x1_w0_01`, `s2_m2_rgb1x7_w3_01`, `s2_m2_gray9x1_w1_01`. Mỗi RUN có 4 unit test và 3 lần CPU thực thi S0/S1/H1. Không phải flow vật lý 78/81 bước.

Điều kiện thành công: `M2 REMAINING FIVE AUDIT PASS`. ZIP tự xuất về `upgrade/reports` trên Windows. Nếu RUN có sẵn và đủ evidence, wrapper audit rồi dùng lại; không chạy lại. Nếu gặp RUN thất bại/thiếu hoặc ZIP khác cùng tên, dừng và giữ nguyên để chẩn đoán; không tự xóa hay đổi tên để chạy lặp. Gửi lỗi đầu tiên nếu batch dừng.

Sau đó chạy [unit DMA v2](DMA_V2_CANDIDATE.md) và export ZIP theo hai lệnh trong tài liệu. Mục tiêu tiếp theo là nghiệm thu M2 đủ bộ và audit unit DMA v2; chưa gọi toàn stage2 hoàn tất.

Các cổng còn lại, theo thứ tự:

1. M2 đủ sáu workload, S0/S1/H1 cùng hardware và output chính xác.
2. DMA v2 unit PASS → tích hợp RV32 + firmware H2 → so sánh S1/H1/H2 gồm transfer/control và latency từng vùng. Có thể sửa ứng viên nếu không nhanh hơn.
3. Chốt cách cấp bộ nhớ cho ảnh cạnh dài480, test workload và biên ảnh phù hợp; không tăng giới hạn RGB bằng cách bỏ check.
4. Chốt RTL/firmware, xác minh phiên bản OpenLane Classic/PDK thực tế, chuẩn bị constraint và phạm vi physical top. Người dùng chạy PPA; đọc báo cáo thật, công khai vi phạm/missing checks và RAM ngoài phạm vi.
5. Đóng gói dữ liệu, bảng/đồ thị có script tái tạo, hạn chế nghiên cứu và bản thảo bài báo. Chưa bảo đảm tính mới học thuật hay chấp nhận bài chỉ từ một kết quả speedup.
