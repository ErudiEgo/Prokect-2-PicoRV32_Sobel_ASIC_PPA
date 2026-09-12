# Chẩn đoán repair_02 và cấu hình thử repair_03

Ngày 2026-09-12. Người dùng chạy OpenLane; trợ lý đọc archive/ODB đã có và chuẩn bị bản sửa. Chưa chạy simulation hay flow repair_03.

## Bằng chứng thực tế

RUN: `picorv32_sobel_clk50_repair_02`.
Archive gốc: `reports/picorv32_sobel_clk50_repair_02_collect_20260912T034459898962Z.tar.gz`.
SHA256: `4db4dfa916fcfd6506a61dd94fb6894ef248544339007390aba59dc5577fac9f`.
Giữ nguyên archive và RUN; bản trích đọc ở `build/repair02_review_5qkrpysx`.

| Tiêu chí | base_01 | repair_02 |
|---|---:|---:|
| Antenna sau detailed routing, net/pin | 14/15 | 7/7 |
| Slew violation, max_ss | 33 | 48 |
| Capacitance violation, max_ss | 8 | 5 |
| Fanout violation, max_ss | 61 | 338 |
| Magic/KLayout DRC, LVS, XOR | 0 | 0 |
| Standard-cell area, µm² | 122331 | 130911 |

**repair_02 chưa PASS.** Diode giảm antenna nhưng làm tăng số tải và diện tích. 338 dòng fanout gồm 18 dòng clock và 320 dòng khác; không được bỏ qua vì ảnh cuối chỉ trình bày Antenna/LVS/DRC. Slew đếm cả driver, pin nhận và pin diode nên số pin tăng không đồng nghĩa mức slew xấu nhất tăng.

Nguồn: `48-openroad-checkantennas-1/reports/antenna_summary.rpt`, `57-openroad-stapostpnr/max_ss_100C_1v60/checks.rpt`, `77-misc-reportmanufacturability/state_out.json`. Các metric timing trong state của bước antenna là dữ liệu kế thừa; dùng báo cáo STA cuối cho timing, không lấy số 0 cũ để kết luận.

## Bảy net còn antenna

Tên dưới đây đã bỏ escape của bus cho dễ đọc. Tỷ số là partial antenna ratio / required ratio trong checker sau DRT. Span được đọc từ pin coordinates của ODB stage 46, không phải wire length đã route.

| Net | Pin lỗi | Layer | Partial / required | Span µm | Diode trên net |
|---|---|---|---|---:|---:|
| `_04475_` | `_09548_/A2_N` | met3 | 1326.16 / 400 | 171.932 | 0 |
| `cpu.alu_out_q[2]` | `_07373_/A_N` | met1 | 719.64 / 400 | 132.018 | 0 |
| `cpu.is_alu_reg_imm` | `_10411_/B` | met1 | 626.11 / 400 | 161.634 | 0 |
| `cpu.decoded_imm_j[17]` | `_08581_/C` | met1 | 573.56 / 400 | 175.342 | 0 |
| `net923` | `fanout922/A` | met1 | 554.56 / 400 | 369.307 | 10 |
| `cpu.reg_pc[16]` | `_07476_/A` | met1 | 469.56 / 400 | 207.053 | 11 |
| `_00967_` | `_10521_/A1` | met1 | 454.81 / 400 | 97.667 | 0 |

Năm net không diode đều có span cuối dưới 200 µm. Điều này phù hợp với giới hạn của heuristic hiện tại; vị trí trước heuristic có thể khác vị trí cuối. Hai net đã có diode cho thấy số diode/heuristic không tự đảm bảo bảo vệ mọi đoạn dây sau detailed routing.

`43-openroad-repairantennas/1-diodeinsertion/diodeinsertion.log` ghi 37 → 5 → 1 vi phạm qua các lượt nội bộ; lần này chưa hội tụ về 0 trong 3 lượt. Checker độc lập ngay sau bước này vẫn báo 4 net/4 pin. Sau detailed routing là 7/7; hai kiểu checker không được đánh đồng.

## Vì sao điện vẫn lỗi

`40-openroad-repairdesignpostgrt` thực sự đã resize 5 instance, thêm 4 buffer trên 6 net. Tuy nhiên bước này đứng **trước** diode trên cổng, heuristic diode và antenna repair. Heuristic của OpenLane 2.3.10 chèn diode ở các terminal của net đủ dài, kể cả phía driver; số tải tăng rõ trong `checks.rpt`.

`44-openroad-resizertimingpostgrt` gọi `repair_timing` cho setup/hold; log báo không có setup/hold violation. Nó không thay cho một lần `repair_design` xử lý tải mới. STA sau đó ghi fanout 338; STA sau extraction ghi slew 48/cap 5. Năm driver cap lỗi: `_07515_/Y`, `_07448_/Y`, `_07463_/Y`, `_07390_/Y`, `_07397_/Y`; tải 0.090427–0.097028 pF vượt giới hạn library 0.086070 pF. Giới hạn library vẫn có hiệu lực dù design cap constraint là 0.2 pF.

## Bản thử repair_03

1. `HEURISTIC_ANTENNA_THRESHOLD`: 200 → **90 µm**, là ngưỡng PDK đã nạp và thấp hơn span của năm net chưa được bảo vệ. Có thể tăng số diode và tải, cần đánh giá trong RUN mới.
2. `GRT_ANTENNA_ITERS`: 3 → **6**, vì log repair_02 còn 1 lỗi ở lượt cuối. Giữ antenna margin 30%; không coi việc tăng số lượt là đủ để bảo đảm antenna sau DRT.
3. Thêm **RepairDesignPostGRT sau lần chèn/sửa diode đầu**, trước ResizerTimingPostGRT: xử lý cap/slew/fanout với tải diode đã hiện diện.
4. Thêm **RepairAntennas sau ResizerTimingPostGRT**, trước STA/DRT: kiểm tra và sửa antenna sau các thay đổi buffer/net của resizer.

Đây vẫn là Classic, dùng cơ chế `meta.substituting_steps` của OpenLane 2.3.10 với tiền tố `-` (chèn trước) và `+` (chèn sau). Không thay hoặc xóa bất kỳ bước cũ nào: **78 bước gốc + 2 bước thêm = 80 bước**. Các bước có điều kiện vẫn có thể skip theo cấu hình gốc, ví dụ EQY vốn chưa bật. Precheck so sánh toàn bộ thứ tự để bảo đảm không mất bước.

Chuỗi liên quan: RepairDesignPostGRT gốc → DiodesOnPorts → HeuristicDiodeInsertion → RepairAntennas gốc → **RepairDesignPostGRT thêm** → ResizerTimingPostGRT gốc → **RepairAntennas thêm** → STAMidPNR → DetailedRouting → checker antenna độc lập → các bước sign-off gốc.

Lưu ý launcher: trong phiên bản 2.3.10, truyền `--flow Classic` sẽ chọn lại lớp Classic gốc sau khi đọc meta, làm mất hai bước thêm. Vì vậy launcher lấy flow từ `config.frozen.json` có `meta.flow=Classic`; precheck dùng cùng `Classic.Substitute(...)`. Đây không phải đổi sang ORFS.

Giữ nguyên RTL/firmware/ENABLE_SOBEL, clock 50 ns, SDC, pin order, floorplan/density, CTS cluster 8, repair margins 40%, RSZ corners và mọi giới hạn checker. Không sửa chương trình CPU hoặc tính toán ảnh để giảm phần cứng. Hash chức năng vẫn khớp `soc_image_smoke_01`; 1295 pixel SW/HW được đối chiếu lại từ bằng chứng, không chạy lại simulation.

Rủi ro cần đọc ở RUN mới: lượt antenna cuối có thể thêm tải sau lần sửa điện; clock fanout có thể cần xử lý CTS riêng; topology/route mới có thể tạo net antenna khác. Không khẳng định repair_03 sẽ PASS trước khi có báo cáo. Chỉ chốt khi antenna sau DRT bằng 0, DRC/LVS/XOR sạch và các lỗi điện/timing/fanout được đánh giá đầy đủ. Power hiện là vectorless; IR chưa có vị trí nguồn package thực tế; phạm vi top không gồm external RAM/pad/package.

## Kiểm tra trước khi giao lệnh

Đã chạy precheck tĩnh ở `build/asic_precheck_rcL0fw8Q`: OpenLane 2.3.10, SKY130 revision `0fe599b2afb6708d281543108caf8310912f54af`, kiểm tra đủ 80 bước theo đúng thứ tự, standalone lint và nạp SDC thành công. Có 33 ngoại lệ lint style upstream đã ghi rõ từ trước; không thêm ngoại lệ mới. Không thực thi synthesis/placement/routing/simulation.

Kiểm tra đóng băng ở `build/packaging_only_putxxdxd`: hash và đường dẫn nguồn hợp lệ, thử ghi đè snapshot bị từ chối. Bản snapshot cũng qua config/lint/SDC-load độc lập, log ở `build/repair03_frozen_check_vNo0p2XT`; kiểm tra cú pháp toàn bộ shell/Python đạt. Hai thử mount scratch trước đó lỗi quyền/đường dẫn của Docker; đã dùng scratch đầy đủ có quyền đọc và kiểm tra thành công, không tác động RUN người dùng.

Lệnh RUN mới và collect: [ASIC_RUN_GUIDE.md](ASIC_RUN_GUIDE.md).

Tham khảo chính thức: [OpenLane custom flow configuration](https://openlane2.readthedocs.io/en/stable/usage/writing_custom_flows.html), [OpenROAD antenna repair](https://openroad.readthedocs.io/en/latest/main/src/grt/README.html). Hành vi cụ thể đã đối chiếu với source trong Docker 2.3.10 cài thực tế.
