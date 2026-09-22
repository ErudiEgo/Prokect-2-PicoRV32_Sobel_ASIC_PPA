# H1 physical review — 2026-09-22

**Quyết định: H1_REVIEW_ACCEPTED_FOR_CONTROLLED_H2_COMPARISON.** Giữ nguyên pair `s2_ppa_pair_clk50_01`; bước tiếp theo là người dùng chạy H2. Không sửa RTL, SDC, clock hoặc methodology, không chạy lại H1 để lấy báo cáo.

RUN: `s2_ppa_h1_clk50_01`. Archive: `reports/s2_ppa_h1_clk50_01_collect_20260922T043059652673Z.tar.gz`.
SHA256: `88da94cfe8298da4984dabe20addbe7e32f216c6adbaad1c4f0ed4f33f1f4cdc`.

Đã đọc archive thực, xác minh 108 file trong READY và 70 file trong source manifest; execution liên kết đúng pair/variant H1, source config/wrapper/SDC/launcher khớp bản chuẩn bị đã review. Final metrics khớp collector; có GDS Magic/KLayout. Báo cáo collector có 87 mục PASS. Audit bổ sung đọc raw STA/netlist và ghi ngoại lệ dưới đây. Không thực thi simulation/physical flow.

| Đại lượng | H1 đo từ RUN này |
|---|---:|
| Clock constraint | 50 ns (20 MHz) |
| Standard-cell area | 194657 µm² |
| Standard-cell count | 26624 |
| Core area | 437820 µm² |
| Die area | 461230 µm² |
| Utilization sau flow | 44,4604% |
| Setup worst slack | +30,941661 ns |
| Hold worst slack | +0,110721 ns |
| Corner của hai worst slack trên | max_ss_100C_1v60 |
| Power vectorless nom_tt_025C_1v80 | 6,125478 mW |
| Power vectorless max_ss_100C_1v60 | 5,056986 mW |
| Power vectorless max_ff_n40C_1v95 | 7,246052 mW |
| VPWR worst drop (SS 1,60 V) | 0,233237 mV |
| VGND worst rise (cùng phân tích) | 0,258301 mV |
| Host elapsed launcher | 1543,003 s ≈25 phút43 giây |

Thời gian thanh progress 23:51 có phạm vi khác host elapsed của launcher; không phải latency của chip. Không suy Fmax từ slack. Power phải so đúng corner, không gán số tổng trong collector cho nominal/default corner.

## Kiểm tra và giới hạn

- DRC Magic/KLayout, LVS, XOR, route DRC: 0. LVS match uniquely: 20182 devices, 19520 nets mỗi phía; số device LVS không đồng nhất với số standard cell có physical-only cells.
- Antenna sau detailed route: 0 net/0 pin; `50-openroad-checkantennas-1/reports/antenna.rpt`.
- Setup/hold/slew/cap/fanout: 0 vi phạm tại cả 9 STA corners; setup/hold slack dương. H1 mới có fanout0, trong khi RUN16 lịch sử còn1; không khái quát đây là cải tiến PPA có ý nghĩa thống kê từ một RUN.
- Báo cáo disconnected pins: 0, critical0. Bảng global-route cuối được collector trích có overflow0; đây không phải bản đồ congestion final DRT.
- **Ngoại lệ STA ngoài bảng PASS:** `checks.rpt` tại 9 corner đều báo hai unconstrained endpoints `ext_addr[0]`, `[1]`. Netlist final nối chúng qua net1563/net1564 tới `sky130_fd_sc_hd__conb_1.LO` (tie-low). Đây là các bit địa chỉ cố định0, không phải hai tín hiệu động thiếu driver. Không xóa cảnh báo hoặc thêm false path.
- Generated LEF thiếu antenna diffusion ở hai output này; raw warning chỉ nêu số lượng. Đã đối chiếu LEF và netlist của hai bit; không gọi cảnh báo đã biến mất hoặc dùng nó thay kiểm tra antenna net/pin.
- Raw parasitic report có157 unannotated drivers/corner, filtered0; danh sách gồm clkload/X và hai HI không dùng của tie cells. Giữ raw và filtered riêng, không báo mọi net đều có annotation.
- Yosys.EQY không chạy; WireLength checker bỏ qua vì không có threshold. LVS không thay thế equivalence RTL→netlist.
- GRT no-routing xuất hiện tại intermediate STA; DRT không hỗ trợ một số LEF58_ENCLOSURE/CUTCLASS; đây là giới hạn tool/model còn giữ trong warning log.
- Power vectorless; IR thiếu VSRC_LOC_FILES và pad/package model. Chưa đo năng lượng workload hoặc nguồn trên chip thật.

Phạm vi: CPU + Sobel/MMIO + DMA H1 + arbiter/interface. Không gồm external program/frame RAM, memory controller thực, pads/package/camera/display. Kết luận là đạt các kiểm tra được báo cáo trong flow phòng thí nghiệm, **không full-chip/tapeout sign-off**.

## Bước tiếp theo — Ubuntu, cùng pair đã có

```bash
cd "$HOME/openlane_projects/picorv32_sobel_stage2"
```

```bash
bash scripts/31_run_ppa.sh h2 s2_ppa_h2_clk50_01 s2_ppa_pair_clk50_01
```

```bash
bash scripts/32_collect_ppa.sh s2_ppa_h2_clk50_01
```

Thu archive kể cả flow lỗi; gửi `s2_ppa_h2_clk50_01_collect_*.tar.gz` trong upgrade/reports. Không cần copy/precheck lại, vì pair đã freeze; launcher kiểm tra hash/công cụ/PDK trước chạy. Không nới constraint nếu H2 fail: lấy stage/net/corner để quyết định có cần pair mới.

Sau H2: audit cùng packet, so cell/core/die area, timing và power từng corner; liên kết với cycles/traffic characterization và giữ kết quả bất lợi. Chưa kết luận H2 tốt hơn về area/power.

Evidence review: `build/h1_ppa_review_01/audit.json`, `review_decision.json`, `SUMMARY.txt`, `STA_SUMMARY.rpt`, raw reports và final netlists. Archive gốc không sửa.
