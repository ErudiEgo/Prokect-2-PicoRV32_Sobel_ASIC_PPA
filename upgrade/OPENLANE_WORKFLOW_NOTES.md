# Cách hỗ trợ OpenLane đã thống nhất

Ngày ghi nhận: 2026-09-11.

Nguồn: cuộc trò chuyện “Chuẩn bị quy trình OpenLane PPA”, đã đọc phần hội thoại hiển thị qua trình duyệt:
https://chatgpt.com/s/cx_6aa3c844dd548191bf411d282f027582

Người dùng yêu cầu học cách hỗ trợ OpenLane trong nguồn này. Những câu hỏi ôn thi, bài Full Adder, bộ nhân và UART–FIFO là ngữ cảnh tham khảo, không phải yêu cầu thực hiện trong dự án xử lý ảnh. Không coi các lời khẳng định kiểm chứng của trợ lý trong nguồn là kết quả do trợ lý hiện tại đã tự xác minh.

## Phân công và cấu trúc

- Trợ lý chuẩn bị, kiểm tra và sửa RTL, testbench, cấu hình, constraints, pin order và script; phân tích kết quả thực tế.
- Người dùng trực tiếp chạy simulation và flow OpenLane trên Ubuntu để quan sát và chụp ảnh. Không tự khởi động simulation hoặc flow nặng.
- Có thể kiểm tra tĩnh, lint, biên dịch và nạp cấu hình trong môi trường hiện có, nhưng phải nói đúng bước nào đã kiểm tra; không gọi compile/config-load PASS là simulation hoặc sign-off PASS.
- Bắt đầu với cấu trúc gọn: rtl/, tb/, config.json, constraints.sdc, pin_order.cfg và hướng dẫn. Giữ scripts/ phục vụ thao tác lặp lại; người dùng đã yêu cầu khôi phục scripts sau khi thử bỏ chúng. CPU có thể cần firmware/ và nguồn thư viện riêng.
- Không tạo hàng loạt thư mục và lớp công cụ không phục vụ công việc thực tế. Các thư mục kết quả/bằng chứng được tạo khi cần.

## Cách đưa lệnh cho người dùng

- Ghi rõ lệnh nhập trong Ubuntu hay Tcl Console của OpenROAD.
- Tách lệnh thành từng bước có điều kiện tiếp tục: copy → cd → precheck → RTL test → chạy flow → collect → xem SUMMARY → export.
- Ưu tiên RUN_TAG tường minh, dễ đọc như design_clk20_base_01; các lệnh phía sau ghi đúng cùng tag. Không phụ thuộc biến terminal từ một phiên cũ hoặc giấu toàn bộ trong một chuỗi lệnh dài.
- Script chạy phải tự kiểm tra đầu vào và dừng nếu precheck/test bắt buộc chưa đạt.
- Chạy trong terminal tương tác có TTY khi có terminal để giữ màu và thanh tiến trình. Không dùng cách pipe output làm mất giao diện người dùng cần chụp. Giữ log và exit status chính xác.
- Mẫu nguồn dùng Docker OpenLane 2.3.10, Classic, sky130A/sky130_fd_sc_hd với thanh 78 bước. Đây là môi trường của mẫu, không phải thông số bắt buộc cho mọi thiết kế. Xác minh phiên bản, flow, PDK và library thực tế trước khi phát lệnh.
- OpenROAD Flow Scripts (ORFS) và OpenLane Classic là hai flow khác nhau. Không trộn config.mk/lệnh ORFS với config.json/script OpenLane; khi chuẩn bị dự án mới phải nói rõ flow đang dùng.

## Bảo toàn RUN và kiểm chứng

- Windows giữ mã nguồn chính; Ubuntu giữ bản chạy và kết quả.
- Copy không xóa runs, báo cáo hoặc snapshot cũ. RUN mới phải có tên mới và từ chối ghi đè.
- Đóng băng RTL, firmware nếu có, constraints, config và phiên bản công cụ/PDK của mỗi RUN; dùng hash để liên kết bằng chứng test với đầu vào.
- RTL hoặc đầu vào chức năng thay đổi thì phải kiểm chứng lại. Chỉ thay cấu hình vật lý thì có thể dùng lại bằng chứng test còn khớp.
- Khi lỗi: nêu stage và nguyên nhân có bằng chứng, sửa nhóm tham số cần thiết, phát lệnh RUN mới, kiểm tra cả lỗi cũ lẫn tác dụng phụ trong kết quả mới.
- Phân biệt cảnh báo hoặc bước được skip với nguyên nhân thật khiến flow dừng.
- Không tăng density máy móc: đọc mức sử dụng, padding, core area và congestion. Không sao chép cách sửa heuristic diode/fanout của một thiết kế sang thiết kế khác khi chưa có bằng chứng.
- Không tắt checker chỉ để có PASS. Ngoại lệ giữ nguyên RTL đề thi và cho phép cảnh báo lint trong nguồn chỉ thuộc bài thi đó, không là mặc định của dự án mới.
- Mạch CPU/Sobel là mạch tuần tự: phải có clock thật và CTS phù hợp; không kế thừa clock ảo hoặc tắt CTS của Full Adder tổ hợp.

## Kết quả và cách trình bày

- Xuất PPA, IR drop và congestion; nêu đúng RUN, stage, corner, đơn vị và đường dẫn nguồn.
- Có bảng STA SUMMARY theo corner và bản summary dễ xem/chụp ảnh; có lệnh export báo cáo/GDS về Windows.
- Đọc setup/hold slack, WNS/TNS, vi phạm; phân biệt WNS theo nhãn công cụ với worst slack. Không suy ra Fmax chỉ từ một số slack.
- Báo standard-cell area/count, core/die area và utilization; phân biệt core utilization với placement density, giá trị đặt với giá trị đo.
- Báo internal/switching/leakage/total power khi có. Ghi vectorless nếu chưa dùng hoạt động chuyển mạch được ánh xạ hợp lệ.
- IR drop phải ghi VPWR drop, VGND rise, đơn vị, corner, điện áp và giả định nguồn/tải. Thiếu vị trí nguồn thực tế hoặc dùng tải vectorless thì nêu giới hạn; không gọi là sign-off nguồn thực tế.
- Báo congestion theo số liệu có sẵn, tách usage và overflow.
- Kiểm tra antenna nets/pins, DRC, LVS, XOR, fanout, slew, capacitance và checker liên quan. Mục tiêu antenna 0 nets/0 pins; không bỏ sót lỗi điện khi màn hình báo DRC/LVS sạch.
- Flow complete hoặc 78/78 không tự chứng minh mọi tiêu chí PASS. Phân biệt chức năng, timing, hoàn tất flow và sign-off theo bộ kiểm tra đã thực hiện.
- Checker không chạy/thiếu số liệu không được ghi PASS hoặc 0. Phân biệt MISSING, chưa trích xuất, không áp dụng và FAIL/INCOMPLETE.
- Khi flow lỗi sau khi có RUN, vẫn thu thập bằng chứng. Khi dừng ở precheck, không đòi báo cáo của RUN chưa được tạo.
- Không chạy lại flow chỉ để mở SUMMARY, lấy ảnh hoặc xem layout. Mở ODB của đúng RUN đã có; timing/IR GUI có thể cần nạp thêm library/constraints tương ứng.
- Dừng tối ưu khi đạt mục tiêu đã thống nhất. Nếu người dùng chấp nhận kết quả còn giới hạn thì giữ và ghi đúng giới hạn, không đổi nhãn thành sign-off đầy đủ.

## Trạng thái dự án mới

- Người dùng đã cung cấp workspace E:\aa. PPA_Project_List\aaa.PicoRV32_Sobel_ASIC_PPA ngày 2026-09-11. Đã có sobel_core, sobel_mmio, top picorv32_sobel_soc, hai firmware RV32I, testbench CPU, checker pixel/tile và replay. Người dùng đã chạy simulation `soc_image_smoke_01`, kết quả chức năng đúng cho ảnh 37 × 35; đã có ASIC base_01 chưa đạt đủ checker. SW 573.713 chu kỳ, HW 774.758 chu kỳ. Giữ RUN này làm baseline; không gọi là đã tăng tốc.
- Hướng đang phát triển: PicoRV32 điều khiển bộ tăng tốc Sobel, xử lý ảnh theo vùng; hiển thị tiến độ từ dữ liệu và mốc chu kỳ thực tế.
- Người dùng đã chốt SKY130 ngày 2026-09-11 vì các bài thực hành trước đều dùng nền tảng này. Dùng sky130A / sky130_fd_sc_hd với OpenLane Classic; không triển khai GF180MCU trong phạm vi hiện tại.
- Đã có kết quả vật lý base_01 nhưng chưa sign-off: DRC/LVS/XOR 0; antenna sau DRT 14 net/15 pin; corner max_ss có slew 33/cap 8; fanout 61 (41 clkbuf_leaf). Archive gốc giữ nguyên. Xem ASIC_BASE01_REVIEW.md.
- Bảng so sánh SKY130 và GF180MCU đã hoàn thành trước khi người dùng chốt SKY130; giữ PDK_COMPARISON.md làm tài liệu tham khảo lịch sử lựa chọn.
- Đã biên dịch core, MMIO và hai cấu hình testbench tích hợp bằng Icarus 12.0 trong Ubuntu-24.04; hai firmware compile bằng GCC 13.2.0 RV32I/ILP32. Người dùng đã chạy mô phỏng; trợ lý đã audit ZIP, xác nhận 35 hash snapshot và 1.295 pixel/4 tile ở mỗi bản, nguồn RTL/TB/firmware/vendor hiện hành khớp RUN. Mỗi cấu hình CPU có hai cảnh báo sensitivity của mảng cpuregs từ Icarus; không phải kết luận lint OpenLane.
- Kiến trúc hiện tại đưa program/image RAM và host logger ra testbench, ngoài physical top. Top tổng hợp gồm CPU/register file, bus decode/interface và Sobel/registers khi bật. Phải ghi phạm vi này khi báo PPA; xem ARCHITECTURE.md.
- Môi trường xác minh ngày 2026-09-12: Docker daemon hoạt động, OpenLane 2.3.10 image ID 37c3bd4ea0534a276cb2deb88d601044857bad2807b9bc5b36efe9d02c62624e; Classic có 78 bước. SKY130 Volare revision 0fe599b2afb6708d281543108caf8310912f54af. Compiler cục bộ trong build/toolchain, không cài toàn hệ thống.
- Đã chuẩn bị config.json, constraints.sdc, pin_order.cfg và scripts/05_asic_precheck.sh, 06_run_openlane.sh, 07_collect_asic.sh. Cấu hình ban đầu CPU+Sobel clock 50 ns, core utilization đặt 35%, placement density 50%; I/O assumptions ghi trong ASIC_RUN_GUIDE.md. Config load, standalone lint và SDC load với khai báo cổng đã kiểm tra khi chuẩn bị; sau đó người dùng đã chạy base_01. Bản sửa mới vẫn chờ người dùng chạy.
- Nguồn CPU gốc và RTL chức năng không đổi. Bản physical tự sinh bỏ timescale và thêm 33 chú thích style lint ở đúng dòng upstream đã rà soát; danh sách/lý do/hash được lưu. Đây không phải upstream warning-free; giữ các checker và báo ngoại lệ rõ ràng. Không sửa blocking assignment upstream thành nonblocking chỉ để hết warning.
- Bản sửa repair_02: heuristic diode cho net dài ngưỡng 200 µm, antenna margin 30%, CTS cluster 8, repair slew/cap margin 40%, RSZ max_ss/min_ff/nom_tt. Giữ clock 50 ns, giới hạn điện, density/utilization và checker. Đã config-load/lint/SDC-load PASS trước khi giao người dùng. Người dùng sau đó đã chạy repair_02; kết quả xem cập nhật bên dưới.
- Collector đã sửa lỗi trộn giá trị timing cũ kế thừa trong antenna state với PASS/FAIL post-PNR. Regression dùng archive thật xác nhận slew 33, cap 8, fanout 61 và antenna 14/15. Không ghi đè báo cáo cũ. GDS từng stage được xuất ngay cả khi deferred errors chặn final, nhãn chưa sign-off rõ ràng.

## Cập nhật repair_03 — 2026-09-12

- Đã đọc actual repair_02: antenna 7/7; max_ss slew 48/cap 5/fanout 338; DRC/LVS/XOR 0. Không PASS. Xem ASIC_REPAIR02_REVIEW.md.
- Bản chuẩn bị tiếp theo `picorv32_sobel_clk50_repair_03`: Classic giữ 78 bước và thêm 2 bước qua meta, tổng 80. Heuristic threshold 90 µm, antenna iterations 6; thêm sửa điện sau diode và antenna sau timing repair. Không đổi RTL/firmware/SDC/checker limits.
- Launcher phải đọc flow từ frozen meta; không truyền --flow Classic vì OpenLane 2.3.10 sẽ bỏ các step additions. Precheck xác minh toàn bộ thứ tự 80 bước.
- Đã precheck cấu hình/lint/SDC và hash chức năng; người dùng thực thi flow. repair_03 sau đó đã có kết quả, xem cập nhật mới bên dưới. Giữ các kết quả cũ và đánh giá cả tải diode/clock fanout sau RUN mới.

## Cập nhật repair_04 — 2026-09-12

- Actual repair_03: antenna 6 net/7 pin; slew 668, cap 67, fanout 60; DRC/LVS/XOR 0. Số diode 9932, area 153139 µm². Chưa PASS; không mô tả giảm lỗi toàn diện.
- repair_04 bỏ heuristic insertion theo chiều dài (không phải checker), giữ router repair và diode input, thêm Sobel.AntennaClosure sau DRT. Classic 81 bước chính, vòng sửa tối đa 3 lần theo unique pin trong report thật, kiểm tra lại sau mỗi reroute. Điện sửa ở SS, timing/all-corner sign-off giữ nguyên.
- Nguồn custom step nằm trong scripts và được freeze; CLI wrapper chỉ đăng ký step rồi gọi OpenLane gốc. Không sửa package/RTL/firmware/SDC hoặc nới checker.
- Precheck/plan-only chỉ đọc và cấu hình. Trợ lý không chạy chèn diode, PNR hay simulation. Người dùng chạy tag picorv32_sobel_clk50_repair_04, collect cả khi lỗi.
- Mọi vòng giữ targets.json/closure_history.json và report/state/log. Mục tiêu phải xác nhận từ checker sau DRT, không từ counter nội bộ router hoặc 81/81. Xem ASIC_REPAIR03_REVIEW.md.

## Cập nhật repair_05 — lỗi API và chạy tiếp checkpoint

- repair_04 dừng sau DRT và checker antenna đầu tiên (7/7), trước chèn diode: AttributeError self.info. Sửa dùng openlane.logging.info ở cả hai nhánh; không đổi config/RTL/firmware/SDC.
- Thêm 3 kiểm tra API vào precheck; không chạy Step.start. Lệnh tiếp tục: bash scripts/06_run_openlane.sh picorv32_sobel_clk50_repair_05 picorv32_sobel_clk50_repair_04.
- Snapshot mới copy/hash toàn bộ view checkpoint, kiểm tra config/nguồn/image/PDK khớp, CLI --from Sobel.AntennaClosure --with-initial-state. Không sửa RUN 4, không chạy synthesis/placement/DRT đầu lại.
- Collector ghi provenance CTS/congestion kế thừa, ưu tiên log reroute mới; runtime chỉ phần tiếp tục. Không gán PASS LVS/DRC của RUN trước cho RUN 4 chưa tới các checker này. Xem ASIC_REPAIR04_REVIEW.md.

## Cập nhật repair_06 — sửa API ODB và preflight kết nối

- RUN 5 dừng trước chèn diode: dbNet.getId không tồn tại. Thay bằng tên net nguyên bản; capture/verify toàn bộ kết nối trước --plan-only và sau chèn.
- Frozen resume precheck resolve target và đọc toàn bộ ODB: 14941 instance/88674 terminal, thử guard master/net sai bằng dữ liệu Python (không đổi ODB), config/lint/SDC/State.loads đạt. Không thực thi physical steps.
- Collector bổ sung child state khi composite chưa ghi state_out, giữ trạng thái FAIL_OR_INCOMPLETE và thiếu final metrics; archive RUN 5 xác nhận antenna 7/7.
- Lệnh mới: bash scripts/06_run_openlane.sh picorv32_sobel_clk50_repair_06 picorv32_sobel_clk50_repair_04. Giữ RUN 4/5; không đổi config/RTL/firmware/checker.

## Cập nhật repair_07 — vòng antenna giữ topology

- RUN 6 hoàn tất exit 2, antenna 7 → 15 → 8 → 12 pin; DRC/LVS/XOR/setup/hold sạch, slew 12/cap 3/fanout 17. Xem ASIC_REPAIR06_REVIEW.md.
- RUN 7 cùng checkpoint RUN 4, chỉ resizer trong vòng đầu; hai vòng sau GlobalRouting/DRT và guard toàn bộ instance/master/kết nối, gồm diode tín hiệu. Giữ tối đa 3 vòng và mọi checker. Không hứa PASS khi chưa có report.
- Lệnh: bash scripts/06_run_openlane.sh picorv32_sobel_clk50_repair_07 picorv32_sobel_clk50_repair_04.
- Trợ lý chỉ kiểm tra tĩnh/config/lint/SDC và đọc ODB; người dùng chạy flow. RUN/evidence cũ giữ nguyên.

## Cập nhật repair_08 — tiếp tục từ checkpoint RUN 7

- RUN 7 antenna giảm còn 2/2: fanout901/A trên net902/met2 và fanout932/A trên net933/met3. DRC/LVS PASS, còn slew 12/cap 2/fanout 21. Xem ASIC_REPAIR07_REVIEW.md.
- Resume hỗ trợ completed Sobel.AntennaClosure trước filler; copy/hash view kế thừa từ snapshot parent đã xác minh. Giữ CTS provenance và tránh lặp lại các vòng đã chạy.
- Continuation ghi SOBEL_ANTENNA_ONLY=true vào frozen config/provenance; mọi vòng bỏ resizer, vẫn guard topology và toàn bộ checker. Không hứa hết lỗi điện khi antenna hết lỗi.
- Lệnh: bash scripts/06_run_openlane.sh picorv32_sobel_clk50_repair_08 picorv32_sobel_clk50_repair_07. Frozen precheck đạt; người dùng thực thi flow.

## Cập nhật repair_09 — native repair trên detailed wires

- RUN 8: 2/2 → 5/5 → 4/4 → 4/5 antenna; LVS/DRC PASS, slew 12/6 theo max_ss/nom_ss, cap 2, fanout 25. Không hội tụ dù guard logic đạt.
- Phát hiện phạm vi thay đổi quá lớn: targeted_diodes xóa toàn bộ dbWire rồi full GRT/DRT. Continuation mới dùng native repair_antennas của đúng OpenROAD edf00dff, cập nhật incremental routing từ detailed wires, không xóa toàn bộ wire trước sửa.
- RUN 9 từ checkpoint RUN 7 (2/2); native một iteration mỗi lần, margin 30, tối đa 3 vòng; guard cho phép chỉ PDK diode mới có kết nối và giữ logic cũ. Vẫn DRT và checker độc lập sau sửa.
- Config/API/native read preflight/lint/SDC và guard trên ODB thật đã đạt; không có physical step được trợ lý chạy. Xem ASIC_REPAIR08_REVIEW.md.
- Lệnh: bash scripts/06_run_openlane.sh picorv32_sobel_clk50_repair_09 picorv32_sobel_clk50_repair_07. Lỗi điện vẫn phải đánh giá tiếp từ report thực tế.

## RUN 9 đạt ba PASS; RUN 10 sửa slew/cap

- RUN 9 thực tế antenna 0/0, LVS/DRC PASS; exit 2, max_ss slew 12, nom_ss slew 1, cap 2, fanout 27. Xem ASIC_REPAIR09_REVIEW.md.
- Hai driver o31ai_4 đã là size lớn nhất. RUN 10 thêm hai buf_8 không đảo, giữ tải/diode, kiểm tra kết nối trước/sau placement/routing rồi native antenna closure. Không nới giới hạn hoặc sửa RTL/firmware.
- Chế độ electrical phải chọn rõ trong lệnh và được ghi vào frozen config/provenance. Fanout/cây clock xử lý tiếp theo report; không hứa RUN 10 full PASS.
- Lệnh người dùng: bash scripts/06_run_openlane.sh picorv32_sobel_clk50_repair_10 picorv32_sobel_clk50_repair_09 electrical.
- Trợ lý chỉ chạy precheck, lint, config/SDC load và đọc ODB. Giữ toàn bộ RUN 9 và evidence; user thực thi physical flow.

## Kết quả RUN 10 và chuyển sang thử ảnh

- Đã đọc log người dùng và SUMMARY trong archive `picorv32_sobel_clk50_repair_10_collect_20260912T163433732014Z.tar.gz`: exit 0, final views, antenna 0/0, LVS/DRC/XOR sạch, setup/hold/slew/cap không vi phạm. Fanout vẫn 27, collector FAIL_OR_INCOMPLETE đúng theo tiêu chí dự án; không nới tiêu chí để đổi nhãn.
- Có thể thử ảnh ở RTL ngay, song song với công việc còn lại về fanout. Replay hiện tại chỉ phát output/timestamp từ simulation đã kiểm chứng; chưa phải mô phỏng netlist hậu layout hoặc chạy chip thật.
- Bước xem ngay: Ubuntu `python3 scripts/replay.py reports/soc_image_smoke_01` (cần Tkinter/GUI). Không chạy lại flow hoặc simulation chỉ để mở replay.
- Ảnh thử đầu nên nhỏ (64x64, rồi 128x128); đầu vào PNG/JPEG được chuyển sang xám. Giới hạn script 512 mỗi chiều; tile mặc định 32, không yêu cầu toàn ảnh 32x32. Chưa có ảnh thật mới do người dùng chọn nên chưa tạo input/RUN mới.
- Giữ so sánh SW/HW cùng ảnh/biên/số học/memory_wait và overhead. Kết quả cũ SW573713/HW774758 chu kỳ chưa chứng minh tăng tốc. Báo cáo PPA tiếp tục phân biệt vectorless power, phạm vi không RAM/pad/package và warning IR nguồn chưa xác định.

## Kiểm kê và kế hoạch ảnh SIPI

- Đã giải mã đủ 20 TIFF trong images: 14 ảnh 256x256, 6 ảnh 512x512; 13 RGB và 7 L, 8 bit/kênh, một frame, hash riêng. Không sửa ảnh hoặc chạy CPU.
- Kế hoạch và hash gốc ở IMAGE_TEST_PLAN.md: bắt đầu 5.1.13 chart256, rồi house256/plant256; peppers512/mandrill512 sau khi xử lý watchdog.
- Ubuntu thiếu Pillow; image prep có thể đọc TIFF qua Pillow, nguồn TIFF đọc trực tiếp từ /mnt/e vì copy script không copy images. Giữ TIFF ngoài Git.
- Phát hiện timeout 600 s quá ngắn có thể ảnh hưởng 256; lệnh dự kiến dùng --timeout-seconds 3600. Watchdog 100 triệu chu kỳ có nguy cơ chặn 512; chưa sửa watchdog/TB hoặc chạy ảnh lớn trong phiên lập kế hoạch.
- Không chạy lại OpenLane chỉ vì đổi ảnh. Các số ngoại suy thời gian trong kế hoạch là dự trù từ smoke test, không phải số đo mới.

## 2026-09-13 — ưu tiên Shapes 32/64, hoãn SIPI

- Người dùng yêu cầu test bộ images 2/output_32x32 và output_64x64 trước. Đã đọc đủ 40 PNG, đúng kích thước, mode L 8-bit, một frame. Không chạy script extraction hay sửa ảnh gốc.
- Đã chuẩn bị input shapes32_00_01, shapes32_01_01, shapes64_00_01, shapes64_01_01 bằng prepare_image.py, so khớp từng byte/hash nguồn. Ubuntu không cần Pillow để chạy các input này. Không tạo output Sobel hoặc chạy simulation.
- Kế hoạch SMALL_IMAGE_TEST_PLAN.md: hai RUN32 rồi hai RUN64, từng RUN; tile16 để replay 4/16 vùng, memory_wait1, timeout/watchdog giữ nguyên. Mở rộng bộ 40 sau khi lượt nhỏ đạt.
- Giữ nguyên RTL/firmware/SDC/flow; không cần OpenLane mới. SIPI hoãn, không chạy theo lệnh 256 cũ.

## 2026-09-13 — Shapes 32 đầu tiên PASS

- ZIP soc_shapes32_00_01 đã export. Đã đối chiếu hash, firmware, snapshot với nguồn hiện hành, 1024 pixel/4 tile mỗi SW/HW, output.pgm và timestamp. Không simulation rerun.
- SW453421 cycles/10.081s host; HW613171 cycles/14.993s host. HW thêm35.2322% chu kỳ, chưa tăng tốc. Chi phí MMIO/CPU là hướng phân tích, chưa đo phân rã.
- Bước tiếp theo replay rồi soc_shapes32_01_01, tile16/memory_wait1. Giữ bộ ảnh nhỏ; không chạy lại ASIC vì đổi ảnh. Chi tiết/hash archive ở SMALL_IMAGE_TEST_PLAN.md.

## 2026-09-13 — replay xác nhận trực quan, chuyển sang phân tích hiệu năng

- Người dùng đã mở replay soc_shapes32_00_01 và xác nhận hiển thị vùng16x16 phù hợp. Ảnh chụp hiển thị SW453421/HW613171 đúng trace; không sửa số liệu/tốc độ replay để tạo tăng tốc.
- Source filter HW có ít nhất5 MMIO transactions/pixel (2 data writes, start, status, result), cộng việc CPU lấy pixel/địa chỉ. Core kết thúc cạnh kế sau start; cần giảm overhead giao tiếp.
- PERFORMANCE_OPTIMIZATION_PLAN.md ghi bước profiling TB theo handshake trước, rồi giảm giao dịch/streaming nếu dữ liệu đo hỗ trợ; giữ baseline32, test64 sau. Chưa sửa RTL/firmware, chưa chạy test mới. Không mặc định dùng lại PPA RUN10 cho phần cứng mới.

## 2026-09-13 — Tile DMA v1 chuẩn bị cho mục tiêu15-20%

- Sau khi người dùng push baseline, triển khai sobel_tile.v + native_bus_arbiter.v. CPU cấu hình vùng; hardware đọc hàng xóm và ghi output RAM; CPU vẫn thực thi firmware và báo tile event. Legacy MMIO/core giữ nguyên.
- Thêm hai unit TB và profiler quan sát bus. Cùng image32/tile16/memory_wait1, code SW không đổi byte; HW652 byte mới. Không làm chậm SW. Pixel/tile golden checker giữ nguyên.
- Compile GCC/Icarus, Python/Bash/hash và Verilator lint đạt. Không simulation/Step.start/PNR. Các unit test mới chỉ compile, chưa có PASS thực thi.
- Lệnh user: bash scripts/03_run_soc_tests.sh soc_shapes32_dma_01 --image inputs/shapes32_00_01 --tile 16 --memory-wait 1; export script04 cùng tag. Chờ số đo, không hứa phần trăm đạt.
- TILE_DMA_RUN_GUIDE.md ghi ABI, memory arbitration, profiler và giới hạn. Mục tiêu báo cả speedup và mức giảm thời gian ở cùng clock. Hoãn256/512.
- Config thêm module mới, asic_project.TEST yêu cầu evidence tagdma mới. Không tiếp tục physical checkpoint RUN10 vì RTL khác; PPA mới chưa đo. RAM/profiler/hostGUI vẫn ngoài ASIC.

## 2026-09-13 — Tile DMA RUN32 đầu tiên đã được xác minh

- Người dùng chạy soc_shapes32_dma_01: 4 unit PASS, toàn bộ1024 pixel/4 tile SW/HW PASS. SW453421/HW69406cycles, speedup6.532879, giảm84.692813% tại cùng clock. Host wall11.942/2.671s tách riêng.
- Đã đọc ZIP, kiểm tra59 hash snapshot/10 trace hashes, firmware, golden từng pixel, tile timestamps và profile. Snapshot nguồn hiện hành khớp; không simulation rerun. Chi tiết/hash ở TILE_DMA_FIRST_RUN_REVIEW.md.
- Giữ RTL, test tiếp soc_shapes32_dma_02 với inputs/shapes32_01_01, rồi soc_shapes64_dma_01 với inputs/shapes64_00_01, tile16/memory_wait1. Người dùng chạy và export script04.
- Mục tiêu15-20% đạt trên ảnh đầu; cần mở rộng bộ kiểm chứng. Physical checks/PPA của DMA chưa chạy, không kế thừa PASS/PPA RUN10.

## Test256 thử trước bộ ảnh chính thức

- Người dùng yêu cầu thử một ảnh256. Chuẩn bị inputs/sipi_chart256_dma_01 từ images/5.1.13.tiff, bytecheck65536pixel nguyên vẹn. Không đổi RTL/firmware, không simulation.
- Lệnh và hash trong TEST_256_DMA_GUIDE.md: RUN soc_sipi_chart256_dma_01, tile16/memory_wait1/timeout3600s; watchdog100M giữ nguyên. Người dùng copy/chạy/export.
- RUN64 log người dùng: FUNCTIONAL PASS, SW1822739/HW281750cycles, speedup6.469349, 4096pixels/16tiles; ZIP đã xuất. Chưa dùng làm PPA.

## Bàn giao sau RUN256 — tạm dừng theo yêu cầu người dùng

- Người dùng yêu cầu để công việc phát triển sang phiên sau; không chạy thêm test hoặc sửa RTL/firmware trong phiên nhận kết quả.
- RUN soc_sipi_chart256_dma_01: log và SUMMARY trong ZIP xác nhận FUNCTIONAL TEST PASS, 65536pixel/256tile mỗi SW/HW. SW29435845/HW4565534cycles, speedup6.447405, giảm84.490% tại cùng clock. Host SW681.066s/HW111.858s; không phải thời gian chip.
- DMA521220 reads/65536 writes/256starts. RUN hoàn tất, không gặp timeout/watchdog theo log. Windows reports/soc_sipi_chart256_dma_01.zip đã tồn tại. Phiên này mới đối chiếu log/SUMMARY và hash ZIP, chưa kiểm tra lại toàn bộ pixel/hash snapshot của RUN256.
- Cần làm phiên sau: audit ZIP256 (và ZIP32_dma_02/64_dma_01 chưa được audit toàn bộ ở các phiên nhận log); chuẩn bị SW optimized làm đối chứng, giữ nguyên baseline; chờ bộ ảnh32/64/128/256 người dùng chuẩn bị, xác định preprocessing thống nhất và test kích thước lẻ/memory_wait khác; sau chức năng ổn chuẩn bị full OpenLane cho RTL DMA.
- Kết quả hiện so với SW C baseline -O2 RV32I, chưa chứng minh tối ưu SW tốt nhất. RGB chuyển gray trên host, ngoài thời gian đo. Không gán PPA/physical PASS của repair_10 cho DMA mới; ASIC DMA NOT_RUN. RUN10 vẫn còn27fanout violations.
- Không xóa/ghi đè RUN cũ, không tự chạy simulation/OpenLane. Reports/runs/run_inputs ngoài Git; bằng chứng phải backup riêng. Input SIPI256 cũng ngoài allowlist Git, giữ riêng.
- SHA256 ZIP256: 23c4b08390e8af2bc1f288f0d3dfbee25b5985dd6529beae2dbff09d799bb1f9


## Hướng dẫn bộ ảnh chuẩn và watchdog512

- Bộ test image có43ảnh, thư mục32/64/128/256/512 đúng kích thước. STANDARD_IMAGE_TEST_COMMANDS.md có lệnh chuẩn bị/chạy/export/replay cho5size và2ảnh128 A/B cụ thể. Ảnh gốc giữ nguyên, RGB chuyểnL8bit host ngoài thời gian đo.
- Đã thêm --max-cycles runner/plusarg TB, mặc định100M, giới hạn1..2tỷ, ghi config/command và áp dụng chung SW/HW. Lệnh512 chọn250M/7200s mỗi subprocess. Không đổi RTL/firmware/golden/cycle interval; Icarus/static PASS. Không simulation.
- Input được người dùng tạo trong Ubuntu, kết quả reports/RUN và ZIP; script04 xuấtZIPWindows. Các input mới ngoài Git và nằm trong snapshotZIP. Không tự động chạy cả bộ.

## Chốt nền tảng báo cáo trước nâng cấp

- Người dùng yêu cầu RUN mới toàn bộ hiện trạng, từ đầu không kế thừa, rồi mở OpenROAD kiểm tra. Chuẩn bị picorv32_sobel_dma_clk50_baseline_01, launcher08 cố định khôngparent. Chưa chạy flow.
- Pin nền tảng grayscaleDMA hiện tại/clock50ns, tạm hoãn RGB và SWoptimized đến sau baseline. Liên kết4ZIP chuẩn32/64/128/256 khớp RTL/TB/firmware.
- Native antenna repair được chọn trên chính DRT mới qua flagSOBEL_NATIVE_ANTENNA_REPAIR; không bật continuation/oldpinECO. Allchecker giữ nguyên.
- Collector bảo toàn tất cả finalviews trongarchive. Viewer09 đọcfinalODB bằngDockerimage đãpin, mountreadonly; không chạy physicalflow. Guide ASIC_DMA_BASELINE_GUIDE.md.

- Precheck build/asic_precheck_T8ZiVbjU PASS; freezeaudit4ZIP/hash/no-parent PASS; readfinalODB cũ bằng OpenROAD -exit PASS. Không physicalflow chạy. User next: copy script00, cdUbuntu, bash scripts/08_run_report_baseline.sh, collect07. Saufinal dùngviewer09 theo guide.

## Kết quả baseline01 và mở layout RUN chưa PASS

- Người dùng chạy full baseline01 đến81/81; exit2. Antenna0/0, LVS/DRC PASS, setup sạch; lỗi hold/slew/cap tại max_ss_100C_1v60. Metrics global slew11/cap1/fanout65. Chưa chốt baselinePASS.
- Không có final/. State79-misc-reportmanufacturability tham chiếu ODB57-odb-cellfrequencytables/picorv32_sobel_soc.odb, saufill/routing. StageGDS61-magic-streamout có tham chiếu trongstate.
- Viewer09 bổ sung --latest-state rõ ràng cho incompleteRUN: lấyODB đúngstatecuối, chỉ trongRUN yêu cầu, ghihash/nguồn và nhãnSTAGE VIEW; projectread-only. Không sửa snapshot cũ. Hai fileviewerđã đồng bộ sangUbuntu.
- OpenROAD GUI đãkhởi chạy vàlog xác nhận ODBloaded; khôngflow rerun. Lệnh mởlại: bash scripts/09_open_final_openroad.sh picorv32_sobel_dma_clk50_baseline_01 --latest-state.
- Evidence userexport: reports/picorv32_sobel_dma_clk50_baseline_01_collect_20260913T103147143862Z.tar.gz. Tiếp theo chẩn đoán chínhxácpath/net/corner, chuẩn bịbaseline02 FULL từđầu nếu sửa; giữbaseline01.

## Baseline02 sửa lỗi điện, vẫn full từ đầu

- RUN01: hold2inputpaths ext_rdata[2]/[0], −14.998/−8.628ps tại maxSS; slew11entriescùngfanout26(buf_1), cap85.686fF>81.492fF. Không bằngchứng lỗi thuậttoán hoặc toolchạysai.
- Bản02: postGRT holdmargin0.2ns; slew/cap optimization margins55%; extraRepairDesignSlowCorner trước multi-cornertiming để targetmaxSS riêng. Signoff9corner/clock/SDC/checker/RTL/firmware/nativeantenna khôngđổi. Fanout65RUN01chưađượcchứngminh đãsạch.
- Launcher08chọnpicorv32_sobel_dma_clk50_baseline_02, khôngparent. GuideASIC_DMA_BASELINE_GUIDE.mdcậpnhật. PrecheckMXXQeUvAPASS; chưa physicalRUN02. Usercopy00/chạy08/collect07tag02.

## RUN12 / baseline02 — kết quả nhận, tạm dừng theo người dùng

- Tên chính xác picorv32_sobel_dma_clk50_baseline_02. Log exit0, Flowcomplete81/81, finalviews đã xuất; Antenna/LVS/DRC, setup/hold/slew/cap PASS.
- Collector vẫn FAIL_OR_INCOMPLETE; fanout metric=62. Không gọi tất cả tiêu chí sạch. Phiên sau audit đầy đủ archive và các check/giới hạn còn thiếu, tổng hợp PPA.
- ArchiveWindows reports/picorv32_sobel_dma_clk50_baseline_02_collect_20260913T110947807320Z.tar.gz đã có. Giữ RUN12 và snapshots, không chạy lại hoặc sửa trong phiên nhận kết quả.
- Mở OpenROAD final bằng: bash scripts/09_open_final_openroad.sh picorv32_sobel_dma_clk50_baseline_02. Không cần --latest-state vì đã cófinalODB. Người dùng yêu cầu lệnh, chưa tự mở GUI lần này.

## Lưu RUN12 và chuẩn bị fanout — 2026-09-13

- User yêu cầu bảo toàn RUN12 trước khi sửa62fanout. Đã lưu full archive1565file/406417999byte, đối chiếu từngSHA256; xem RUN12_PRESERVATION_AND_FANOUT.md.
- baseline_02 là RUN12: exit0/Ant/LVS/DRC/setup/hold/slew/cap đạt, fanout62. Không gọi fullsignoff.
- ODB xác định23clock từCTS và39signal códiode sauDRT/antenna closure.
- baseline_03 là RUN13, full từđầu. CTS native có wrapper đặt mục tiêu cell6; extra SS repair đặt mục tiêu design5 trước diode. Trảvề giới hạn10 trước lưu/timing; SDC/RTL/firmware/checker khôngđổi.
- Trợ lý chỉ config/lint/API/SDC/mock checks; người dùng chạyflow để xác nhận tác động fanout/timing/antenna/PPA. Không tiếp tục checkpoint của RUN12.

## RUN13 lỗi bootstrap; chuẩn bị RUN14

- baseline_03 exit1 đầu CTS34: SOBEL_SCRIPT_DIR nằm trong `_env.tcl` nhưng wrapper chưa source. Stage33 là state hoàn tất cuối. Archive user đã collect, giữ nguyên.
- Sửa hai wrapper CTS/postGRT bằng source `_TCL_ENV_IN` trước biến custom. Không đổi RTL/firmware/config/SDC/fanout targets hoặc checker.
- Thêm regression dùng OpenLane `_reroute_env` thật và upstream stub: bản cũ tái hiện lỗi, bản sửa cả2wrapper PASS. Không gọi CTS/resizer/Step.start.
- Precheck PeAmhKU6 PASS; nguồn chức năng khớp bốn ZIP benchmark. RUN14 baseline_04 chạy81steps từ đầu qua08, collect07baseline_04. Chưa physicalPASS mới.

## RUN14 lỗi chọn cell; chuẩn bị RUN15 — 2026-09-14

- baseline_04 exit1 đầuCTS34: mỗi clock buffer có4STAobject cùngtên sau nạp3Libertycorner. Chưa chạyCTS. Guard cũ đòi1object là lỗi wrapper của trợ lý.
- Chọn chính xácSTAcell liên kết với ODB master.staCell, kiểm thêmname/library; không chọnfirstmatch. Fixture readLEF/link_design có5candidate cũng được xử lý đúng.
- Precheck d2Icy7F6 PASS config/lint/SDC/API/env/multi-corner real-library tests. Thử readonly actualODB/SDC/Liberty RUN14 cũng PASS lựa chọn4clockmasters, CTSdelegate stub; khôngphysicalflow.
- RUN15 baseline_05 full81steps từđầu qua08; collect07baseline_05. Không đổiRTL/firmware/config/SDC/fanouttarget/checker; bảo toàn RUN12/13/14.

## Đánh giá RUN15 thực tế — 2026-09-14

- baseline_05 đi hết81step, exit2; Antenna/LVS/DRC/setup/holdPASS. Fanout4 (từ62), slew20/cap8 (từ0), instancearea193493µm² (RUN12=172005). Chưa chấp nhận làm baseline cuối.
- 4fanout làclock clkbuf_2_[0..3]_0_clk/X, mỗi16tải;5clockdrivers lỗi cap. 20slew thuộc3net tín hiệu fanout4485/net4662,fanout4549/net4726,_12538_/_07482_, có1/5/2diode cuối. STA59maxSS là nguồn lỗiđiện.
- Giữ RUN12đãbackup và RUN15thửnghiệm. Không hứa xóa mọiWARNING; khôngtắtchecker/nớiSDC. Xem RUN15_REVIEW.md.
- Phiên này đánh giá bằng actualreport/ODBread-only; không sửaconfig/RTL, không chạyflow, chưa chuẩn bịRUN16. Launcher08vẫn tag05đãtồn tại, tránh chạy lại.

## Chuẩn bị RUN16 theo yêu cầu chốt sạch — 2026-09-14

- baseline_06 full81steps từ đầu qua08, chưa physicalrun. Giữ mọiRUNcũ/RUN12backup.
- CTSspacing80µm, nativebranching_point_buffers_distance1µm; giữ targetfanout6 để tránh tầng2lái16tải ởtầng6.
- ExtraSSrepair2lượt:55%rồi70%slew/capmargin, fanout5 phục hồi10 kểcảlỗi. NativeGRT/DPL/timing/antenna/chếđộsignoffgiữnguyên.
- Precheck CvJfVKaZ PASS: config/lint/SDC/API/env/master/regressions, installedCTS Tclparser vớiC++engine stub. Khôngflow/simulation.
- Warnings nguồnPDK, VSRC, wirelength chưa cóthreshold đượcgiảithíchtrongRUN16_REPAIR_PLAN.md; khôngchelog hoặc bỏchecker. Chưa hứaPASS hoặc sốWARNINGgiảm.


## RUN16 đã chạy — đánh giá khả năng chốt 2026-09-14

- User hỏi có đáng sửa hết WARNING không; chưa yêu cầu RUN17. Đã đọc báo cáo thật/ODB/LEF, không simulation hoặc physical flow.
- baseline_06 exit0, full81stage, Antenna/LVS/DRC/setup/hold/slew/cap PASS; fanout1 khiến collector FAIL_OR_INCOMPLETE. Instance area195012µm². Không gọi sạch toàn bộ.
- wire45/X buf8/net1746 trước DRT chỉ có fanout4272/A; sau DRT có thêm10diode ANTENNA_547..556, tổng11>10. Không xóa diode/nới giới hạn/tắt checker. Chèn buffer hay đổi routing có thể xử lý nhưng phải tái kiểm tra, chưa được thực nghiệm.
- 5nhómWARNING: GRT giữa flow, LEF58 parser, WireLength chưa ngưỡng, VSRC thiếu mô hình, 2output thiếu diffusion. LEF và ODB xác nhận ext_addr[0:1] là hai output thiếu diffusion, được tieLO conb1. Không bỏ hở; không bịa antenna data.
- Đề xuất chốt RUN16 làm baseline phòng thí nghiệm có ngoại lệ fanout1 và giới hạn kiểm tra; không hứa fullsignoff. Chưa chuẩn bị RUN17. RUN16_REVIEW.md lưu bằng chứng và phân tích khả thi, README cập nhật; RTL/config/SDC/scripts không đổi trong phiên này.
- Archive final hiện có reports/picorv32_sobel_dma_clk50_baseline_06_collect_20260914T045526219194Z.tar.gz, SHA256620ba7d4dbde97777013e0748a4018863344fdc91d0fb0d557a38603ab2568a0. Đây không phải backup toàn bộ stageODB; các stage vẫn ở Ubuntu. RUN12 fullbackup còn nguyên.
- Launcher08 trỏ tag06 đã tồn tại, không chạy lại. Viewer09 mở final tag06 mà không chạy flow. Bước tiếp theo đề xuất: bảo toàn bằng chứng, tổng hợp PPA/utilization/benchmark theo phạm vi RAM ngoài, power vectorless, IR indicative đã ghi.


## RGB branch — 2026-09-15
User approved sequential R/G/B processing and original-color replay. Branch codex/rgb-from-run16 starts at e9ff741; RUN17/18 edits are preserved in stash commit 9655c28f108e231d3df66c4824e54f60c41e770f, also reachable through codex/preserved-run17-run18 (including untracked files in its third parent). Do not drop this stash or overwrite old runs.
No synthesizable RTL or physical config is changed. The existing DMA windows cap this version at RGB256x256 (three planar channels); grayscale512 remains supported. A 512x512 RGB input is rejected before execution. All channel processing/control and output transfers are timed inside one CPU execution per variant. GUI playback is based on verified full-tile R/G/B output.
Assistant may compile/static-check, but user runs simulation and OpenLane. No physical run is scheduled by the RGB upgrade. Old physical launchers are historical; do not reuse their RUN names. Consult RGB_RUN_GUIDE.md for commands and scope.

## RGB32 actual result — 2026-09-15
User-run soc_rgb32_smoke_01 FUNCTIONAL PASS and ZIP exported. Reaudited73 frozen hashes,11 evidence hashes,3072 channel samples per SW/HW and4 full-RGB tile events. SW1352946/HW206960 cycles (6.537234x). No new physical or activity-based power run. Next user-run checks: RGB17x19 memory_wait3 and grayscale regression. See RGB32_FIRST_RUN_REVIEW.md.
