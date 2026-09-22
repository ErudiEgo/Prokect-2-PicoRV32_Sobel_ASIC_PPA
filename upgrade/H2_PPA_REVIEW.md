**Cập nhật: thử nghiệm repair đã chạy và FAIL; xem H2_REPAIR01_REVIEW.md. Kế hoạch dưới đây ghi thời điểm trước RUN.**

# H2 physical RUN01 — chẩn đoán và thử nghiệm sửa, 2026-09-22

**H2 FAIL_OR_INCOMPLETE. Repair hypothesis prepared/static PASS; repair physical NOT_RUN.**

Giữ nguyên archive `s2_ppa_h2_clk50_01_collect_20260922T054005584302Z.tar.gz` trong upgrade/reports, SHA256 `5564b206ce732d49dfe49fce6534b1f260f368f3e41bf9e4219f3ba3acc8282a`. Đã kiểm tra các hash trong READY/source manifest và execution; pair READY hash trùng H1 (`259c3508f0728480157f95cc0bc82d8e94626923f7bbcd3ff29dbae7718f50de`). Raw state_out ở stage79 khớp metrics collector. Dữ liệu thất bại là kết quả thực của cặp baseline, không xóa hoặc đổi thành PASS.

## Kết quả thực

| Đại lượng | H1 RUN01 | H2 RUN01 chưa closure |
|---|---:|---:|
| Standard-cell area (µm²) | 194657 | 341300 |
| Cell count | 26624 | 45891 |
| Core area (µm²) | 437820 | 730358 |
| Die area (µm²) | 461230 | 759937 |
| Setup worst slack (ns) | +30,941661 | +18,641807 |
| Hold worst slack (ns) | +0,110721 | +0,158425 |
| Power vectorless nominal TT (mW) | 6,125478 | 7.749697 |
| Power vectorless max SS (mW) | 5,056986 | 6.440095 |
| Power vectorless max FF (mW) | 7,246052 | 9.199169 |
| Fanout violations | 0 | 6 |
| Capacitance violations | 0 | 1 tại max_ss_100C_1v60 |

H2 area tăng 75.33% ở RUN chưa closure. Đây là trade-off đo được, không phải bằng chứng lỗi RTL hoặc quy toàn bộ phần tăng cho riêng line buffer khi chưa có phân rã area. H2 đã giảm cycles trên characterization nhưng không đồng nghĩa tiết kiệm area/power. Không ghép power vectorless thành năng lượng workload thực.

DRC Magic/KLayout, LVS, XOR, route DRC, antenna 0/0, setup/hold/slew đều đạt kiểm tra hiện có. LVS match 34675 devices/33389 nets mỗi phía. Clock50ns; scope không có external program/frame RAM/pads/package. Host elapsed2924,084s (~48phút44giây), khác progress45:15 và khác thời gian chip.

Flow exit2 vì deferred max-cap error; 81/81 là đã đi tới cuối chuỗi, không phải tất cả kiểm tra đạt. `flow__errors__count=0` trong metrics không thay thế process exit/deferred checker. Không có final/metrics hoặc final GDS; stage GDS vẫn được collector bảo toàn. Không chạy lại để lấy final giả.

## Chẩn đoán theo pin/net/corner

Nguồn: `59-openroad-stapostpnr/max_ss_100C_1v60/checks.rpt`, đối chiếu ODB các stage43/45/47/57 bằng thao tác đọc, không sửa database.

| Driver | Fanout / limit | Diode loads ở stage57 |
|---|---:|---:|
| _37253_/Q (dimensions[29]) | 15 / 10 | 11 |
| _21381_/X | 12 / 10 | 11 |
| _38015_/Q (CPU alu_out_q[4]) | 12 / 10 | 11 |
| wire9729/X | 12 / 10 | 11 |
| _38014_/Q (CPU alu_out_q[3]) | 11 / 10 | 10 |
| max_cap9911/X | 11 / 10 | 8 |

Driver capacitance: `_28633_/Y`, cell `sky130_fd_sc_hd__nor4b_1`, net `_10681_`, một tải logic và không có diode. SS pin limit0,018321pF, actual0,018618pF, slack−0,000297pF (~1,62% vượt). Không được thay bằng global limit0,2pF: giới hạn pin cell chặt hơn vẫn có hiệu lực.

Một số tải diode đã tồn tại ở stage43; stage45 thêm tải trên wire9729 và max_cap9911; sau closure dimensions[29] tăng từ4 lên15 loads do11diode. STA stage46 báo cap0/fanout5; post-PNR STA stage59 báo cap1/fanout6. Các stage không chạy STA có thể kế thừa số cũ, không suy chúng đã đo lại.

Antenna closure đi qua94→8→1→0 net vi phạm. Do đó không xóa diode hoặc tắt antenna để xử lý fanout. Cũng không chỉ tăng cỡ cell rồi coi fanout đã sửa: giới hạn số tải vẫn10.

## Thử nghiệm sửa có kiểm soát

Nhóm B, cấu hình physical mới; giữ H2 frozen RTL/firmware và toàn bộ source/corner/SDC. `physical/prepare_repair_pair.py` dẫn xuất từ pair bất biến, kiểm tra đúng hash archive lỗi, thay **hai tham số optimization ở cả H1/H2**:

- GRT_ANTENNA_MARGIN:30→10. Giả thuyết giảm lượng diode do dự phòng dư; antenna checker vẫn phải0/0. Không phải thay giới hạn DRC/antenna của PDK.
- SOBEL_POST_FANOUT_MARGIN_PCT:70→80. Tăng headroom **slew và cap** ở lượt repair thứ hai trước routing, kỳ vọng chịu được sai khác parasitic sau route. Có thể tăng buffer/area/power.

Đây là thử nghiệm, không cam kết giải hết6fanout/1cap. Diode có thể vẫn được thêm theo cụm hoặc cần nhiều tải để đạt antenna; nếu lỗi giữ nguyên phải chuyển sang phương án cấu trúc net/placement/ECO có kiểm chứng, không lặp giảm/tăng margin vô hạn.

Giữ fanout10, cap0,2pF cùng pin-specific limits, clock50ns, flow81bước, util35/density50, tool/PDK và mọi checker. Không ECO netlist/RTL trong lượt chuẩn bị này. PASS criteria: cap/fanout0, antenna0/0, DRC/LVS/XOR/setup/hold/slew đạt, final views và snapshot integrity; dữ liệu âm được giữ.

Kiểm tra đã chạy: config/lint/SDC cả2variant, multicorner cell lookup với CTS stub, API/env/mock tests, mock margin80 (không gọi repair thật), source-preservation và chống overwrite. Evidence: `build/ppa_repair_static_01`, `build/ppa_repair_prepared_01`. Actual repair flow NOT_RUN.

## Lệnh Ubuntu — chạy H2 sửa trước để kiểm tra giả thuyết

```bash
bash "/mnt/e/aa. PPA_Project_List/aaa.PicoRV32_Sobel_ASIC_PPA/upgrade/scripts/00_copy_to_ubuntu.sh"
```

```bash
cd "$HOME/openlane_projects/picorv32_sobel_stage2"
```

```bash
bash scripts/33_prepare_ppa_repair.sh s2_ppa_pair_clk50_01 s2_ppa_pair_clk50_repair_01
```

Chỉ tiếp tục khi `PPA REPAIR PAIR READY`. Đây là kiểm tra tĩnh/audit; không simulation hay physical run.

```bash
bash scripts/31_run_ppa.sh h2 s2_ppa_h2_clk50_repair_01 s2_ppa_pair_clk50_repair_01
```

```bash
bash scripts/32_collect_ppa.sh s2_ppa_h2_clk50_repair_01
```

Thu/export cả khi lỗi và gửi archive. Full run từ đầu, không resume ngoài kế hoạch. Không chạy lại M3/characterization. Chưa chạy H1 profile mới: review H2 sửa trước; nếu giữ profile mới cho PPA controlled comparison thì cần H1 cùng profile. Không trộn H1 baseline với H2 repair rồi gọi cùng điều kiện.

Giới hạn kế thừa: power vectorless, IR không có nguồn/package thực, EQY skipped, wirelength threshold chưa đặt; không tuyên bố tapeout sign-off. H3/FPGA chưa mở.
