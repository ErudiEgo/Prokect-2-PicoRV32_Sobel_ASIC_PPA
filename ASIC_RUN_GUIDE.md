# Chạy ASIC PicoRV32 + Sobel — OpenLane Classic

Chuẩn bị ngày 2026-09-12. Đây là bước chạy vật lý sau khi người dùng hoàn tất simulation `soc_image_smoke_01`.

**RUN `repair_08` chưa PASS: antenna 4/5, lỗi điện còn tồn tại.** RUN mới `picorv32_sobel_clk50_repair_09` bắt đầu từ checkpoint pre-filler RUN 7 (2/2), dùng native post-DRT repair để giữ dây hiện có làm đầu vào. Không dùng vòng xóa toàn bộ dây/reroute cũ. Xem [chẩn đoán](ASIC_REPAIR08_REVIEW.md).

## Phạm vi và môi trường

- Top: `picorv32_sobel_soc`, `ENABLE_SOBEL=1`: CPU + Sobel MMIO + bus. Program/image RAM ngoài, host logger, pad ring và package không thuộc PPA này.
- Docker đã kiểm tra: `ghcr.io/efabless/openlane2:2.3.10`, image ID `sha256:37c3bd4ea0534a276cb2deb88d601044857bad2807b9bc5b36efe9d02c62624e`.
- Classic gốc có 78 bước; repair_04 thêm 3 bước sửa, tổng cộng **81 bước chính**, giữ đủ 78 bước gốc. Một số bước điều kiện vẫn được skip; 81/81 không tự chứng minh PASS.
- PDK đã nạp: `sky130A`, library `sky130_fd_sc_hd`, Volare revision `0fe599b2afb6708d281543108caf8310912f54af`.
- Tham khảo chức năng flow: [OpenLane Classic](https://openlane2.readthedocs.io/en/latest/reference/flows.html). Script kiểm tra phiên bản cài thực tế, không dựa hoàn toàn vào tài liệu latest.

## Cấu hình repair_09 (giữ cấu hình vật lý repair_04)

Clock vật lý 50 ns (20 MHz mục tiêu), có CTS. Đây là điểm bắt đầu, chưa phải tần số đạt được. Chưa đổi RTL/firmware để tối ưu tốc độ ảnh: bản HW của RUN mô phỏng đầu tiên vẫn chậm hơn SW về chu kỳ.

Floorplan relative, `FP_CORE_UTIL=35%`, placement target density 50%, padding 2. Diện tích die sẽ được tính sau synthesis, không giả định die bằng ví dụ UART hoặc bộ nhân trước đây. Hai tỷ lệ đặt này không phải utilization đo sau routing.

SDC dùng clock thật; resetn đồng bộ được timing như dữ liệu. Input/output delay min=0,5 ns, max=5 ns; input transition=0,1 ns; tải output=10 fF; setup uncertainty=0,25 ns, hold uncertainty=0,10 ns. Fanout tối đa 10, transition 1,5 ns, capacitance 0,2 pF. Không có false path hoặc multicycle exception. Các giá trị I/O là giả định phòng thí nghiệm, chưa phải đặc tính của bộ nhớ/bo ngoài. `memory_wait` trong testbench không tự xác định các delay vật lý này.

Giữ lint checker, DRC Magic/KLayout, XOR, LVS và timing/slew/cap ở mọi corner. RUN 9 giữ SOBEL_ANTENNA_ONLY=true; mỗi vòng capture topology → native repair_antennas (1 iteration, margin 30) trên dây đã route → DetailedRouting → guard logic/diode → checker antenna độc lập. Native router cập nhật incremental GRT; không gọi full GlobalRouting/resizer và không tự xóa toàn bộ dbWire. Tối đa ba vòng, dừng sớm khi antenna 0/0. Mọi giới hạn điện, clock, RTL/firmware giữ nguyên. Chi tiết ASIC_REPAIR08_REVIEW.md.

## Lint upstream và liên kết chứng cứ

PicoRV32 upstream giữ nguyên cùng hash đã simulation. Khi chuẩn bị nguồn vật lý trong `build/asic_sources`, script chỉ:

1. Bỏ đúng một dòng timescale, tránh trộn chỉ thị thời gian simulation với model PDK.
2. Thêm comment lint đúng 33 vị trí đã rà soát: 7 GENUNNAMED, 15 UNUSEDSIGNAL và 11 BLKSEQ. Đây là các trường hợp đặt tên generate, debug/observation không dùng và biến tạm blocking có chủ ý trong upstream; thay blocking bằng nonblocking có thể đổi hành vi.

Danh sách từng dòng, nguyên văn và lý do ở `scripts/upstream_lint_review.json`; hash/provenance bản tạo ra ở `build/asic_sources/provenance.json`. Script kiểm tra khi bỏ các comment này thì nội dung trở về đúng nguyên bản trừ timescale. Không có sửa phương trình, state machine, register hay tham số CPU. Bằng chứng simulation gốc vẫn được giữ và kiểm tra hash trước chạy.

Không mô tả đây là “upstream không có warning”: có **33 ngoại lệ lint style tại vị trí cụ thể**. Lỗi latch, timing constructs, width mới ngoài phạm vi suppression sẵn có của upstream và các checker vật lý không bị tắt. Các suppression WIDTH/PINMISSING/CASEOVERLAP/CASEINCOMPLETE upstream có sẵn vẫn còn trong bản gốc; đây là giới hạn của lint IP và không thay thế test chức năng.

## Các lệnh nhập trong Ubuntu

**1. Copy mã và cấu hình mới:**

```bash
bash "/mnt/e/aa. PPA_Project_List/aaa.PicoRV32_Sobel_ASIC_PPA/scripts/00_copy_to_ubuntu.sh"
```

**2. Vào thư mục làm việc:**

```bash
cd "$HOME/openlane_projects/picorv32_sobel_asic_ppa"
```

Lưu ý: đường dẫn `~/.../reports/soc_image_smoke_01` là thư mục báo cáo simulation, không phải lệnh khởi chạy flow. Không cần chạy lại simulation đã đạt.

**3. Precheck ASIC:**

```bash
bash scripts/05_asic_precheck.sh
```

Điều kiện tiếp tục: `ASIC PRECHECK PASS`. Bước này đọc lại ZIP test, kiểm tra hash, nạp cấu hình PDK, lint standalone và nạp SDC với khai báo cổng. Nó không tổng hợp hoặc chạy stage vật lý. Log riêng ở `build/asic_precheck_...`.

**4. Người dùng chạy OpenLane Classic:**

```bash
bash scripts/06_run_openlane.sh picorv32_sobel_clk50_repair_09 picorv32_sobel_clk50_repair_07
```

Lệnh tạo RUN mới, copy/hash checkpoint và chạy từ Sobel.AntennaClosure. Classic vẫn có 81 bước chính, các bước trước checkpoint được bỏ qua; không tổng hợp/placement/DRT ban đầu lại. Script tự kiểm tra lại đầu vào, đóng băng nguồn rồi nạp/lint bản đóng băng trước khi chạy flow. Terminal tương tác được giữ TTY/màu/progress; log do OpenLane lưu, không pipe mất giao diện. Mặc định 4 jobs. Runtime chỉ đo phần tiếp tục; provenance và bản sao checkpoint nằm trong snapshot mới. Nếu config/nguồn/PDK khác checkpoint thì dừng, không tự bỏ qua kiểm tra.

Kết quả nằm tại:

```text
~/openlane_projects/picorv32_sobel_asic_ppa/runs/picorv32_sobel_clk50_repair_09
```

Nguồn đóng băng ở `run_inputs/picorv32_sobel_clk50_repair_09`, gồm source hash, config.frozen.json, input RTL gốc/bản vật lý, firmware và ZIP test. Image/PDK ghi trong environment.txt; runtime.txt ghi thời điểm, thời lượng flow và exit status. Snapshot được mount read-only trong flow. Không ghi đè tag cũ, kể cả khi flow chưa chạy do frozen precheck thất bại.

**5. Thu thập và xuất bằng chứng, kể cả flow lỗi:**

```bash
bash scripts/07_collect_asic.sh picorv32_sobel_clk50_repair_09
```

Không chạy lại flow. Mỗi lần collect tạo bộ mới có timestamp trong reports, gồm SUMMARY.txt, metrics.json, STA_SUMMARY.rpt nếu có, config/nguồn, log/report mọi stage và GDS/LEF cuối nếu có. Archive tự copy về thư mục Windows `E:\aa. PPA_Project_List\aaa.PicoRV32_Sobel_ASIC_PPA\reports`. ODB/netlist đầy đủ vẫn nằm trong RUN Ubuntu để mở layout sau này.

Mở SUMMARY theo đúng đường dẫn script in ra. Chụp màn hình stage lỗi hoặc màn hình cuối có Antenna/LVS/DRC. Báo đã export để trợ lý đọc archive. Nếu lỗi ở precheck trước khi tạo snapshot/RUN, gửi log precheck, không cần collect một RUN chưa tồn tại.

## Điều kiện đánh giá

Antenna 0/0 vẫn chưa đủ: RUN 8 có thể còn lỗi điện và exit 2. Cần actual reports: antenna sau detailed routing 0 nets/0 pins; DRC/LVS/XOR/illegal overlap sạch; setup/hold, slew/cap/fanout, disconnected pins, power grid, congestion được kiểm tra. Metric thiếu ghi MISSING; không tự đặt bằng 0. Không lấy 81/81 làm full sign-off.

Collector tách area/cell count, core/die/utilization, timing theo corner, vectorless internal/switching/leakage/total power, IR drop và bảng congestion khi có. Chưa ánh xạ switching activity từ workload Sobel vào netlist; VCD simulation không tự thành power annotation. Chưa cung cấp VSRC_LOC_FILES/nguồn package thật, nên IR drop chỉ là đánh giá theo mô hình công cụ, cần đọc warning/nguồn/tải trước khi sử dụng.

Số liệu của CPU + Sobel không được ghi là Sobel-only hoặc toàn chip có RAM. Đánh giá tiết kiệm năng lượng/tăng tốc cần thêm bản CPU baseline và điều kiện so sánh tương ứng; chưa kết luận từ một RUN.
