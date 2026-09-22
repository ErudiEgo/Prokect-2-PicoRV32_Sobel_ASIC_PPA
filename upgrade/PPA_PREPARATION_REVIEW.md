# PPA preparation — biên bản 2026-09-22

Trạng thái: **PPA_PREPARATION_ACCEPTED_STATIC_ONLY**. H1/H2 ASIC stage2 **NOT_RUN**.

Đã audit lại 10 ZIP characterization, giữ nguyên baseline H2 và nguồn Stage1. Hai cấu hình H1/H2 đã qua config load, Verilator lint, SDC port-only, lookup CTS với Liberty nhiều corner và CTS engine stub, fanout policy mock, API checks (4 tests), truyền env của hai wrapper. Không thực hiện thuật toán CTS/repair/routing.

Bảy host tests đạt: tag/path, source hash, snapshot tồn tại, PDK hash/sổ hash rỗng, launcher với subprocess stub và giữ mã lỗi, collector với thiếu report/fanout theo corner. Collector cũng đọc subset báo cáo RUN16 thật: giữ fanout=1 và FAIL_OR_INCOMPLETE; không nhận đó là H1/H2 stage2.

Evidence hiện hành: `build/ppa_pair_prepared_06`, `build/ppa_pair_static_06/PASS.json`, `build/ppa_host_tests_02.log`, `build/ppa_final_static_checks_01.json`. Các revision trước giữ để chẩn đoán, không dùng làm packet chạy. Checker hiện hành trùng byte với bản trong prepared_06.

Đã sửa trong quá trình chuẩn bị: dùng wrapper literal để lint chọn đúng DMA; mở rộng zero tường minh hai toán hạng H2 ở nguồn physical dẫn xuất; cô lập env của Tcl/mock tests; chuyển kiểu đường dẫn OpenLane khi thu hash PDK và chặn inventory rỗng. Không tắt warning/checker để đạt.

Đã hash và đối chiếu trên host 926 file PDK được resolved config trỏ trực tiếp; không tuyên bố hash toàn bộ nội dung PDK. Image/revision được pin, cấu hình chung 50 ns, sky130A/HD, Classic 78+3. Power/IR vẫn theo giới hạn trong PPA_RUN_GUIDE.md; whole-design formal equivalence và native antenna closure trên thiết kế mới chưa được kiểm chứng.

Lệnh tiếp theo: theo PPA_RUN_GUIDE.md, copy → precheck `s2_ppa_pair_clk50_01` → user chạy H1 `s2_ppa_h1_clk50_01` → collect kể cả lỗi → review trước H2. Không chạy lại characterization hoặc mở H3/FPGA.
