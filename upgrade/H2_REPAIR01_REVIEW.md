**Bước chạy tiếp theo: [H2_ECO_RUN_GUIDE.md](H2_ECO_RUN_GUIDE.md). Đã đạt preflight tĩnh; physical ECO chưa chạy. Tiếp tục H2 bằng 4 buffer có mục tiêu từ checkpoint repair01, dùng scripts 34/35/36 và RUN mới `s2_ppa_h2_eco_clk50_01`.**

# H2 repair_01 — đánh giá sau chạy, 2026-09-22

**Tên đúng: H2 physical repair_01, không phải H3. Trạng thái FAIL_OR_INCOMPLETE.**

RUN `s2_ppa_h2_clk50_repair_01`, pair `s2_ppa_pair_clk50_repair_01`. Source hashes của packet gốc đã đối chiếu với packet H2 người dùng thực sự chạy, không dùng đường dẫn provenance của bản chuẩn bị trên Windows làm đối chứng. READY/source integrity khớp; config chỉ đổi GRT_ANTENNA_MARGIN30→10 và SOBEL_POST_FANOUT_MARGIN_PCT70→80. Toàn bộ file có trong source manifest cha ngoài hai config giữ hash. Không có RTL H3 mới.

Archive: `reports/s2_ppa_h2_clk50_repair_01_collect_20260922T120915755007Z.tar.gz`.
SHA256: `2c328fb0f50f26a3d224a8a1922e44f3d050af9b5d2501256b12aa5e05812779`.

## Kết quả so với H2 trước repair

| Đại lượng | H2 baseline RUN01 | H2 repair_01 |
|---|---:|---:|
| Fanout violations (mỗi corner) | 6 | 1 |
| Cap violations (worst corner) | 1 | 2 |
| Slew violations (worst corner) | 0 | 4 |
| Corner lỗi cap/slew | max SS | nom/min/max SS |
| Standard-cell area µm² | 341300 | 352413 |
| Standard-cell count | 45891 | 47424 |
| Core/die area µm² | 730358 / 759937 | 730358 / 759937 |
| Setup worst slack ns | +18,641807 | +14,326759 |
| Hold worst slack ns | +0,158425 | +0,105061 |
| Process exit | 2 | 2 |

Area tăng thêm3,26%; timing slack giảm nhưng setup/hold vẫn đạt. DRC Magic/KLayout, LVS, XOR, route DRC và antenna0/0 đạt. LVS36685devices/35804nets ở mỗi phía. H2 repair chưa có final export; stage views/báo cáo vẫn là bằng chứng thực. Host elapsed2569,565s≈42phút50giây; không phải latency chip. Power vẫn vectorless, IR thiếu nguồn/pads/package thực, EQY và wirelength-threshold check vẫn chưa thực hiện.

**Kết luận thử nghiệm:** kết quả fanout tốt hơn nhưng closure chưa đạt; cap/slew và area xấu hơn. Không chấp nhận cấu hình này như bản sửa thành công. Vì đổi2tham số cùng lúc, không quy riêng lợi/hại cho một knob. Không tăng margin tiếp hoặc chạy H1 cùng repair profile chỉ để hoàn tất một cặp chưa đạt.

## Driver và topology đã kiểm tra

Đọc ODB các stage43/45/47/57, không ghi/sửa DB hoặc chạy physical algorithm:

1. `_37271_/Q`, `sky130_fd_sc_hd__dfxtp_4`, net `soc.g_sobel.g_v2.tile_engine.origin[15]`: trước closure có2loads, không diode; sau closure có13loads gồm11diode. Giới hạn10, fanout13. Lỗi remaining fanout gắn với diode thêm trong closure.
2. `_28558_/Y`, `sky130_fd_sc_hd__nor4_1`, net `_10606_`: một tải logic, không diode. Ở max_ss cap0,030333pF > limit0,020152pF; slew2,101641ns >1,492081ns. `wire49/A` cùng đường tín hiệu cũng vi phạm slew.
3. `_28646_/Y`, `sky130_fd_sc_hd__nor4_2`, net `_10692_`: một tải logic, không diode. Ở max_ss cap0,053096pF >limit0,036631pF; slew2,021104ns >1,489198ns. `_28649_/C` cùng đường tín hiệu cũng vi phạm slew.

Bốn pin slew không phải bốn net độc lập: chúng nằm trên hai kết nối driver→load. Không dùng giới hạn global0,2pF để bỏ qua giới hạn pin Liberty.

Stage37 và stage46 STA báo slew/cap/fanout0. Stage59 STA sau extraction báo4/2/1. Native antenna rounds109→3→0net. Timeline cho thấy các vấn đề cần được kiểm tra với routing/parasitics cuối và diode closure, không chỉ metric trước DRT. Chưa có phân rã RC đủ để khẳng định wire detour/cell placement là nguyên nhân duy nhất của hai net cap.

## Bước tiếp theo có căn cứ

- Giữ H1 baseline, H2 baseline và H2 repair như ba kết quả riêng; không gọi H3 hoặc di chuyển tag H2.
- Không phát lệnh rerun mù. Hướng kế tiếp là chẩn đoán RC/độ dài/vị trí hai net NOR và khả năng buffer/resize/placement có kiểm soát; riêng origin[15] phải xem cách giảm/chia tải diode vẫn bảo toàn antenna.
- Trước ECO: xác minh master/pin/net và checkpoint, preservation của logic connectivity/nguồn/corner; không xóa diode tùy ý hoặc chỉ nới fanout. Buffer/resize có thể tạo lỗi antenna/hold khác, cần đo lại đủ checks sau routing.
- Nếu muốn phân lập tác dụng knob, có thể thiết kế ablation từng tham số; không dùng kết quả hai-knob này làm bằng chứng nhân quả. Việc chọn ablation hay targeted ECO là quyết định tiếp theo, chưa có script physical repair_02 được chuẩn bị/kiểm thử.
- Chưa nên chạy H1 với profile repair chưa đạt. H3 spec/review/RTL vẫn chưa mở.

Evidence: `build/h2_repair01_review_02/audit.json`, `collector_metrics.json`, `h2_net_topology.json`, `odb_inspection.log`, raw archive extracts. Không chạy simulation/OpenLane flow trong lượt review; archive gốc giữ nguyên.
