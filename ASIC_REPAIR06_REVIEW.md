# RUN 6: antenna chưa hội tụ; bản sửa kiểm soát cho RUN 7

## Bằng chứng thực tế

Archive gốc: `reports/picorv32_sobel_clk50_repair_06_collect_20260912T055308225024Z.tar.gz`.
SHA256: `86e0459f925fbfa0d719ce7fcbb506b7bb93bf2f40c0749a06567e23f03f420f`.
RUN 6 chạy tiếp từ DRT của RUN 4, kết thúc exit 2. Không phải PASS.

| Kiểm tra antenna | Net lỗi | Pin lỗi |
| --- | ---: | ---: |
| Trước sửa | 7 | 7 |
| Sau vòng 1 | 14 | 15 |
| Sau vòng 2 | 7 | 8 |
| Sau vòng 3 / cuối RUN | 12 | 12 |

Nguồn: `runs/picorv32_sobel_clk50_repair_06/01-sobel-antennaclosure/closure_history.json` và report từng round.
Các log `02-targeted-diodes/sobel-targeteddiodes.log` xác nhận đã chèn 7, 15 và 8 diode, không còn crash API của RUN 4/5.
Các log `04-repair-electrical-ss/openroad-repairdesignpostgrt.log` ghi lần lượt 16/3/3 buffer mới và 13/2/1 cell được resize.
Bộ pin lỗi thay đổi qua các vòng; không mô tả kết quả này là giảm lỗi liên tục.

Final state `32-misc-reportmanufacturability/state_out.json`: DRC Magic/KLayout, LVS, XOR, setup/hold sạch; slew 12, cap 3 tại max_ss_100C_1v60, fanout 17. Antenna 12 net/12 pin.
Area standard cell 123168 um², utilization 0.403097; power vectorless khoảng 6.608 mW. Chưa sign-off; không kết luận tiết kiệm điện hoặc tăng tốc.

## Chẩn đoán và thay đổi có kiểm soát

Sau mỗi lần chèn diode, cách cũ chạy cả resizer và reroute toàn thiết kế. Log chứng minh buffer/cell tiếp tục thay đổi; đây là nguồn gây xáo trộn topology trong vòng sửa antenna. Chưa chứng minh toàn bộ 12 lỗi đều do resizer: đường đi dây và vị trí diode cũng ảnh hưởng antenna theo từng lớp.

RUN 7 giữ nguyên vòng đầu để so sánh với RUN 6. Hai vòng sau thay RepairDesign/RepairTiming bằng OpenROAD.GlobalRouting rồi DetailedRouting; vẫn legalization, vẫn đọc report độc lập sau DRT. Không tăng số vòng hay số diode mỗi pin, không nới giới hạn và không sửa RTL/firmware/config/SDC.

Thêm `topology_after_diodes.json` và `Sobel.VerifyAntennaTopology` sau reroute ở hai vòng cuối: so sánh chính xác tên instance, master và kết nối, gồm chân tín hiệu diode. Power pins của diode mới được standard global-connect nối sau insertion. Guard không tự sửa hoặc che metric; nếu topology đổi thì dừng để chẩn đoán. LVS gốc vẫn chạy.

Global/detailed routing vẫn có thể đổi đường dây. Đây chưa phải ECO routing chỉ giới hạn vài net; không hứa chắc RUN 7 sẽ PASS. Slew/cap/fanout phải tiếp tục kiểm tra từ kết quả cuối, vì ngừng resize trong hai vòng cuối có thể giữ lại lỗi điện.

Tài liệu tham chiếu: [OpenROAD Global Routing](https://openroad.readthedocs.io/en/latest/main/src/grt/README.html), [Gate Resizer](https://openroad.readthedocs.io/en/latest/main/src/rsz/README.html). Quyết định dựa thêm trên script và log của phiên bản cài thực tế.

## Chuẩn bị và lệnh người dùng

Chạy từ checkpoint RUN 4 để có cùng điểm xuất phát với RUN 6; không ghi đè RUN 4/6. Tên mới: `picorv32_sobel_clk50_repair_07`.
Lệnh đầy đủ trong ASIC_RUN_GUIDE.md. Precheck kiểm tra config, API, nguồn chức năng, lint, SDC và đọc ODB; không phải chạy antenna/DRC/LVS thực tế. Kết quả RUN 7 chưa có.

## Kiểm tra đã hoàn tất trước khi giao RUN 7

- Python AST và bash -n đạt; hash RTL/TB/firmware/vendor và pixel test cũ vẫn khớp, không chạy lại simulation.
- Frozen precheck: `build/resume07_frozen_check_nVPcOERD/precheck.log`. OpenLane 2.3.10, cấu hình Classic 81 bước, 4 kiểm tra API/sequence, lint và SDC-load đạt.
- Đọc ODB thật: 14941 instance/88674 terminal, 7 target; JSON round-trip và guard master/net sai được kiểm tra. CLI guard trên reference thật đạt. `state_load.log` xác nhận mọi view của checkpoint tồn tại. Không Step.start/Flow.start, không chèn diode/reroute trong các kiểm tra này.
- Audit chỉ đọc hai ODB của vòng đầu RUN 6: 16 instance mới, 162 chân tín hiệu đổi net, trong đó 20 chân DIODE; chỉ 2 master khác ở hai snapshot cuối (khác với 13 lượt resize được log trong quá trình). Dữ liệu tại `build/repair06_topology_nscJ6bqb/`. Bảy diode mới vẫn cùng net với gate tương ứng sau vòng đầu: chưa có bằng chứng rằng resizer tách chính bảy cặp này. Thay đổi vòng sửa nhằm giảm xáo trộn toàn mạch, không khẳng định đã tìm nguyên nhân duy nhất.
- RUN 7 chưa chạy; antenna/slew/cap/fanout cuối vẫn chờ người dùng chạy và thu thập.
