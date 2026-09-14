# Đánh giá RUN15 so với RUN12 — 2026-09-14

## Kết luận

RUN12 `picorv32_sobel_dma_clk50_baseline_02` vẫn là mốc ổn định để bảo toàn:
exit0, Antenna/LVS/DRC/setup/hold/slew/cap đạt, còn62fanout. Chưa gọi full signoff.
RUN15 `picorv32_sobel_dma_clk50_baseline_05` cải thiện fanout nhưng chưa đạt tổng thể:
exit2 do slew/cap; không thay RUN12 làm baseline báo cáo cuối.
RUN13/14 dừng vì lỗi tích hợp wrapper trước CTS; RUN15 đã đi hết81bước và phát hiện
vi phạm điện thật sau extraction. Hai loại lỗi này khác nhau.

| Chỉ tiêu | RUN12 | RUN15 |
|---|---:|---:|
| OpenLane exit |0|2|
| Antenna / LVS / DRC |PASS|PASS|
| Setup / hold |PASS|PASS|
| Max fanout violation count |62|4|
| Max slew violation count |0|20|
| Max capacitance violation count |0|8|
| design__instance__area (µm²) |172005|193493|
| design__instance__count |21806|26662|
| clock_buffer instance count |516|752|

Slew/cap trong bảng là metric tổng của công cụ (corner xấu nhất ở đây max_ss_100C_1v60),
không cộng các corner. Fanout4 ở cả9corner. Diện tích instance tăng khoảng12,49%; đây
không phải die/core area, không phải số transistor từ LVS. Không đánh giá PPA tốt hơn
chỉ dựa vào fanout giảm. Số liệu lấy từ final metrics RUN12 và state79 RUN15.

## Net gây lỗi đã xác định

**Clock:** bốn driver `clkbuf_2_0_0_clk/X` đến `clkbuf_2_3_0_clk/X` đều dùng clkbuf_8,
fanout16>10. Chúng trực tiếp lái các buffer tầng6; hiện diện ngay trong ODB CTS34 và
không đổi tới cuối. Đây là toàn bộ4fanout còn lại; không phải net tín hiệu Sobel.
Cả4 cùng lỗi capacitance ở maxSS: 0,205329–0,243279pF, giới hạn0,2pF.
Clock root `clkbuf_0_clk/X` còn lỗi cap0,223298pF>0,2pF; ODB cuối có4clock sinks+4diode.
Mục tiêu CTSfanout6 đã tác động nhưng chưa buộc mọi nhánh clock đạt giới hạn10.

**Tín hiệu:** 20 dòng slew tại maxSS nằm trên3net, không phải20net độc lập:

| Driver / net | Cell | Tải cuối / diode | Slew lớn nhất (ns) | Cap (pF) / giới hạn Liberty |
|---|---|---:|---:|---|
|fanout4485/X / net4662|buf_1|4 / 1|1,644827|0,089498 / 0,081492|
|fanout4549/X / net4726|buf_1|9 / 5|1,585516|0,085985 / 0,081492|
|_12538_/Y / _07482_|a311oi_4|4 / 2|1,523103|0,083841 / 0,079661|

Slew nominal target1,5ns; riêng limit driver _12538_/Y ghi1,495742ns trongchecks.rpt.
ODB stage43 cho ba net lần lượt3/4/2tải, chưa có diode; stage47 có thêm1/5/2diode.
Các metric điện trung gian trước STA59 có thể kế thừa từ bước trước; không dùng
chúng để khẳng định extracted RC đã PASS. Báo cáoSTA59 xác nhận lỗi điện cuối.
Chèn nhiều buffer để giảm fanout làm thay đổi placement/routing; thêmdiode làm tăng tải.
Dữ liệu cho thấy hướng sửa điện còn thiếu, không chứng minh chức năng ảnh bị đổi.

## Warnings và kế hoạch tiếp theo

Warnings như LEF58_ENCLOSURE không được hỗ trợ, VSRC_LOC_FILES thiếu và checker wirelength
chưa cóthreshold là thông báo về giới hạn công cụ/điều kiện kiểm tra. Chúng không đồng
nghĩa với error slew/cap; không được xóa bằng cách che log, tắt checker hay nới constraint.
Warning2outputpins cần ghi rõ và đối chiếu với cổng địa chỉ nối hằng nếu dùng trong báo cáo.

1. Giữ RUN12 và backup làm mốc; giữ RUN15 làm bằng chứng thử nghiệm fanout.
2. Hướng sửa tiếp theo phải xử lý4nhánh clock fanout16 cùng5clock cap trước, đồng thời
   bảo đảm3net tín hiệu có đủ sức lái saudiode/routing. Không tiếp tục siết fanout toàn
   thiết kế chỉ để giảm bộ đếm mà chưa đánh giá diện tích và lỗi điện.
3. Chỉ chấp nhận bản mới khi fanout/slew/cap đạt và vẫn giữAntenna/LVS/DRC/setup/hold.
   Sauđó mới so sánhPPA. RUN mới nếu chuẩn bị vẫn chạy từđầu theo thỏa thuận.

Phiên đánh giá này chỉ đọc báo cáo/ODB và cập nhật hồ sơ; không đổi cấu hình, RTL,
firmware, constraints, không khởi độngsimulation/OpenLane và chưa phát lệnhRUN16.
Launcher08 hiện trỏtagRUN15 đã tồn tại; không dùng lại tag này.

## Bằng chứng

- Archive: `reports/picorv32_sobel_dma_clk50_baseline_05_collect_20260914T032020831629Z.tar.gz`.
- STA: `runs/picorv32_sobel_dma_clk50_baseline_05/59-openroad-stapostpnr/max_ss_100C_1v60/checks.rpt` tạiUbuntu.
- Metrics: `runs/picorv32_sobel_dma_clk50_baseline_05/79-misc-reportmanufacturability/state_out.json`.
- Chẩn đoán ODB chỉđọc: `build/run15_failure_nets.json` ởWindows, chứa tải/diode của8driver
  quaCTS34, repair43, DRT47, antenna48 vàstate79. Không cówrite_db hoặc sửaODB.
