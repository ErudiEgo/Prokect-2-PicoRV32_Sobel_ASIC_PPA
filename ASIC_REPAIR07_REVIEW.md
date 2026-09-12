# RUN 7: còn hai lỗi antenna; tiếp tục bằng RUN 8

Archive: `reports/picorv32_sobel_clk50_repair_07_collect_20260912T085919720705Z.tar.gz`.
SHA256: `6bee660674f062458a6140ef3c4b8eb946f8d59a39203ad81fddbec8ac58d7c4`.

## Kết quả thực tế

Antenna theo vòng: 7/7 → 14/15 → 10/10 → 2/2 (net/pin). Hai vòng antenna-only đã chạy guard bảo toàn topology thành công. DRC và LVS PASS trên RUN 7; exit status vẫn 2.

| Net | Pin | Lớp | Partial side-area ratio | Giới hạn |
| --- | --- | --- | ---: | ---: |
| net902 | fanout901/A | met2 | 464.22 | 400 |
| net933 | fanout932/A | met3 | 583.40 | 400 |

Nguồn: `01-sobel-antennaclosure/round_03/01-check-antennas/reports/antenna.rpt` trong RUN 7. Hai pin này không nằm trong targets của ba lần chèn trước. Có diode trên net chưa đảm bảo mọi gate được bảo vệ ở mọi lớp; không bỏ checker theo số diode.

Điện cuối RUN: slew 12 (max_ss), capacitance 2 (max_ss và nom_ss), fanout 21. Hai driver `_07463_/Y` và `_07515_/Y` có capacitance 0.094709/0.093490 so với limit 0.086070 trong checks.rpt tại max_ss. Slew ở driver và các sink của chúng vượt giới hạn; nhiều lỗi fanout khác nằm trên clock buffer và input buffer. Setup/hold không có violation được báo, nhưng checks.rpt vẫn ghi hai endpoint ext_addr[0:1] unconstrained; chưa kết luận mọi đường đều được timing sign-off.

## Thay đổi RUN 8

Tiếp tục từ `01-sobel-antennaclosure/state_out.json` của RUN 7, trước filler/sign-off. Không lấy ODB cuối đã thêm filler, không làm lại các vòng sửa đã xong. Copy/hash tất cả view vào snapshot mới, gồm view kế thừa đã được kiểm tra từ snapshot RUN 7; CTS provenance được kế thừa có ghi nguồn.

`SOBEL_ANTENNA_ONLY=true` được ghi rõ trong config.frozen.json của continuation và provenance; raw config/RTL/firmware/SDC không đổi. Ba vòng tối đa đều chỉ chèn diode theo report, legalization, global/detailed route, guard topology, rồi kiểm tra antenna độc lập. Dừng sớm nếu 0/0. Không chạy resizer trong continuation này và không tắt/nới checker.

Mục tiêu lần này là khép lỗi antenna. Không hứa hết slew/cap/fanout: chúng vẫn được kiểm tra ở cuối và có thể khiến flow exit 2 ngay cả khi antenna đạt. Sửa điện sau đó cần cân nhắc tác động lại tới antenna.

## Kiểm tra trước khi giao lệnh

`build/resume08_frozen_check_JB02thlr/precheck.log` và `state_load.log`: OpenLane 2.3.10, Classic 81 bước, config/API/sequence/lint/SDC-load đạt. Chế độ antenna-only khớp provenance. ODB thật có 14989 instance/88930 terminal, resolve đúng hai target; guard và JSON round-trip đạt. Tất cả đường dẫn view sao chép tồn tại; snapshot hash đạt và từ chối ghi đè.

Trợ lý chỉ đọc ODB, kiểm tra cấu hình và biên dịch/lint; không chạy flow, không chèn diode hay reroute. RUN 8 chưa có kết quả thực tế.

Lệnh người dùng: `bash scripts/06_run_openlane.sh picorv32_sobel_clk50_repair_08 picorv32_sobel_clk50_repair_07`. Thu thập sau chạy: `bash scripts/07_collect_asic.sh picorv32_sobel_clk50_repair_08`. Các bước copy/cd xem ASIC_RUN_GUIDE.md.
