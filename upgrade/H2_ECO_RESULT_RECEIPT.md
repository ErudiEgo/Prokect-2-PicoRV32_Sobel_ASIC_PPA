# H2 ECO — tiếp nhận kết quả 2026-09-22

RUN: `s2_ppa_h2_eco_clk50_01`.

Đã lưu console người dùng, báo cáo collector và receipt/hash vào `build/h2_eco_result_receipt_01/`. Archive gốc giữ nguyên tại `reports/s2_ppa_h2_eco_clk50_01_collect_20260922T131043447357Z.tar.gz`.

SHA256 archive: `e1ee1a54bed2982dd53fed5d301bb2e95b650bea460354d9deb9b5ce9fb4a112`.

Báo cáo collector trong archive ghi `PASS_FOR_REPORTED_FLOW_CHECKS`: 89/89 check PASS, exit 0. Cap/slew/fanout đều 0; antenna violating nets 0. Console báo LVS match uniquely, DRC và antenna đạt; final views đã được xuất.

Setup worst slack 14.3360669615 ns; hold worst slack 0.1061338825 ns. Standard-cell area 352481 um²; standard-cell count 47431. Đây là số liệu đọc từ báo cáo, chưa thay thế audit độc lập báo cáo gốc.

Thời gian continuation 1337.503877878189 giây (~22 phút 18 giây), không bao gồm thời gian RUN cha. Đây là H2 ECO tiếp tục từ repair01, không phải H3 hoặc một lượt full flow từ synthesis.

`pair=MISSING` là trường nhãn pair không có trong execution của launcher continuation. Parent RUN và hash READY vẫn có trong execution. Không xem riêng dòng nhãn này là lỗi vật lý; cần làm rõ định dạng trong lượt bảo trì tiếp theo.

Giới hạn còn nguyên: EQY bị bỏ qua; threshold wirelength chưa đặt; IR không có VSRC_LOC_FILES; cảnh báo LEF và hai output thiếu antenna diffusion information cần đối chiếu báo cáo gốc. PPA không gồm external program/frame RAM, pads/package; power là vectorless. Chưa tuyên bố tapeout sign-off.

Trạng thái tiếp theo: chờ chỉ thị người dùng. Công việc ưu tiên khi tiếp tục là audit độc lập nguồn/checkpoint, topology sau ECO, báo cáo tất cả corner và các cảnh báo; sau đó chốt bảng so sánh H1/H2. Không chạy lại flow chỉ để lấy báo cáo.
