# Hồ sơ tổng hợp để phản biện dự án PicoRV32 xử lý ảnh

Ngày chốt: 2026-09-22, sau H1/H2 physical RUN01 và trước khi người dùng chạy thử nghiệm repair.

Tài liệu này tự chứa bối cảnh, số liệu và các điểm cần phản biện. Đây là bản tổng hợp từ RTL, các biên bản audit và báo cáo thực trong workspace; không tạo kết quả mô phỏng/PPA mới. Mọi giá trị được phân loại: đã đo, đã kiểm tra tĩnh, giả thuyết hoặc kế hoạch. Các tài liệu lịch sử có dòng “chưa chạy/NOT_RUN” ở thời điểm viết; dùng trạng thái ngày chốt trong hồ sơ này khi đánh giá tiến độ hiện tại. Không sửa những snapshot cũ để đồng bộ lời mô tả.

## 1. Mục tiêu, định vị và đích đến

Chủ dự án đã nâng phạm vi từ đồ án sinh viên thành dự án nghiên cứu cá nhân để xây dựng uy tín và hướng tới bài báo khoa học trong nước có chất lượng. Yêu cầu bắt buộc: số liệu thật, nguồn/binary/config gắn với từng RUN, phương pháp công bằng, giữ kết quả âm, không “vẽ số liệu”, không bảo đảm trước khả năng được nhận bài.

Mục tiêu tổng: **kiến trúc SoC/subsystem xử lý ảnh độ phân giải thấp dựa trên PicoRV32 và accelerator**, nghiên cứu offload, di chuyển dữ liệu, local reuse và trade-off tốc độ/tài nguyên. Sobel là operator đầu tiên, không phải sản phẩm cuối cùng.

Ứng dụng dài hạn: xử lý ảnh trên thiết bị yếu, camera giáo dục/đồ chơi hoặc preprocessing nhúng. “480” hiện được cụ thể hóa bằng workload Gray8 480×320, không phải VGA640×480, không phải mọi ảnh có cạnh480 đã được nghiệm thu. Camera hoàn chỉnh còn cần sensor/capture, memory thật, điều khiển, hiển thị/lưu trữ và có thể xử lý màu. Những phần đó chưa tồn tại trong physical top.

Ba đích tách biệt:

1. **Gần hạn — Paper1:** một nghiên cứu tái lập được về software S0/S1 → DMA H1 → line-buffer H2; đo cycles, traffic, latency và PPA cùng phạm vi, giải thích cả chi phí/ca thua. Hoàn thành closure hoặc công khai giới hạn; literature review đánh giá novelty trước tuyên bố đóng góp.
2. **Trung hạn — H3:** tách data movement/window generation khỏi operator, kiểm chứng Sobel rồi thêm một operator khác để chứng minh khả năng tái sử dụng.
3. **Dài hạn — prototype phần cứng và imaging subsystem:** FPGA với CPU boot và bộ nhớ/I/O thật; sau đó mới xem camera/demo hoặc tích hợp ASIC memory/pads. Chưa có silicon, tapeout hay sản phẩm camera.

Paper1 là checkpoint của dự án, không phải bắt buộc đợi H3/FPGA/camera, cũng không phải kết thúc dự án. Lịch 2–3 ngày từng được nêu là kỳ vọng phối hợp, không phải bảo đảm hoàn thành nghiên cứu/publication.

## 2. Phân biệt tên gọi

| Tên | Ý nghĩa | Trạng thái hiện tại |
|---|---|---|
| Stage1 | Giai đoạn nền, gồm lịch sử RTL/firmware và physical RUN16 | Bảo toàn nguyên trạng |
| Stage2 | Workspace nâng cấp độc lập trong upgrade | Đang thực hiện |
| M1/M2/M3… | Milestone công việc/kiểm chứng | Không phải các phiên bản accelerator |
| S0 | Software Sobel gốc chạy RV32 | Có regression lịch sử |
| S1 | Software tối ưu reuse theo chiều ngang | Có regression; không tuyên bố tối ưu tuyệt đối |
| Legacy MMIO Sobel | CPU gửi hàng xóm qua MMIO, core tính kết quả | Tồn tại và được giữ trong top |
| H1 | Sobel tile DMA v1, chưa spatial reuse giữa các output | Functional đạt, physical mới đạt reported checks |
| H2 | Sobel tile DMA v2 với hai line buffer/data reuse | Functional đạt; physical RUN01 FAIL cap/fanout |
| H2 repair | Thay hai tham số tối ưu physical, không đổi thuật toán/RTL | Static PASS; physical NOT_RUN |
| H3 | Hướng accelerator 2D dataflow tách operator | Chưa có spec duyệt/RTL |
| H4/H5/Hn | Chưa có định nghĩa chính thức | Không được mô tả như đã có kế hoạch kỹ thuật chốt |

Chuỗi lịch sử: CPU software → legacy MMIO → H1 DMA → H2 reuse → [dự kiến] H3 dataflow → operator thứ hai → real-memory/hardware prototype → ứng dụng mở rộng.

## 3. Cấu trúc hiện tại đã triển khai

```text
                      PHẦN RTL ĐƯỢC TỔNG HỢP
       +------------------------------------------------------+
       | PicoRV32 RV32I                                       |
       |       | native bus + address decode                  |
       |       +--> legacy Sobel MMIO --> sobel_core           |
       |       +--> tile descriptor/control/status             |
       |                     |                                |
       |             chọn H1 hoặc H2                          |
       |             - H1: read neighbours/FSM/Sobel/write     |
       |             - H2: scan halo/2 line buffers/taps/       |
       |                   FSM/Sobel/write                     |
       |                     | DMA master                     |
       | CPU memory master --+--> native_bus_arbiter --> ext_* |
       +------------------------------------------------------+
                                                        |
                         NGOÀI PHYSICAL TOP             |
                    testbench RAM 1 MiB <---------------+
                    code/stack/input/output + wait model
                    profiler/CSV/events/golden/replay ở host
```

### CPU/bus

- Top chức năng: `candidate/picorv32_sobel_soc_m3.v`; physical wrapper: `picorv32_image_ppa`.
- PicoRV32 RV32I: 32 thanh ghi, register file dual-port, barrel shifter, counters; không bật MUL/DIV, compressed ISA, IRQ hoặc PCPI.
- CPU và DMA chia sẻ native external interface qua arbiter; bus data32 bit, write strobes4 byte; valid/ready. Chưa có AXI/cache/bus64/multiple outstanding được triển khai.
- Wrapper physical nối cổng và đặt literal DMA_VERSION1/2, đảm bảo lint và synthesis chọn đúng H1/H2. Top chứa một tile engine được chọn, không phải hai DMA hoạt động đồng thời.
- Legacy Sobel peripheral vẫn hiện diện ở cả hai top. Cần ghi chi phí này khi giải thích PPA, không gọi số đo là chỉ một Sobel core.

### H1

- CPU thiết lập descriptor tile, khởi động và quản lý completion.
- Tile engine đọc lại các hàng xóm cần cho mỗi output, chạy Sobel, ghi output. Không tái sử dụng spatial window như H2.
- Có overhead instruction fetch, arbitration, register/MMIO, tile/channel loops và warm-up. Đó là một phần phép đo tích hợp, không chỉ số chu kỳ của toán tử.

### H2

- `candidate/sobel_tile_v2.v`, ABI TIL2; H1 dùng TIL1.
- Quét tile cộng halo1 pixel; hai line buffer66 byte và taps cửa sổ3×3. **132 byte là hai dòng**, chưa bao gồm taps/control/CPU registers và không phải toàn bộ memory của hệ thống.
- Đọc mỗi mẫu hợp lệ trong vùng scan một lần; halo giữa các tile vẫn có thể đọc lại. Padding ngoài frame bằng0.
- Mỗi mẫu8bit vẫn sử dụng một read transaction bus32bit. Chưa word packing; không được nói đã sử dụng đủ4byte mỗi giao dịch.
- Chưa tích hợp SRAM macro; buffer có thể được tổng hợp thành FF/mux. Chưa có phân rã area đủ để quy toàn bộ area tăng cho line buffer.
- Chưa tách movement/window/operator thành giao diện generic. H2 **Sobel-specific**.
- Core nhận start ở cạnh N, phát kết quả ở N+1 khi busy; controller còn đọc/ghi/đợi bus. Không suy ra toàn pipeline1pixel/cycle từ latency core.

### Số học và RGB

Sobel lấy8 hàng xóm, bỏ center trong phép tính; Gx/Gy signed11bit, magnitude=|Gx|+|Gy| dùng12bit và saturation255. Không tính căn bậc hai. Zero-padding ở biên toàn ảnh. RGB hiện xử lý từng plane/channel nối tiếp; không phải ISP màu, demosaic, white balance hay một pipeline RGB song song.

S1 tính row pointers và giữ cột cửa sổ theo chiều ngang; chưa reuse toàn bộ giữa các hàng/tile. Cùng hợp đồng volatile memory với S0. Firmware RV32I/ILP32 GCC13.2.0, -O2 và cùng tùy chọn nền; nguồn/binary/build artifacts có manifest.

## 4. Memory: điều đang có và điều chưa có

| Hạng mục | Thực trạng |
|---|---|
| RAM1MiB trong mô phỏng | Model testbench; không nằm trong ASIC |
| Program/data/stack | Trong RAM ngoài của TB; reset PC0, SP0xF000 |
| Input window | 0x10000–0x4FFFF, 256KiB |
| Output window | 0x50000–0x8FFFF, 256KiB |
| Sobel MMIO | Vùng0x40000000..0x400000FF; legacy/tile được decode riêng |
| Host markers | TB nhận log/đo; không phải peripheral sản phẩm |
| H2 local storage | Hai line buffer và taps/control, thuộc physical top |
| SRAM macro/framebuffer/pads/controller DRAM | Chưa tích hợp |
| External ext_* | Interface logic; chưa là giải pháp bộ nhớ/bo mạch hoàn chỉnh |

Phân biệt **capacity**, **bandwidth/latency**, **reuse**. Nới capacity không tự tăng tốc; bus32→64 cũng không tự giải quyết nếu chỉ dùng1byte/read. Không đưa framebuffer hàng trăm KiB/MiB vào standard-cell FF để nói đã có RAM.

Memory map nền có giới hạn gray512×512/RGB256×256, nhưng characterization hiện nghiệm thu các kích thước cụ thể tới gray480×320. Không suy tất cả kích thước/mẫu ảnh đều đã test. RGB480 chưa triển khai/nghiệm thu.

`memory_wait=0` vẫn có bắt tay đồng bộ; không phải RAM0cycle thực. Wait trong TB không đồng nhất với ràng buộc timing I/O của ASIC.

## 5. Tiến độ kiểm chứng và bảo toàn

| Mốc | Kết quả |
|---|---|
| M1 baseline/profile | 3 RUN đạt audit |
| M2 S0/S1/H1 | 6 RUN đạt audit |
| H2 unit | 181 ca đạt bằng chứng RTL |
| M3 integration | 7 workload đạt pixel/tile/profile và source binding |
| Freeze H2 | PASS; local tag/commit/package bất biến |
| Characterization | 10 RUN synthetic đạt:7pilot+3large |
| Physical H1 mới | PASS_FOR_REPORTED_FLOW_CHECKS, có ngoại lệ/giới hạn cần công khai |
| Physical H2 mới | FAIL_OR_INCOMPLETE:1cap+6fanout |
| Repair profile | Chuẩn bị/static PASS; chưa chạy |
| H3/operator thứ hai/FPGA/camera | Chưa triển khai |
| Literature/bản thảo/venue | Chưa hoàn tất; chưa chứng minh novelty |

181unit gồm byte lanes, nhiều mẫu kể cả gradient ít saturation, partial tile/halo, tile64, ảnh hẹp, memory waits, descriptor bounds/overflow, ghi lúc busy, partial MMIO và reset khi đọc/ghi. Regression không chứng minh mọi trạng thái hoặc thay thế formal.

Freeze:
- Tag cục bộ `H2_LINEBUFFER_BASELINE`.
- Commit `a5b8f2317589a90a599ea37d5bc2a782d71e99f0`.
- Parent `e9ff741064810c1ce893745581a2d89917b0b238`.
- Manifest SHA256 `d41639057c7ee48e10f86284a558ad43682fe8c741f1ff3d4e34c2a974299eb6`.
- Package `baseline/H2_LINEBUFFER_BASELINE/`:141source files,17ZIP evidence M1/M2/M3, audit/provenance. Chưa push; không tuyên bố toàn working tree sạch.

Stage1 và RUN cũ không ghi đè. Không generic hóa H2 tại chỗ; H3 phải nhánh/revision riêng sau review.

## 6. Hiệu năng chức năng đã đo

M3/characterization chạy bốn cấu hình: S1 trên topH1, H1, S1 trên topH2, H2. CPU/RAM/ảnh/thuật toán và điều kiện so sánh nhất quán; audit kiểm tra S1 trên hai top có profile bằng nhau. M2 có S0 riêng; không lấy software cycles từ topology cũ để tráo vào phép so sánh mới.

Cửa sổ đo gồm điều khiển/transfer/tile/channel overhead theo marker đã định; boot và host decode/replay ngoài cửa sổ. Profiler quan sát TB, không phải bộ đếm phần cứng đã tích hợp FPGA. Counter CPU/DMA có nhóm chồng lấn, không cộng bừa. Bus read bytes32bit không phải useful/unique image bytes.

### Scaling synthetic, tile32/wait1

| Gray | S1 cycles (cả2top) | H1 cycles | H2 cycles | H1/H2 | S1/H2 | DMA reads H1→H2 |
|---|---:|---:|---:|---:|---:|---|
| 32×32 | 310052 | 68987 | 18044 | — | — | H2=1024 |
| 64×64 | 1247066 | 279162 | 71435 | — | — | H2=4356 |
| 128×128 | 5002475 | 1125450 | 286501 | — | — | H2=17956 |
| 256×256 | 20039142 | 4521530 | 1150057 | 3,931570 | 17,424477 | 521220→72900 |
| 320×240 | 23490947 | 5302041 | 1352571 | 3,919972 | 17,367626 | 611044→85852 |
| 480×320 | 46994735 | 10613703 | 2699463 | 3,931783 | 17,408920 | 1224004→171704 |

Dấu “—” nghĩa bảng không trình bày tỷ số, không phải missing cycles. Bộ input là coordinate-field generator; chưa phải benchmark ảnh tự nhiên đa dạng.

### Tile và memory wait, cùng ảnh64×64

| Tile | Wait | H1 cycles | H2 cycles | H2 reads | First-region H2 cycles |
|---|---:|---:|---:|---:|---:|
| 16 | 1 | 283270 | 80071 | 4900 | 5562 |
| 32 | 1 | 279162 | 71435 | 4356 | 18403 |
| 64 | 1 | 278200 | 68287 | 4096 | 68246 |
| 32 | 0 | 210844 | 58484 | 4356 | 15061 |
| 32 | 3 | 436109 | 104596 | 4356 | 26968 |

Tile lớn giảm halo/overhead nhưng tăng thời gian chờ vùng đầu; vùng đầu có kích thước khác nhau nên không phải cùng một region được trả chậm hơn đơn thuần. RAM chậm làm cycles tuyệt đối tăng dù tỷ số speedup có thể tăng.

### Ca nhỏ/kết quả âm phải giữ

- RGB32: H1=206960, H2=57515cycles, H1/H2≈3,598; DMA reads23436→3468.
- RGB1×1: H1=864, H2=999cycles — H2 chậm hơn.
- RGB1×7: H1=5116, H2=5347cycles — H2 chậm hơn.
- Có ca S1 không thắng S0; không loại các ca đó khỏi công bố.
- Tổng host time của bốn CPU simulations cho ba large RUN≈90,29phút; hai S1 chiếm≈87,19%. Đây không phải latency chip và không phải lý do xóa một đối chứng mà không thay đổi methodology công khai.

Chưa báo FPS thiết bị/camera hoặc năng lượng/ảnh. Chuyển cycles sang thời gian giả định tại clock là tính toán mô hình, không tự trở thành đo camera end-to-end.

## 7. Phương pháp ASIC chung của cặp đã chạy

- OpenLane v2.3.10, flow Classic, **78 bước gốc+3additions=81**, không phải81ca test RTL.
- Image ID `sha256:37c3bd4ea0534a276cb2deb88d601044857bad2807b9bc5b36efe9d02c62624e`.
- sky130A / sky130_fd_sc_hd, Volare `0fe599b2afb6708d281543108caf8310912f54af`.
- Clock50ns, util đặt35%, placement density50%, relative floorplan. Không ép cùng die/core area.
- I/O assumptions max/min5/0,5ns, input transition0,1ns, output load10fF, setup/hold uncertainty0,25/0,10ns. Reset timing đồng bộ; không false path mới.
- Global limits fanout10, slew1,5ns, cap0,2pF; pin-specific Liberty limits vẫn có hiệu lực.
- Chung CPU/legacy peripheral/arbiter/external interface; khác tile engine H1/H2. Không gồm program/frame RAM ngoài, pads/package/camera.
- Hai config chỉ khác wrapper source trong pair baseline. Source packet và 926file PDK được config tham chiếu đã hash; không tuyên bố hash toàn bộ PDK.
- Power vectorless; IR giả định nguồn/tải, chưa VSRC_LOC_FILES/pad/package model.
- Physical source dẫn xuất bỏ timescale CPU,33chú thích style upstream; H2 có2zero-extension tường minh cho sx/sy7→16bit trong so sánh unsigned. Hash và giải thích đã lưu; chưa whole-design formal equivalence.

Phương pháp repair kế thừa từ RUN16/H1, không chứng minh là tối ưu cho cả hai kiến trúc. Một RUN mỗi biến thể không phải thống kê nhiều seed/cấu hình.

## 8. PPA thực và trạng thái H1/H2

| Đại lượng | H1 s2_ppa_h1_clk50_01 | H2 s2_ppa_h2_clk50_01 |
|---|---:|---:|
| Process exit | 0 | 2 |
| Reported status | PASS_FOR_REPORTED_FLOW_CHECKS | FAIL_OR_INCOMPLETE |
| Standard-cell area µm² | 194657 | 341300 |
| Standard-cell count | 26624 | 45891 |
| Core area µm² | 437820 | 730358 |
| Die area µm² | 461230 | 759937 |
| Utilization đo | 44,4604% | 46,7305% |
| Setup worst slack ns | +30,941661 | +18,641807 |
| Hold worst slack ns | +0,110721 | +0,158425 |
| Power nom_tt_025C_1v80 mW | 6,125478 | 7,749697 |
| Power max_ss_100C_1v60 mW | 5,056986 | 6,440095 |
| Power max_ff_n40C_1v95 mW | 7,246052 | 9,199169 |
| VPWR worst drop mV, SS | 0,233237 | 0,196971 |
| VGND worst rise mV, SS | 0,258301 | 0,216140 |
| Host elapsed launcher s | 1543,003 | 2924,084 |
| Final views | Có | Final export bị chặn; stage GDS còn |

H2 area tăng **75,33%**, là số thực của RUN chưa closure. Cần phân rã cell/buffer/mux/descriptor logic/physical overhead trước khi quy nguyên nhân. Power phải so đúng corner; số aggregated7,246/9,199mW không được mặc định gán nominal TT. Không suy Fmax từ slack, không dùng vectorless power×cycles như năng lượng workload thật.

### H1: đạt gì và còn gì?

- DRC Magic/KLayout, LVS, XOR, route DRC, antenna, setup/hold/slew/cap/fanout đạt kiểm tra được báo cáo; fanout0 ở9corners. RUN16 H1 lịch sử còn1fanout, không nhầm với RUN H1 mới.
- Có87mục PASS của collector; không phải87formal proof hoặc full-chip sign-off.
- Raw STA báo2unconstrained endpoints `ext_addr[0]`/`[1]`; final netlist xác nhận cả hai nối tie-low `sky130_fd_sc_hd__conb_1.LO`. Không phải2tín hiệu động thiếu driver; cảnh báo vẫn phải công khai.
- Generated LEF có2output thiếu antenna diffusion; đã đối chiếu hai bit địa chỉ và connectivity. Antenna net/pin checker riêng0/0.
- Raw parasitic unannotated157/corner, filtered0; danh sách clkload/X và HI không dùng của tie cells. Không báo raw0.
- EQY skipped; wirelength threshold checker skipped. LVS không chứng minh RTL→netlist equivalence.
- Cảnh báo GRT no-routing ở intermediate STA; một số LEF58_ENCLOSURE/CUTCLASS không được DRT hỗ trợ. Giữ giới hạn model/tool.
- IR thiếu VSRC_LOC_FILES; không sign-off nguồn thực. Không chip độc lập chứa đủ RAM.

### H2: lỗi thực, không phải chỉ warning

- DRC Magic/KLayout, LVS, XOR, route DRC, antenna0/0, setup/hold/slew đạt.
- **Capacitance1vi phạm tại max_ss_100C_1v60.**
- **Fanout6vi phạm tại9corners.** Log cuối nêu cap vì deferred max-cap checker làm flow exit2; fanout vẫn là lỗi thật dù không có một error cuối tương tự.
- 81/81 là flow đi tới cuối chuỗi, không có nghĩa closure. `flow__errors__count=0` kế thừa trong metrics không phủ định process exit2.
- Collector dùng stage79state_out, không final/metrics; raw/collector đã đối chiếu. Không đổi nhãn FAIL, không giả final GDS.

## 9. H2: bằng chứng chẩn đoán tới driver/net

Đã đọc ODB của các stage43,45,47,57 bằng OpenDB trong container chỉ đọc, không sửa hoặc chạy thuật toán physical.

| Driver | Fanout | Limit | Diode loads ở stage57 |
|---|---:|---:|---:|
| _37253_/Q, H2 dimensions[29] | 15 | 10 | 11 |
| _21381_/X | 12 | 10 | 11 |
| _38015_/Q, CPU alu_out_q[4] | 12 | 10 | 11 |
| wire9729/X | 12 | 10 | 11 |
| _38014_/Q, CPU alu_out_q[3] | 11 | 10 | 10 |
| max_cap9911/X | 11 | 10 | 8 |

Cap lỗi riêng:
- Driver `_28633_/Y`; cell `sky130_fd_sc_hd__nor4b_1`; net `_10681_`.
- Một tải logic, không có diode trên net này.
- Pin limit0,018321pF; actual0,018618pF; slack−0,000297pF, vượt≈1,62%.
- Không nới về global0,2pF để lờ giới hạn Liberty chặt hơn.

Timeline:
- Stage43 đã có một số net fanout cao với nhiều diode.
- Stage45 thêm diode lên wire9729/max_cap9911.
- Stage46 STA: cap0/fanout5.
- Sau native antenna closure, dimensions[29] từ4loads lên15loads, gồm11diode.
- Antenna rounds94→8→1→0 violating nets.
- Stage59 extracted STA: cap1/fanout6. Số metric ở stage không chạy STA có thể là số kế thừa.

Kết luận giới hạn: có chứng cứ tải diode góp phần trực tiếp vào6fanout; lỗi cap là net khác không mang diode. Chưa chứng minh tối ưu margin là đủ sửa, cũng chưa phân rã toàn bộ nguyên nhân area. Không xóa diode để đạt fanout; tăng driver strength đơn thuần không giảm số tải.

## 10. Repair đã chuẩn bị nhưng CHƯA CHẠY — cần phản biện

Nhánh thực nghiệm physical, không phải H3 và không sửa H2 RTL. Script `physical/prepare_repair_pair.py`, wrapper `scripts/33_prepare_ppa_repair.sh`.

| Tham số | Baseline | Experiment | Lý do giả thuyết |
|---|---:|---:|---|
| GRT_ANTENNA_MARGIN | 30 | 10 | Giảm dự phòng để có thể giảm lượng diode |
| SOBEL_POST_FANOUT_MARGIN_PCT | 70 | 80 | Tăng headroom slew/cap của lượt repair thứ2 trước route |

Giữ clock50ns, fanout10, cap0,2pF/pinlimits, density/util, tool/PDK/flow81, RTL/firmware/SDC và mọi checker. Áp dụng hai thay đổi ở cả2config trong packet mới; baseline cũ bất biến.

Đã kiểm tra: nguồn ngoài2config không thay, config/lint/SDC, multicorner lookup với CTS stub, API/env, mock margin80, guard chống overwrite. **Không chạy synthesis/repair/place/route. Static PASS không chứng minh closure.**

Điểm yếu cần phản biện thẳng:
1. Chưa có proof mức30→10 làm giảm được diode trên6net; native repair có thể thêm theo cụm hoặc topology buộc nhiều diode.
2. Tăng70→80 có thể tăng buffers/area/power mà không chữa được pin cap sau route.
3. Đổi2knob cùng lúc là thử nghiệm repair phối hợp, **không phải ablation tách nguyên nhân**. Nếu cần kết luận nhân quả cho paper, phải tách thí nghiệm hoặc không đưa claim đó.
4. Giảm optimization margin không đổi tiêu chí antenna0/0, nhưng có thể khiến antenna không đạt sau route. Không biết trước kết quả.
5. Nếu lỗi giữ nguyên, không lặp chỉnh margin vô hạn; cân nhắc net splitting/placement/targeted ECO hoặc phương pháp repair khác sau khi xác minh connectivity/equivalence và chạy lại đủ checks.

Pair dự kiến `s2_ppa_pair_clk50_repair_01`, RUN thử H2 `s2_ppa_h2_clk50_repair_01`. Người dùng **đang xin đánh giá trước khi chạy**, hồ sơ này không yêu cầu khởi động ngay.

Nếu thử H2 rồi giữ profile mới làm kết quả paper, cần H1 cùng profile cho controlled comparison. Cặp baseline hiện tại vẫn là thí nghiệm hợp lệ nhưng một phía chưa closure; giữ kết quả âm. Không bắt buộc chạy H1 sửa trước khi biết repair H2 có ích.

## 11. Những lỗi/cạm bẫy đã gặp trong chuẩn bị

| Vấn đề | Xử lý/trạng thái |
|---|---|
| Linter OpenLane không chọn DMA qua SYNTH_PARAMETERS như kỳ vọng | Wrapper literal H1/H2; config/lint đã xác minh |
| H2 comparison7bit với16bit gây WIDTHEXPAND | Zero-extension tường minh ở physical-derived source; frozen RTL không đổi; chưa formal toàn design |
| Upstream PicoRV32 style warnings | 33site annotation có danh sách/provenance; không gọi upstream warning-free |
| Test Tcl thiếu SOBEL_SCRIPT_DIR / env leak vào testserialization | Giới hạn env đúng testprocess; negative-control/mock tests đạt |
| Kiểu Path trong resolved config làm inventory PDK rỗng | Serialize đúng, guard reject rỗng;926file được hash |
| RUN16 lịch sử còn1fanout | Công khai; H1 mới0; không xóa evidence RUN16 |
| H2 81/81 nhưng exit2 | Collector giữ FAIL và missing final; đã truy cap/fanout |
| PASS trong collector không bao hết raw warnings | Review bổ sung raw STA/netlist; H1 hai tie-low endpoints được ghi riêng |
| Nhiều tài liệu lịch sử ghi trạng thái cũ | Hồ sơ mới xác định mốc thời gian; không sửa frozen evidence |

Các test mock/host chỉ kiểm tra công cụ, guard hoặc thuật toán host; không được dùng thay CPU RTL execution hay physical closure.

## 12. H3 và các bước sau — gate trước khi mở rộng

### H3: hướng đã thống nhất, chưa specification được duyệt

```text
PicoRV32 → descriptor/control/status
                 |
RAM/interface ↔ read/address engine
                 ↓
          small local buffer
                 ↓
          window generator
                 ↓ valid/ready + window/center/metadata
          operator (Sobel đầu tiên)
                 ↓ valid/ready + result/metadata
             write engine → RAM/interface
```

Read/address engine không biết Gx/Gy. Operator không biết main-memory address/arbiter. Reuse CPU/bus/verification; refactor accelerator có kiểm soát trên branch riêng. Không chỉ thêm OPCODE rồi gọi generic.

Spec phải chốt: payload width/signedness/rounding, window layout, metadata, ownership, valid/ready khi stall, backpressure, reset/abort/flush/done/error, address/stride/alignment/bounds, border/tile/partial/degenerate, ordering, warm-up, latency và buffer budget. Không mặc định read/write đồng thời,1pixel/cycle hay nhiều outstanding.

Gate: **spec → user review → RTL H3 Sobel → bit-exact/regression với H2/golden → đo overhead/reuse/PPA phù hợp**. Generic interface có thể tăng chi phí; phải báo cả overhead.

### Sau H3, chưa đánh số H4/H5

- Một operator thứ hai: ứng viên blur3×3/sharpen/threshold hoặc convolution giới hạn. Chọn theo giả thuyết reuse/chi phí, có golden riêng, không tự mặc định programmable CNN.
- Word packing/useful bytes, overlap/FIFO, bus/memory upgrades: chỉ làm sau profiler xác định bottleneck; không thêm AXI/cache/bus64 theo cảm tính.
- SRAM macro: milestone riêng cần model chức năng, Liberty/corners, LEF/GDS, power/PDN/floorplan và verification. Không gộp vào area baseline hiện tại.
- Các mục này có thể được đặt H4/H5 sau khi scope được duyệt; hiện chỉ là hướng, không phải phiên bản đã hứa sẽ có.

### FPGA: track riêng

- GateA: minimal SoC+BRAM nhỏ, Vivado synthesis/implementation/timing/utilization; dùng reports mới kết luận Basys3 đủ/thiếu. Chưa có kết quả fit.
- GateB: CPU boot thật; PC gửi nhiều ảnh sau một lần nạp bitstream; FPGA xử lý/trả output bit-exact; hardware counters thật. PC không làm operator thay FPGA.
- Tách processing time và communication/end-to-end. LUT/FF/BRAM/DSP không quy sang ASIC area, FPGA Fmax không thay ASIC timing.
- Camera/storage/display là nhánh ứng dụng sau; không để GUI đẹp quyết định ngược lịch xử lý hardware.

## 13. Kế hoạch ưu tiên từ trạng thái này

| Thứ tự | Công việc | Điều kiện đi tiếp |
|---|---|---|
| 1 | Phản biện hồ sơ/repair hypothesis trước RUN mới | Chấp nhận hoặc sửa phương án, không nới checker |
| 2 | Người dùng chạy repair H2 nếu phương án hợp lý | Evidence đúng packet; phân tích lại net/corner và mọi checker |
| 3 | Chốt physical methodology và cặp H1/H2 so được | Cùngscope/corner/flow; công khai violations/negative và trạng thái final |
| 4 | Phân rã area, review fairness và workload | Không suy nguyên nhân chỉ từ tổng area; cân nhắc ảnh thật và ablation có ích |
| 5 | Literature/claim matrix + reproducibility artifact/Paper1 | Mỗi claim truy raw evidence, novelty được so tài liệu đã kiểm chứng |
| 6 | H3 spec rồi review riêng | Không code trước review; baseline H2 giữ nguyên |
| 7 | H3 Sobel rồi operator thứ hai | Bit-exact, stall/reset/border/partial và reuse được chứng minh |
| 8 | FPGA/real-memory hoặc ứng dụng theo scope riêng | Có resource/timing/hardware evidence, không trộn với ASIC |

Không nhất thiết đợi tất cả8bước mới viết bài. Một số nghiên cứu/literature có thể làm song song về mặt kế hoạch; không tự khởi động nhiều track implementation cùng lúc. Không ấn định thời gian hoàn thành closure/publication khi chưa có dữ liệu.

## 14. Rủi ro học thuật và câu hỏi cần ChatGPT phản biện

Đề nghị đánh giá cụ thể, không chỉ động viên:

1. Với CPU+bus+accelerator nhưng external RAM không nằm trong top, nên gọi SoC architecture/subsystem thế nào cho đúng phạm vi?
2. Hai baseline S0/S1 và phép đo S1 trên cả2top đủ công bằng chưa? Còn compiler/volatile/tiling/transfer overhead nào cần công khai hoặc bổ sung?
3. Ma trận synthetic10RUN và regression nhỏ có đủ cho claims hiện tại? Ảnh tự nhiên/ablation nào thêm giá trị nhất thay vì chạy Cartesian product tốn thời gian?
4. H2 area tăng75,33% so lợi ích cycles/traffic có chấp nhận được với mục tiêu thiết bị yếu không? Cần phân rã logic nào trước khi kết luận?
5. Với6fanout do diode và1cap pin-specific, thử margin30→10 và70→80 có căn cứ đủ không? Nên tách từng knob, hay cần chuyển sang xử lý topology ngay? Đề xuất phải giữ checker và evidence.
6. H1 “PASS_FOR_REPORTED_FLOW_CHECKS” cần chú thích gì thêm trước khi dùng trong paper, nhất là tie-low endpoints, unannotated filtering, EQY/IR và tool limitations?
7. Có điểm nào trong số đo power/corner khiến việc so sánh dễ sai? Những claim năng lượng/FPS nào hiện chưa được phép?
8. Đóng góp Paper1 nên nằm ở integration/controlled data reuse/traffic–cycles–PPA trade-off hay cần bổ sung novelty gì? Không mặc định line buffer+RISC-V+Sobel tự đủ mới.
9. H3 có scope tối thiểu nào đủ chứng minh generic2D reuse mà không over-engineering? Operator thứ hai nên chọn bằng tiêu chí nào?
10. Có nên chốt Paper1 trước H3/FPGA? Gate nào thực sự cần, gate nào chỉ làm chậm nghiên cứu?
11. Xin phân loại góp ý: bắt buộc trước RUN repair / trước báo cáo PPA / trước nộp bài / hướng dài hạn. Không yêu cầu rewrite mọi thứ cùng lúc.

Không đề nghị ChatGPT bịa kết quả, bảo đảm acceptance hoặc trích dẫn chưa tra cứu. Literature/venue chưa được tìm kiếm trong lượt tổng hợp này.

## 15. Evidence và cách kiểm tra tiếp

Workspace Windows: `E:\aa. PPA_Project_List\aaa.PicoRV32_Sobel_ASIC_PPA\upgrade`.
Ubuntu: `~/openlane_projects/picorv32_sobel_stage2`.

Tệp quan trọng:
- Direction: `PROJECT_DIRECTION_LOW_RES_IMAGE_SOC.md` (giữ ý định; một số trạng thái trong đó là lịch sử2026-09-21).
- Freeze: `H2_FREEZE_REVIEW.md`, `baseline/H2_LINEBUFFER_BASELINE/`.
- Functional: `M2_M3_UNIT_ACCEPTANCE.md`, `H2_CHARACTERIZATION_PILOT_REVIEW.md`, `H2_CHARACTERIZATION_ACCEPTANCE.md` và ZIP gốc.
- Physical: `H1_PPA_REVIEW.md`, `H2_PPA_REVIEW.md`, `PPA_PREPARATION_REVIEW.md`.
- Current RTL: `candidate/picorv32_sobel_soc_m3.v`, `candidate/sobel_tile_v2.v`, `rtl/sobel_tile.v`, `rtl/native_bus_arbiter.v`, `rtl/sobel_core.v`, `rtl/sobel_mmio.v`.
- Firmware: `firmware/`, `firmware/s1/`, `firmware/h2/`.
- Physical tools: `physical/prepare_ppa.py`, `check_ppa.py`, `ppa.py`, `collect_ppa.py`, `prepare_repair_pair.py`.
- H2 exact raw failure: `59-openroad-stapostpnr/max_ss_100C_1v60/checks.rpt` trong archive.
- Read-only topology evidence: `build/h2_ppa_review_01/h2_net_topology.json`, `odb_inspection.log`.

Archive H1:
`s2_ppa_h1_clk50_01_collect_20260922T043059652673Z.tar.gz`
SHA256 `88da94cfe8298da4984dabe20addbe7e32f216c6adbaad1c4f0ed4f33f1f4cdc`.

Archive H2:
`s2_ppa_h2_clk50_01_collect_20260922T054005584302Z.tar.gz`
SHA256 `5564b206ce732d49dfe49fce6534b1f260f368f3e41bf9e4219f3ba3acc8282a`.

Pair chung `s2_ppa_pair_clk50_01`, READY SHA256 `259c3508f0728480157f95cc0bc82d8e94626923f7bbcd3ff29dbae7718f50de`.

Gói review/repair đã lưu: `reports/s2_ppa_h2_review_and_repair_preparation_20260922_01.zip`; raw physical archives gốc vẫn riêng, không thay thế bằng bản tóm tắt.

Quy tắc vận hành: trợ lý chuẩn bị/sửa code và static/compile/lint/read-only audits; **người dùng chạy RTL simulation/OpenLane/Vivado**. Không rerun để xem report. Tên RUN mới, không overwrite, freeze source/tool/PDK/settings, giữ bằng chứng FAIL. Mọi triển khai H3 cần spec review trước. Lượt này chỉ tổng hợp tài liệu; repair vẫn chưa chạy.
