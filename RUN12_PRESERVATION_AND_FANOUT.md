# Lưu trữ RUN12 và sửa fanout

## RUN12 được bảo toàn — 2026-09-13

Tên chính xác: `picorv32_sobel_dma_clk50_baseline_02`.
RUN đầy đủ từ đầu, exit 0, Antenna 0 pin/0 net, LVS/DRC/XOR sạch;
setup/hold/slew/cap đạt các checker đã chạy. Còn **62 vi phạm max fanout**,
vì vậy collector vẫn giữ `FAIL_OR_INCOMPLETE`. Không gọi đây là full signoff.

Bản sao đầy đủ tại Windows:
`backups/run12_20260913T144806Z/picorv32_sobel_dma_clk50_baseline_02_FULL.tar.gz`.

- Dung lượng: 406417999 byte; 1565 file, bao gồm mọi stage và run_inputs đóng băng.
- SHA256 archive: `05b023d5eb05c82da3354348e3cf5102ae4c03d8984015de33752ac07709781c`.
- Mỗi file trong archive đã được đối chiếu kích thước và SHA256 với nguồn Ubuntu.
- `manifest.json` cùng thư mục ghi hash từng file; `README.txt` mô tả phạm vi.
- Giữ nguyên RUN, final views và snapshot tại Ubuntu. Không ghi đè hoặc xóa.
- PDK và Docker image không nằm trong archive. Giữ SKY130 revision
  `0fe599b2afb6708d281543108caf8310912f54af`, OpenLane image
  `sha256:37c3bd4ea0534a276cb2deb88d601044857bad2807b9bc5b36efe9d02c62624e`.
- Đây là backup trên cùng máy, chưa phải bản sao ngoài máy. Git bỏ qua archive nặng;
  tài liệu này được phép theo Git. Người dùng có thể copy nguyên thư mục backup ra ổ khác.

## Chẩn đoán từ ODB và báo cáo thật

| Stage RUN12 | Clock fanout >10 | Signal fanout >10 | Tổng |
|---|---:|---:|---:|
|34-openroad-cts|23|0|23|
|43-sobel-repairdesignslowcorner|23|0|23|
|47-openroad-detailedrouting|23|22|45|
|48-sobel-antennaclosure và final|23|39|62|

23 net clock có fanout 11–15, nằm giữa nhánh H-tree và các leaf buffer.
39 net tín hiệu đều có tải diode antenna; nhiều net đã đủ 10 tải trước khi thêm diode.
Ví dụ `net1729` có fanout14, trong đó5 diode. Không xóa diode để giảm fanout.
Chi tiết đọc ODB lưu `build/run12_fanout_odb.json`; ODB gốc được mở read-only.
Báo cáo điện cuối: `59-openroad-stapostpnr/max_ss_100C_1v60/checks.rpt`.

CTS của OpenROAD `edf00dff99f6c40d67a30c0e22a8191c5d2ed9d6` đọc giới hạn
fanout từ **STA Cell của ODB master** và Liberty trong `getBufferFanoutLimit`;
không lấy trực tiếp giới hạn top design ở hàm này. Vì thế chỉ đặt cluster8 và
max fanout10 ở top chưa chặn được các nhánh H-tree 11–15 tải.
Nguồn kiểm tra:
[TritonCTS.cpp](https://github.com/The-OpenROAD-Project/OpenROAD/blob/edf00dff99f6c40d67a30c0e22a8191c5d2ed9d6/src/cts/src/TritonCTS.cpp),
[HTreeBuilder.cpp](https://github.com/The-OpenROAD-Project/OpenROAD/blob/edf00dff99f6c40d67a30c0e22a8191c5d2ed9d6/src/cts/src/HTreeBuilder.cpp).

## Lịch sử bản sửa fanout chuẩn bị cho RUN13

Tag: `picorv32_sobel_dma_clk50_baseline_03`. Chạy lại toàn bộ từ đầu,
không parent/checkpoint, vẫn81 bước chính của Classic.

1. `Sobel.CTSWithFanoutMargin` kế thừa CTS gốc, gọi toàn bộ script CTS cài đặt.
   Ngay khi gọi CTS, đặt max fanout6 lên các ODB clock-buffer master cell.
   CTS dùng mục tiêu này để tạo cây sâu hơn/phân cụm nhỏ hơn khi cần; giới hạn
   CTS_SINK_CLUSTERING_SIZE8 có thể được CTS tự giảm còn6 theo giới hạn cell.
   Sau CTS trả cell limit về10 trước timing/write_views. Không xóa dummy clock load.
2. `Sobel.RepairDesignSlowCorner` vẫn sửa điện tại SS, gọi script post-GRT gốc.
   Khi repair_design chạy, đặt mục tiêu fanout5 ở top để dành ngân sách cho diode.
   Trả về10 ngay sau repair_design, kể cả khi lỗi. Legalization/routing gốc vẫn chạy.
3. Giữ RTL, firmware, SDC, clock50ns, checker, ngưỡng slew/cap và quy trình antenna.
   Không sửa kích thước cell/đấu nối thủ công sau khi antenna đã đóng.

Đây là mục tiêu tối ưu chặt hơn, không phải bảo đảm fanout cuối bằng0. CTS sử dụng
phân cụm hình học; router có thể cần thêm diode. RUN thật phải kiểm tra cả fanout,
antenna, DRC/LVS, setup/hold/slew/cap và thay đổi diện tích/công suất do buffer mới.

## Lệnh Ubuntu hiện hành — RUN15 baseline_05

```bash
bash "/mnt/e/aa. PPA_Project_List/aaa.PicoRV32_Sobel_ASIC_PPA/scripts/00_copy_to_ubuntu.sh"
```
```bash
cd "$HOME/openlane_projects/picorv32_sobel_asic_ppa"
```
```bash
bash scripts/08_run_report_baseline.sh
```
Sau khi kết thúc, kể cả lỗi:
```bash
bash scripts/07_collect_asic.sh picorv32_sobel_dma_clk50_baseline_05
```

Thành công mong đợi: exit0, Antenna/LVS/DRC PASS và fanout/slew/cap/setup/hold0
ở các corner được kiểm tra. Báo cáo power vẫn vectorless; IR drop vẫn có giả định
VSRC_LOC_FILES=None. PPA chỉ gồm physical top đã nêu trong ARCHITECTURE.md.

## Giới hạn kiểm tra trước khi giao chạy

Trợ lý chỉ kiểm tra cấu hình, API, lint, nạp SDC và mock Tcl; không thực hiện CTS,
resizer, routing hoặc simulation. Kiểm tra mock bảo đảm truyền nguyên đối số,
gọi native đúng một lần, khôi phục giới hạn10 cả khi thành công/lỗi và chặn
mục tiêu sai hoặc master không tồn tại. PASS fanout vật lý phải chờ RUN13.

Kết quả precheck thực tế: `build/asic_precheck_MDkR0Bgf` tại Ubuntu — PASS cấu hình81 bước, lint, SDC, API và mock phục hồi constraint. Bốn ZIP benchmark32/64/128/256 được đối chiếu lại golden/hash, không chạy lại simulation. API set_max_fanout lên ODB master clock cũng đã nạp thử trong bộ nhớ, không gọi CTS hoặc write_db. Collector nhận cả tên CTS cũ và wrapper mới, vẫn cần state_out.json để xác nhận CTS đã hoàn tất.

Đối chiếu trực tiếp source_sha256.json của RUN12: **22 file RTL/TB/firmware/third-party/SDC/pin order khớp byte-for-byte** với nguồn chuẩn bị RUN13. Python compile và Bash syntax đạt; tag baseline_03 chưa tồn tại khi bàn giao.

## RUN13 dừng trước CTS — sửa bootstrap cho RUN14

RUN13 `picorv32_sobel_dma_clk50_baseline_03` exit1 tại
`34-sobel-ctswithfanoutmargin`; state cuối hoàn tất là detailed placement33.
Chưa chạy thuật toán CTS, chưa có dữ liệu đánh giá hiệu quả fanout mới.
Evidence đã export: `reports/picorv32_sobel_dma_clk50_baseline_03_collect_20260913T151351104294Z.tar.gz`.

Đối chiếu `_env.tcl` của stage34 cho thấy SOBEL_SCRIPT_DIR đã được Python ghi đúng.
OpenLane TclStep._reroute_env đưa biến custom vào file, không đưa trực tiếp vào môi trường
process. Wrapper đọc biến trước khi source file nên lỗi. Đây là lỗi tích hợp wrapper của
trợ lý; không phải RTL, thiếu RAM hoặc lỗi thuật toán fanout.

Sửa `cts_fanout.tcl` và `repair_design_fanout.tcl`: source `$::env(_TCL_ENV_IN)` trước
khi đọc SOBEL_SCRIPT_DIR. Giữ nguyên phương án fanout6/5, giới hạn kiểm tra10 và81steps.
Bài test `scripts/test_fanout_env.py` dùng chính TclStep._reroute_env cài đặt, tái hiện lỗi
với bản bỏ loader và xác nhận hai wrapper thật nạp thành công sau sửa. Upstream CTS/repair
được thay bằng stub chỉ kiểm tra nạp; không có lệnh vật lý nào được thực thi.

Precheck `build/asic_precheck_PeAmhKU6` tại Ubuntu: config/lint/SDC/API, mock fanout,
kiểm tra serialization của cả hai wrapper và bằng chứng ảnh32/64/128/256 đều PASS.
Precheck này thay cho kết luận kiểm tra bootstrap chưa đầy đủ của phiên trước.

RUN tiếp theo: **picorv32_sobel_dma_clk50_baseline_04 (RUN14)**, launcher08 chạy từ đầu,
không parent/checkpoint. Giữ nguyên RUN12 đã backup và RUN13 lỗi. Chưa có kết quả vật lý
RUN14; sau chạy vẫn phải đọc fanout và toàn bộ checker trước khi kết luận PASS.

## RUN14: trùng tên clock cell; sửa cho RUN15 — 2026-09-14

RUN14 `picorv32_sobel_dma_clk50_baseline_04` exit1 tại đầu CTS34:
`Expected exactly one CTS master: sky130_fd_sc_hd__clkbuf_16`.
Lỗi `_env.tcl` đã được vượt qua. State hoàn tất cuối vẫn là stage33 detailed placement;
thuật toán CTS chưa thực thi nên chưa thể đánh giá phương án sửa fanout.
Archive user đã collect:
`reports/picorv32_sobel_dma_clk50_baseline_04_collect_20260913T152826708591Z.tar.gz`.

Tái hiện với ODB RUN14 và ba thư viện TT/FF/SS cho thấy mỗi clkbuf16/2/4/8 có4
STA Cell cùng tên (3 timing model, 1 physical cell). Kiểm tra cũ chỉ đọc ODB mà
không nạp đủ Liberty nên bỏ sót trường hợp này. Fixture LEF + link_design còn có thể
có5 đối tượng, trong đó2 đối tượng cùng tên thư viện vật lý.

`fanout_policy.tcl` nay chọn cell dựa trên **đối tượng mà ODB master.staCell trỏ tới**,
đồng thời đối chiếu tên cell/thư viện. Với SWIG của OpenROAD đã pin, chỉ so sánh phần
định danh con trỏ được trả về dưới hai kiểu Cell*/void*; không dựng hoặc giải tham chiếu
con trỏ ép kiểu. Guard vẫn yêu cầu duy nhất một liên kết thật, và dừng nếu biểu diễn
API thay đổi hoặc master không tồn tại. Không lấy tùy ý phần tử đầu danh sách.

Kiểm tra đã thực hiện, không chạy PNR/simulation:
- Precheck `build/asic_precheck_d2Icy7F6`: config81step, lint, SDC, API, serialization,
  mock restoration và chọn cell với LEF/thư viện thật đa corner đều PASS.
- `scripts/test_fanout_cells.tcl`: tái hiện guard cũ sẽ lỗi với5candidate; bản mới chọn
  đúng4loại clock master, áp dụng rồi khôi phục SDC fanout; CTS delegate chỉ là stub.
- ODB/SDC RUN14 và đúng ba corner thực tế được nạp read-only: cả4master chọn đúng
  từ4candidate. Log `build/run14_actual_cell_preflight.log` kết thúc
  `RUN14 ACTUAL ODB READ CHECK PASS`. Không CTS, resizer, routing hay write_db.
- Bằng chứng simulation32/64/128/256 vẫn được đối chiếu golden/hash, không chạy lại.

RUN tiếp theo là **picorv32_sobel_dma_clk50_baseline_05 (RUN15)**, full từ đầu qua08,
không parent/checkpoint. Giữ nguyên RUN12/13/14 và bản backup RUN12. Giữ clock50ns,
fanout optimization6/5, signofflimit10, RTL/firmware/config/SDC và tất cả checker.
Đây là sửa lỗi tích hợp chọn cell; PASS fanout/antenna/timing chỉ có thể kết luận sau
RUN15 thực tế. Không gọi precheck là physicalPASS.
