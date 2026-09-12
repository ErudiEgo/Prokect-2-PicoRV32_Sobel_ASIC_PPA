# repair_03: chẩn đoán và bản sửa có mục tiêu repair_04

Ngày 2026-09-12. Người dùng chạy flow; trợ lý chỉ đọc kết quả và chuẩn bị/kiểm tra tĩnh. Chưa có kết quả vật lý repair_04.

## Bằng chứng và kết luận

Archive gốc: `reports/picorv32_sobel_clk50_repair_03_collect_20260912T042558472133Z.tar.gz`.
SHA256: `d62e92ac1843c521d339787b1eb6f87a628c7ad9dc6dde6b02252b307ad7a21c`.
Bản trích đọc: `build/repair03_review_cjmiheip`. RUN Ubuntu và archive gốc giữ nguyên.

| Tiêu chí | repair_02 | repair_03 |
|---|---:|---:|
| Antenna sau DRT, net/pin | 7/7 | 6/7 |
| Slew violations, max_ss | 48 | 668 |
| Cap violations, max_ss | 5 | 67 |
| Fanout violations, max_ss | 338 | 60 |
| Magic/KLayout DRC, LVS, XOR | 0 | 0 |
| Standard-cell area, µm² | 130911 | 153139 |

**repair_03 chưa PASS và không cải thiện tổng thể.** Hạ ngưỡng heuristic xuống 90 µm làm số diode lớn; state cuối ghi 9932 antenna cells. Số `antenna_diodes_count=79` là số của một bước sửa, không phải tổng diode. Không dùng việc giảm một net antenna để che lỗi điện tăng.

Nguồn: `50-openroad-checkantennas-1/reports/antenna.rpt`, `59-openroad-stapostpnr/max_ss_100C_1v60/checks.rpt`, `79-misc-reportmanufacturability/state_out.json`. Setup/hold không có vi phạm theo checker; formal EQY chưa chạy, giới hạn này không thay đổi.

## Pin cần bảo vệ theo báo cáo cuối

| Net | Pin | Layer lỗi | Partial / required |
|---|---|---|---|
| net2709 | fanout2599/A | met3 | 1923.62 / 400 |
| net926 | fanout2264/A | met3 | 1762.32 / 400 |
| net2369 | _07123_/A1 | met4; via4 | 916.70 / 400; 10.16 / 6 |
| net2393 | fanout865/A | met3 | 674.73 / 400 |
| net2393 | fanout866/A | met3 | 674.73 / 400 |
| net1651 | fanout1541/A | met3 | 545.26 / 400 |
| net2383 | fanout901/A | met3 | 480.41 / 400 |

Có 8 dòng layer nhưng chỉ 7 pin trên 6 net. Parser gộp các layer của cùng pin, không chèn lặp một diode cho mỗi dòng. Đã đối chiếu cả 7 pin/net vào ODB stage 48 bằng chế độ `--plan-only`, không sửa ODB.

Tên net mới phần lớn thuộc mạng buffer sau repair; không thể chỉ bám tên 7 net ở repair_02. Lần này `44-openroad-repairdesignpostgrt-1` thêm 1683 buffer và resize 152 instance. Lần antenna repair tiếp theo ghi 52 → 15 → 1 → 0 theo kiểm tra nội bộ router, nhưng checker độc lập vẫn thấy lỗi. Vì vậy tiếp tục tăng số iteration của router không trực tiếp xử lý chênh lệch này.

Cap cuối lớn nhất tại `fanout2580/X`: 0.118824 pF so với giới hạn library 0.081492 pF. Slew tại pin nhận đạt 2.180457 ns so với 1.5 ns. Lần sửa mới cần kiểm tra cả tải và antenna sau đi dây thật.

## Thay đổi cho repair_04

- Giữ CPU, Sobel, bus, firmware, pin order, SDC, clock 50 ns, density/utilization, CTS và các checker/giới hạn. Hash chức năng phải còn khớp `soc_image_smoke_01` trước RUN.
- Đặt `RUN_HEURISTIC_DIODE_INSERTION=false`: dừng cách chèn diode hàng loạt theo chiều dài. Đây là bước tối ưu tùy chọn, không phải checker. `RUN_ANTENNA_REPAIR=true`, diode trên input ports và tất cả bước kiểm tra antenna/DRC/LVS vẫn giữ.
- Giữ hai bước thêm của repair_03; thêm `Sobel.AntennaClosure` ngay sau DetailedRouting, trước RemoveRoutingObstructions và checker antenna cuối. **Classic có 81 bước chính: 78 gốc + 3 bước thêm.** Heuristic và EQY vẫn hiện trong danh sách nhưng skip theo cấu hình đã ghi.
- Bước mới đọc báo cáo `check_antennas -verbose` từ chính layout hiện tại. Đối chiếu số pin/net đã parse với metric checker; thiếu/mâu thuẫn bằng chứng thì dừng báo lỗi.
- Với mỗi pin đang vi phạm, chèn một diode SKY130 cạnh pin đó, dùng thư viện `DiodeInserter` của OpenLane cài sẵn với lựa chọn phía theo pin. Không gọi thuật toán quét toàn net, không hardcode tên net của RUN cũ. Kiểm tra toàn bộ target trước khi sửa; xác nhận mọi instance/cổng nối cũ còn nguyên ngay sau thao tác chèn.
- Xóa detailed signal wires trong **bản ODB của RUN mới** trước khi di chuyển cell; không giữ dây cũ sau thay đổi placement. PG special wires không bị thao tác này xóa. Legalize, chạy repair_design tại `max_ss_100C_1v60`, chạy repair_timing với các RSZ corners gốc, rồi detailed routing lại. Đây là một lần sửa vật lý thực sự, không phải chỉnh số trong báo cáo.
- Đọc lại antenna sau DRT; tối đa **3 vòng sửa**. Nếu sạch thì dừng vòng lặp; nếu còn lỗi thì giữ nguyên số thật và tiếp tục các checker cuối để có đầy đủ chẩn đoán. Không ghi metric 0 thủ công, không gọi hết số vòng là PASS.

Mỗi vòng giữ `targets.json`, báo cáo checker, config, ODB, netlist, log và state của từng bước. `closure_history.json` ghi số lỗi trước/sau mỗi vòng. Chạy có thể lâu hơn vì cần reroute, nhưng có giới hạn số vòng rõ ràng. Các tên thư mục stage có thể lệch vì bước heuristic được skip; dùng step ID và báo cáo, không đoán từ một số thứ tự cố định.

## Nguồn triển khai và kiểm chứng

`scripts/antenna_targets.py`: đọc report và gộp unique pin; `targeted_diodes.py`: ODB edit chỉ ở user-run flow, có `--plan-only` đọc thuần; `antenna_closure.py`: bước Classic có giới hạn vòng; `openlane_with_repairs.py`: đăng ký bước rồi gọi CLI OpenLane gốc. Launcher dùng bản script đã đóng băng trong snapshot; không sửa package OpenLane cài đặt.

Dùng trực tiếp `DiodeInserter` của OpenLane 2.3.10, Apache-2.0, Efabless/Sylvain Munaut; không sao chép hay sửa IP PicoRV32. Cơ chế bước mở rộng theo [OpenLane custom steps](https://openlane2.readthedocs.io/en/latest/usage/writing_custom_steps.html) và [đăng ký plugin](https://openlane2.readthedocs.io/en/latest/usage/writing_plugins.html). API cụ thể được đọc từ Docker đang cài.

Đã kiểm tra parser bằng báo cáo RUN thật (6 net/7 pin), ba unit test cho gộp layer/thiếu report/report sạch; đọc ODB resolve đúng cả 7 target và API cần dùng. Precheck đầu `build/asic_precheck_4j3otCs9` nạp Classic 81 bước, lint và SDC đạt. Precheck mở rộng `build/asic_precheck_9PFQFDqb` đã xác nhận cấu hình từng bước con và override SS. Bản đóng băng nạp/lint/SDC đạt tại `build/repair04_frozen_check_klfuNQQx`; CLI wrapper trả đúng OpenLane v2.3.10 với --version. Cú pháp shell/Python đạt, launcher dùng script đã freeze. Các kiểm tra này không chạy chèn diode, repair, placement, routing hay mô phỏng.

**Giới hạn:** chưa chạy thử các thao tác vật lý của bước mới; RUN người dùng mới xác định hiệu quả placement/route và tính hội tụ. Bản sửa nhằm xử lý đúng pin còn lỗi, không đảm bảo trước antenna PASS. Slew/cap/fanout, setup/hold, DRC/LVS/XOR đều phải được đọc lại. Power vẫn vectorless, IR chưa có nguồn package thật; PPA top vẫn không gồm RAM ngoài/pad/package.

Lệnh chạy và thu thập: [ASIC_RUN_GUIDE.md](ASIC_RUN_GUIDE.md), tag `picorv32_sobel_clk50_repair_04`.
