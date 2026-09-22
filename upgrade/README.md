**Cập nhật 23/09: H2 ECO đã chạy và audit đạt với các giới hạn công khai. Xem [H1_H2_PPA_ACCEPTANCE.md](H1_H2_PPA_ACCEPTANCE.md). Các lệnh/tag ECO bên dưới là lịch sử, không chạy lại.**

**Bước chạy tiếp theo: [H2_ECO_RUN_GUIDE.md](H2_ECO_RUN_GUIDE.md). Đã đạt preflight tĩnh; physical ECO chưa chạy. Tiếp tục H2 bằng 4 buffer có mục tiêu từ checkpoint repair01, dùng scripts 34/35/36 và RUN mới `s2_ppa_h2_eco_clk50_01`.**

**Cập nhật sau H2 repair_01: vẫn FAIL (fanout1/cap2/slew4), chưa phải H3. Xem H2_REPAIR01_REVIEW.md. Các lệnh repair_01 bên dưới là lịch sử; không chạy lại tag cũ.**

# Stage 2 — RV32 image-processing research

Ngày khởi tạo: 2026-09-17. Thư mục này là dự án nâng cấp độc lập; nguồn và báo cáo stage 1 ở thư mục cha được giữ nguyên.

**M1/M2/M3 đã có bằng chứng nghiệm thu; H2 baseline được freeze.** Mười RUN characterization Gray8 (tới480×320, tile16/32/64 và wait0/1/3 theo ma trận chọn lọc) đã audit. Xem [nghiệm thu characterization](H2_CHARACTERIZATION_ACCEPTANCE.md). RGB480 và ảnh tự nhiên chưa được nghiệm thu.

**Bước hiện hành: [PPA_RUN_GUIDE.md](PPA_RUN_GUIDE.md).** Chuẩn bị cặp physical H1/H2 cùng phương pháp RUN16, nguồn/PDK/tool được khóa. Config/lint/SDC preflight khác với physical PASS; H1 physical đã review, xem [H1_PPA_REVIEW.md](H1_PPA_REVIEW.md); H2 physical RUN01 FAIL cap1/fanout6; xem [H2_PPA_REVIEW.md](H2_PPA_REVIEW.md). Các hướng dẫn M1/M2/M3 ghi các lượt đã qua, không tự chạy lại.

- Nguồn gốc: RTL RUN16 + firmware RGB hiện có; nguồn nhập từ working tree được lưu trong `baseline/stage1_import.zip` với SHA-256 từng tệp và trạng thái Git tại lúc nhập. Không tuyên bố toàn working tree là commit RUN16 sạch.
- Phần RTL/firmware được khóa bằng hash trong M1. Thay đổi M1 chỉ ở testbench quan sát, checker, runner và tài liệu stage 2.
- Observer đếm đúng cạnh handshake trong cửa sổ start/end cũ; không lái tín hiệu DUT/bộ nhớ. Chia bus idle/wait/accept và DMA arbitration/service wait. Các counter CPU/DMA có thể chồng lấn.
- Đo số giao dịch ảnh, byte bus đọc 32 bit, byte ghi theo strobe, chu kỳ/pixel/kênh và latency vùng đầu/cuối. Số byte đọc bus không phải số byte ảnh duy nhất.
- S0/H1 giữ nguyên; S1 bổ sung horizontal-window reuse. Runner M2 đo cả ba trên ENABLE_SOBEL=1. Không lấy cycles SW M1 làm cycles SW M2 vì bus topology đã đổi để so sánh cùng hardware.
- Gray tối đa512, RGB tối đa256 theo phần cứng nền; target stage2 là cạnh dài480 sau nâng cấp. Không giả vờ RGB480 đã hỗ trợ.
- H1 ASIC stage2 đã review đạt các flow checks; H2 RUN01 FAIL cap1/fanout6; repair prepared. RUN16 lịch sử còn fanout1, power vectorless, không gồm RAM ngoài/pads/package. Clock constraint lịch sử50ns=20MHz.
- Launcher physical stage2: scripts/30_ppa_precheck.sh, 31_run_ppa.sh, 32_collect_ppa.sh. Chỉ người dùng chạy flow. physical/run16_reference là tham chiếu lịch sử, không dùng launcher bên trong.

Ubuntu dùng riêng `~/openlane_projects/picorv32_sobel_stage2`; export chỉ về `upgrade/reports`. Không dùng lệnh lịch sử từ tài liệu stage1 để chạy stage2. Không xóa/ghi đè RUN hoặc archive đã có.

Trợ lý chỉ kiểm tra tĩnh/compile/host checker; người dùng chạy simulation/OpenLane. Lịch 2–3 ngày là mong muốn tăng tốc phối hợp, không phải cam kết functional/PPA PASS hay hoàn thành bài báo.
