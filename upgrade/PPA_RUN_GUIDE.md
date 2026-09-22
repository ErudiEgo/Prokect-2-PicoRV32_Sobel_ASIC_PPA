**Cập nhật 23/09: H2 ECO đã chạy và audit đạt với các giới hạn công khai. Xem [H1_H2_PPA_ACCEPTANCE.md](H1_H2_PPA_ACCEPTANCE.md). Các lệnh/tag ECO bên dưới là lịch sử, không chạy lại.**

**Bước chạy tiếp theo: [H2_ECO_RUN_GUIDE.md](H2_ECO_RUN_GUIDE.md). Đã đạt preflight tĩnh; physical ECO chưa chạy. Tiếp tục H2 bằng 4 buffer có mục tiêu từ checkpoint repair01, dùng scripts 34/35/36 và RUN mới `s2_ppa_h2_eco_clk50_01`.**

**Cập nhật sau H2 repair_01: vẫn FAIL (fanout1/cap2/slew4), chưa phải H3. Xem H2_REPAIR01_REVIEW.md. Các lệnh repair_01 bên dưới là lịch sử; không chạy lại tag cũ.**

**Cập nhật H2 RUN01: FAIL cap1/fanout6; xem H2_PPA_REVIEW.md và lệnh repair mới. Các lệnh baseline dưới đây là lịch sử, không chạy lại tag cũ.**

# Stage 2 — cặp PPA H1/H2, chuẩn bị 2026-09-22

**Nhóm B — ASIC/PPA. H1 đã chạy và review đạt trong phạm vi báo cáo; H2 RUN01 FAIL cap1/fanout6.** Xem H1_PPA_REVIEW.md. Các bước copy/precheck/H1 dưới đây là lịch sử đã hoàn tất; hiện chạy H2 bằng cùng pair. Mười RUN characterization đã audit; không chạy lại simulation để chuẩn bị PPA. Dùng một gói nguồn chung cho hai RUN vật lý mới. RUN16 chỉ cung cấp phương pháp và công cụ lịch sử, không thay cho phép đo mới.

## Mục tiêu và phạm vi

Đo trade-off H1/H2: standard-cell area/count, core/die area, timing theo corner, power vectorless, IR/congestion và toàn bộ checker. Giả thuyết: H2 giảm traffic/cycles đã đo, nhưng hai line buffer và logic điều khiển có thể tăng area hoặc làm timing xấu hơn. Chưa có kết luận area/power của H2.

Giữ CPU, legacy Sobel MMIO, arbiter, memory interface và Sobel arithmetic; chọn một tile DMA H1 hoặc H2. H2 local line buffers nằm trong top và chịu chi phí tổng hợp. Không có SRAM macro được tích hợp. Program/frame RAM của testbench, controller bộ nhớ ngoài thực, pads/package, camera/display đều ngoài physical top. Không dùng full-frame FF RAM.

Hai wrapper `picorv32_image_ppa` chỉ nối cổng và đặt DMA_VERSION=1/2 bằng literal. OpenLane 2.3.10 lint không áp dụng SYNTH_PARAMETERS như synthesis; wrapper đảm bảo cả lint lẫn synthesis chọn đúng kiến trúc. Hai config chỉ khác đường dẫn wrapper. Không đổi RTL/firmware/testbench đã freeze.

Nguồn physical dẫn xuất giữ 33 chú thích style upstream của RUN16 và bỏ timescale CPU. Riêng H2 có hai phép mở rộng zero tường minh từ sx/sy unsigned 7 bit thành 16 bit trong so sánh bằng; Verilog trước đó đã mở rộng ngầm như vậy. Có `h2_width_derivation.json` và SHA trước/sau. Đây là lập luận tương đương của hai biểu thức, **không phải whole-design formal equivalence hoặc gate-level simulation**.

## Điều kiện chung

- OpenLane v2.3.10, image ID `sha256:37c3bd4ea0534a276cb2deb88d601044857bad2807b9bc5b36efe9d02c62624e`.
- SKY130 Volare `0fe599b2afb6708d281543108caf8310912f54af`, sky130A / sky130_fd_sc_hd.
- Classic 78 bước gốc + 3 additions = 81 bước cấu hình. Đây là các bước physical flow, không phải 78 bài test RTL. Không truyền `--flow Classic` vì phiên bản này sẽ bỏ meta substitutions.
- Clock thử nghiệm 50 ns; core utilization đặt 35%, placement density đặt 50%. Cùng phương pháp relative sizing, không ép hai core/die có cùng diện tích. Đây chưa phải clock sản phẩm cuối cùng.
- SDC: clock thật, I/O max/min 5/0,5 ns; transition 0,1 ns; uncertainty setup/hold 0,25/0,10 ns; load 10 fF; giới hạn fanout 10, slew 1,5 ns, cap 0,2 pF. Reset được timing đồng bộ, không thêm false path.
- Giữ cấu hình repair RUN16, không tắt checker/nới giới hạn. Cấu hình này được chọn từ lịch sử H1; phép so sánh đầu là cùng một phương pháp, chưa phải tối ưu riêng cho mỗi kiến trúc. RUN16 còn một fanout violation, nên các RUN mới không được mặc định PASS.
- Power là vectorless; IR dùng giả định nguồn/tải của flow, chưa có pad/package/board model. Không lấy power RUN16 hoặc power vectorless nhân cycles để tuyên bố năng lượng thực của workload.

## Lệnh nhập trong Ubuntu

Chỉ người dùng chạy flow. Mỗi tag dùng một lần. Nếu precheck lỗi, giữ log và chọn tag mới sau khi sửa; không xóa snapshot để dùng lại tên. `physical/run16_reference/` chỉ là nguồn tham chiếu bất biến; không chạy launcher lịch sử bên trong.

1. Copy nguồn mới, giữ RUN/evidence cũ:

```bash
bash "/mnt/e/aa. PPA_Project_List/aaa.PicoRV32_Sobel_ASIC_PPA/upgrade/scripts/00_copy_to_ubuntu.sh"
```

```bash
cd "$HOME/openlane_projects/picorv32_sobel_stage2"
```

2. Chuẩn bị một cặp — chỉ audit dữ liệu cũ, hash, config/lint và SDC port-only:

```bash
bash scripts/30_ppa_precheck.sh s2_ppa_pair_clk50_01
```

Cần `PPA PAIR READY: s2_ppa_pair_clk50_01 ; ASIC NOT_RUN`. Snapshot ở `run_inputs/s2_ppa_pair_clk50_01`; log `preflight/console.log`, `PASS.json`, hash các PDK file được config tham chiếu và `READY.json`. Các dòng `OLD FAILURE REPRODUCED`/`OLD UNIQUE-NAME GUARD WOULD FAIL` thuộc test đối chứng của lỗi cũ; cần kết luận PASS cuối cùng. Warning PDK `NOWIREEXTENSIONATPIN ... obsolete` được giữ nguyên. Không tự pull image/cài PDK khác. Môi trường lệch sẽ dừng. Precheck không đo timing/PPA và không chạy lại CPU simulation.

3. Chạy H1 trước — đây là lệnh bắt đầu flow nặng:

```bash
bash scripts/31_run_ppa.sh h1 s2_ppa_h1_clk50_01 s2_ppa_pair_clk50_01
```

Terminal giữ màu/progress khi chạy tương tác. Mặc định 4 jobs. Mỗi RUN chụp lại đúng packet, kiểm tra hash trước chạy, không resume/skip stage. Wall-clock OpenLane lưu riêng trong `runtime.txt`, không phải cycles hay target execution time.

4. Thu/export kể cả khi flow lỗi:

```bash
bash scripts/32_collect_ppa.sh s2_ppa_h1_clk50_01
```

Gửi archive `s2_ppa_h1_clk50_01_collect_*.tar.gz` được export về Windows `upgrade/reports/`. Collector không chạy lại flow. Exit0 của launcher/collector chưa phải đạt sign-off. Xem `SUMMARY.txt`, `metrics.json`, báo cáo STA và raw reports. Nếu precheck dừng trước khi có RUN, gửi log preflight thay cho báo cáo layout chưa tồn tại.

**Dừng tại đây để review H1.** Nếu cần sửa điều kiện vật lý, tạo pair mới và chạy lại cặp tương ứng để giữ so sánh công bằng. Không tự sửa riêng H2 rồi ghép với H1 cũ như cùng điều kiện.

Sau review H1 cho phép tiếp tục với cùng pair:

```bash
bash scripts/31_run_ppa.sh h2 s2_ppa_h2_clk50_01 s2_ppa_pair_clk50_01
```

```bash
bash scripts/32_collect_ppa.sh s2_ppa_h2_clk50_01
```

## Nghiệm thu và handoff

Chỉ ghi từng checker PASS từ report thực. Thiếu report là MISSING; nonzero violation là FAIL. Phải xem antenna sau detailed route, fanout/slew/cap, setup/hold mọi corner, DRC/LVS/XOR, overflow, CTS/clock và provenance. Flow completion không phải tapeout sign-off. Lưu cả kết quả âm.

Collector kế thừa RUN16, thay binding snapshot/variant và export vào stage2; giữ toàn bộ final views và raw metrics/log/reports, không gộp timing cũ trong antenna state vào timing cuối. Bổ sung kiểm tra fanout theo corner. Evidence characterization và archive physical không thay thế nhau: raw functional evidence vẫn nằm trong 10 ZIP đã giữ; `functional_link.json` ghi hash liên kết.

Các file cần đọc phiên sau: `H2_CHARACTERIZATION_ACCEPTANCE.md`, hướng dẫn này, `physical/prepare_ppa.py`, `physical/check_ppa.py`, `physical/ppa.py`, `physical/collect_ppa.py`, packet và báo cáo người dùng vừa chạy. H3 mới ở roadmap; chưa mở RTL H3/FPGA/camera trong lượt này.
