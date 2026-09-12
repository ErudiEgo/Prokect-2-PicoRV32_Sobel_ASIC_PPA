# Chẩn đoán ASIC base_01 và cấu hình repair_02

RUN đã chạy bởi người dùng: `picorv32_sobel_clk50_base_01`. Trợ lý chỉ đọc archive và ODB có sẵn, không chạy lại flow. Archive gốc giữ nguyên tại `reports/picorv32_sobel_clk50_base_01_collect_20260911T172749972219Z.tar.gz`, SHA256 `3d9bca1fc145165707cd9da71a4e36b442f0705dfcf49a5a221f2c9bda3a3c4d`.

## Kết quả xác nhận

| Hạng mục | Kết quả base_01 | Nguồn trong RUN |
|---|---|---|
| Flow | Exit 2, đi hết các bước nhưng còn deferred errors | runtime.txt / flow.log |
| DRC Magic/KLayout, LVS, XOR | 0 vi phạm theo metrics | 76-misc-reportmanufacturability/state_out.json |
| Setup/hold | Slack dương ở cả 9 corner được báo cáo | 56-openroad-stapostpnr và metrics theo corner |
| Antenna sau detailed routing | 14 net / 15 pin vi phạm | 47-openroad-checkantennas-1/reports/antenna_summary.rpt |
| Slew tại max_ss_100C_1v60 | 33 vi phạm | 56-openroad-stapostpnr/max_ss_100C_1v60/checks.rpt |
| Capacitance tại max_ss_100C_1v60 | 8 vi phạm | Cùng checks.rpt |
| Fanout | 61 vi phạm, 41 pin thuộc clkbuf_leaf | Cùng checks.rpt |

Các corner SS khác: nom_ss có slew 22/cap 4; min_ss có slew 16/cap 2. Không cộng số vi phạm các corner để coi là số net độc lập.

Đây là kết quả vật lý chưa đạt đầy đủ. Có dữ liệu area/power/timing để phân tích, nhưng không dùng như thiết kế đã sign-off. Thư mục final có thể chưa được xuất khi còn deferred errors; GDS từng stage có thể đã tồn tại ở streamout. Collector mới phân biệt hai trường hợp này.

## Bằng chứng antenna

Trước repair: 81 net / 93 pin. Vòng repair chèn diode báo lần lượt 109 → 17 → 0 theo bộ kiểm tra nội bộ của router, nhưng CheckAntennas ngay sau repair vẫn báo 11 net / 11 pin. Sau detailed routing tăng lên 14 net / 15 pin. Vì router đã báo 0 trước khi hết số vòng mặc định, chỉ tăng số vòng không giải quyết rõ sự khác biệt này.

Ví dụ nặng nhất: `net7`, pin `_07341_/B2`, met3, partial ratio 1478,03 so với giới hạn 400 (khoảng 3,70 lần). Các ví dụ khác: `net625` 874,38/400; `_04821_` 818,22/400. Có cả vi phạm met1 lẫn met3.

Đọc ODB sau detailed routing ở chế độ read-only xác nhận 13/14 tên net tra được: 12 net chưa có diode; `net933` có một diode nhưng vẫn vi phạm. Net `cpu.cpu_state[5]` chưa khớp tên escape trong lượt tra này nên không suy ra số diode cho nó. Khoảng bao Manhattan theo tọa độ instance của 13 net tra được nằm khoảng 216,88–469,58 µm. Đây là khoảng bao, không phải chiều dài dây routing trích xuất. `net7` dài theo khoảng bao 434,06 µm, driver `input7/X`, không có diode.

Điều này là cơ sở bật thêm heuristic protection cho net dài; không phải sao chép thiết lập của bài UART khác. Ngưỡng 200 µm là giá trị thử nằm dưới khoảng bao nhỏ nhất vừa quan sát, không bảo đảm mọi topology sau placement mới đều được bảo vệ.

## Bằng chứng lỗi điện

Pin `_07529_/Y`: slew 2,093652 ns so với giới hạn library 1,488467 ns; capacitance 0,128132 pF so với giới hạn library 0,086070 pF. Các tải cùng nhánh gồm fanout133–136 và diode ANTENNA_25–28. Có thêm lỗi tương tự tại `_07502_/Y`, `_07441_/Y`, `_07515_/Y`.

Log repair post-GRT của base_01 nạp các corner nominal RC (nom_tt/nom_ff/nom_ss). Bước sửa điện nằm trước bước chèn diode; diode bổ sung làm thay đổi tải. Cần tăng dự phòng sửa và dùng corner RC/PVT phù hợp. Không thay phép gán RTL hoặc nới giới hạn điện để làm mất cảnh báo.

Clock leaf có fanout tới 14 trong khi giới hạn là 10. CTS sink cluster mặc định 25 không bảo đảm fanout cuối cùng <=10. Các net dữ liệu còn lỗi fanout cũng phải kiểm tra ở RUN sau, không chỉ riêng clock.

## Thay đổi cho repair_02

| Tham số | base_01 | repair_02 | Mục đích |
|---|---|---|---|
| RUN_HEURISTIC_DIODE_INSERTION | false | true | Bảo vệ thêm các net dài trước repair antenna |
| HEURISTIC_ANTENNA_THRESHOLD | 90, không hoạt động | 200 µm | Chọn nhóm net dài dựa trên ODB đã đọc |
| GRT_ANTENNA_MARGIN | 10% | 30% | Tăng dự phòng giữa ước lượng global route và routing cuối |
| CTS_SINK_CLUSTERING_SIZE | 25 | 8 | Giảm số tải mỗi cụm clock |
| RSZ_CORNERS | mặc định, log nạp nom_tt/nom_ff/nom_ss | max_ss, min_ff, nom_tt | Dùng corner chậm RC max và nhanh RC min khi tối ưu |
| GRT_DESIGN_REPAIR_MAX_SLEW_PCT | 10% | 40% | Tăng dự phòng slew trước thay đổi tải/routing |
| GRT_DESIGN_REPAIR_MAX_CAP_PCT | 10% | 40% | Tăng dự phòng capacitance |

Clock vẫn 50 ns; fanout limit 10, max transition 1,5 ns, max capacitance 0,2 pF vẫn giữ. Giới hạn library chặt hơn vẫn có hiệu lực. Không đổi RTL/firmware, density, core utilization, I/O constraints hoặc bỏ corner sign-off nào. Số vòng antenna vẫn theo mặc định 3.

Đây là nhóm thay đổi vật lý để thử đồng thời các lỗi có liên quan, chưa phải kết quả sửa thành công. Có thể tăng diode/buffer/area/công suất và thay đổi timing/congestion. Sau RUN mới phải so cả lỗi cũ lẫn những ảnh hưởng này. Nếu còn lỗi sẽ chọn net/stage cụ thể để sửa tiếp; không hứa PASS trước khi người dùng chạy.

## Sửa script tổng hợp

Lỗi cũ: giá trị slew/cap/fanout có thể bị lấy từ state antenna vốn kế thừa metrics của stage sớm hơn, trong khi PASS/FAIL lấy từ post-PNR. Vì vậy có dòng FAIL nhưng value=0 hoặc PASS kèm số cũ khác 0. Lỗi nằm ở hiển thị giá trị; kết luận flow chưa đạt vẫn đúng.

Collector mới chỉ dùng state antenna cho hai giá trị antenna sau routing; metrics khác lấy cùng nguồn với trạng thái đánh giá. Đã chạy regression với 7 giá trị từ archive thật, đồng thời xác nhận integrity snapshot. Archive và báo cáo cũ không bị ghi đè. Collector cũng xuất GDS từ stage streamout nếu flow chưa có final, với nhãn rõ chưa sign-off.

## Kiểm tra trước RUN mới

Sau khi người dùng bật lại Docker, config repair_02 đã nạp được trong OpenLane 2.3.10; standalone lint và SDC-load đã PASS. Log: `build/asic_precheck_ng8F7dzh`. Precheck không chạy synthesis, repair, timing analysis, routing hoặc simulation.

Lệnh chạy/collect dùng tag mới `picorv32_sobel_clk50_repair_02`, xem ASIC_RUN_GUIDE.md. Không cần chạy lại simulation vì RTL và firmware còn khớp bằng chứng chức năng.
