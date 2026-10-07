# Báo cáo kết quả thiết kế hệ thống PicoRV32 tích hợp bộ tăng tốc xử lý ảnh

**Trạng thái tài liệu:** Bản báo cáo kỹ thuật đầy đủ v1.0  
**Ngày tổng hợp:** 2026-10-04  
**Phạm vi:** Các kết quả đã có bằng chứng trong Stage 1, Stage 2, H3 và FPGA Basys3. Tài liệu không nâng trạng thái của các phép thử chưa chạy hoặc chưa đạt.

## Tóm tắt

Báo cáo trình bày quá trình thiết kế, kiểm chứng và hiện thực vật lý một hệ thống xử lý ảnh độ phân giải thấp dựa trên CPU PicoRV32. Nghiên cứu bắt đầu từ phiên bản xử lý hoàn toàn bằng phần mềm, tiếp tục với bộ tăng tốc Sobel H1, kiến trúc H2 có line/window reuse và cuối cùng là H3, trong đó đường di chuyển dữ liệu và sinh cửa sổ 3×3 được tách khỏi toán tử để dùng chung cho Sobel và Box filter. CPU thực thi firmware RV32I thật trong các phép thử; đầu ra được đối chiếu từng pixel với mô hình tham chiếu độc lập. Các RUN và bằng chứng được đóng băng bằng hash để duy trì khả năng truy xuất.

Trên workload Gray 480×320, tile32 và `memory_wait=1`, H2 hoàn thành trong 2.699.463 chu kỳ, nhanh hơn H1 3,931783 lần và nhanh hơn phần mềm S1 17,408920 lần. Số lần đọc DMA giảm từ 1.224.004 xuống 171.704. Đánh giá ASIC H1/H2 bằng OpenLane Classic và SKY130 cho thấy H2 tăng standard-cell area 81,08% nhưng vẫn đạt các kiểm tra timing và physical flow đã audit.

Đối với H3, các workload synthetic và ảnh tự nhiên 480×320 đã được kiểm tra cho Sobel và Box. Bản physical top CPU + H3 đạt closure ở clock period 40 ns, tương đương 25 MHz. Evidence cuối `s2_h3_c40_final_signoff_02` và full-flow `s2_h3_c40_monolithic_06` xác nhận route DRC, disconnected pin, antenna, setup, hold, slew, capacitance, fanout, Magic DRC, KLayout DRC, XOR và LVS đều không có vi phạm theo bộ kiểm tra đã chạy. Worst setup slack là +7,542642 ns và worst hold slack là +0,116533 ns trên chín corner. GDS, LEF, DEF, netlist, SDF, SPEF và SPICE đã được xuất. Kết quả này là OpenLane Classic PASS với các giới hạn được công khai, không phải tuyên bố tapeout công nghiệp.

Trên FPGA Basys3, hệ thống đã chạy ảnh thật qua UART và đối chiếu đúng pixel. RUN11 tiếp tục cải tiến giao thức theo hướng boot một lần, RGB một phiên và CRC/ACK theo block; RTL simulation đã đạt, còn routed timing và board session riêng của RUN11 chưa được ghi nhận trong evidence hiện có.

**Từ khóa:** PicoRV32, Sobel, Box filter, DMA, line buffer, image accelerator, OpenLane Classic, SKY130, FPGA, UART, PPA.

## 1. Tóm tắt kết quả

Đề tài đã xây dựng và kiểm chứng một hệ thống xử lý ảnh dùng CPU PicoRV32, firmware RV32I thực thi thật và các bộ tăng tốc Sobel theo nhiều thế hệ kiến trúc. Hệ thống xử lý ảnh theo vùng, kiểm tra đầu ra từng pixel bằng golden model độc lập và lưu bằng chứng gắn với nguồn RTL, firmware, cấu hình và dữ liệu đầu vào.

Kết quả chính đã đạt:

- Baseline H1 vượt phần mềm S0 khoảng 5,96–6,54 lần trên ba workload M1 đã audit.
- DMA v2 H2 dùng line/window reuse xử lý ảnh xám 480×320 trong 2.699.463 chu kỳ, nhanh hơn H1 3,931783 lần và nhanh hơn phần mềm S1 17,408920 lần trong cùng workload đã định.
- Trên ASIC SKY130, H1 và H2 ECO đều đạt các kiểm tra flow đã audit về timing, cap, slew, fanout, DRC, LVS, XOR và antenna. H2 đổi hiệu năng lấy diện tích: standard-cell area tăng 81,08% so với H1.
- Kiến trúc H3 đã chứng minh khả năng tái sử dụng datapath cho hai toán tử Sobel và Box, xử lý ảnh 480×320 qua RAM hữu hạn và giao tiếp host–UART–CPU–H3 ở mức mô phỏng chân UART.
- Physical top CPU + H3 đã hoàn tất ở 40 ns/25 MHz. Chín corner đều có setup/hold dương và không có slew/cap/fanout violation; route DRC, connectivity, antenna, Magic/KLayout DRC, XOR và LVS đều đạt. Full flow 79 bước cấu hình kết thúc exit code 0 và xuất đầy đủ final views.
- Trên Basys3, RUN10 đã xử lý ảnh thật qua UART ở 921.600 baud và kiểm tra đúng đầu ra từng pixel cho các phiên Gray/RGB được lưu. Tuy nhiên RUN10 không có bằng chứng timing closure, nên chỉ được dùng làm bằng chứng chức năng trên board.
- RUN11 đã đưa vào boot một lần, RGB một phiên và giao thức block UART có CRC/ACK theo block. RTL simulation đã PASS; Vivado timing và board test của RUN11 chưa được xác minh.

## 2. Mục tiêu và phạm vi hệ thống

Mục tiêu của đề tài là thiết kế một SoC nhỏ gồm PicoRV32 và bộ tăng tốc xử lý ảnh, cho phép CPU chạy firmware thật, điều khiển xử lý theo vùng và trả kết quả ảnh qua giao tiếp ngoài. Hai toán tử được dùng trong giai đoạn H3 là Sobel và Box filter. Việc đánh giá gồm ba lớp độc lập:

1. Kiểm chứng chức năng RTL và firmware bằng đối chiếu từng pixel, sự kiện vùng và các trường hợp biên.
2. Đánh giá PPA ASIC bằng OpenLane Classic, PDK `sky130A`, thư viện `sky130_fd_sc_hd`.
3. Thử nghiệm FPGA Basys3 với UART, firmware nạp lúc boot và phần mềm host.

Số liệu ASIC hiện có không bao gồm external program/frame RAM, pad, package hoặc board interface. Vì vậy các số PPA trong báo cáo là PPA của phạm vi logic đã nêu, không phải PPA của một chip hoàn chỉnh có I/O và bộ nhớ ngoài.

## 3. Quá trình phát triển kiến trúc

### 3.1. Baseline S0/H1

S0 là phiên bản phần mềm chạy trên PicoRV32. H1 là bộ tăng tốc DMA thế hệ đầu. Mốc M1 xác nhận CPU thực thi firmware, các phép toán Sobel đúng từng pixel, tile cuối không đầy hoạt động đúng và bộ đo profile không làm thay đổi DUT.

| Workload | S0 (chu kỳ) | H1 (chu kỳ) | Tăng tốc S0/H1 |
|---|---:|---:|---:|
| RGB 32×32, wait1 | 1.352.946 | 206.960 | 6,537234× |
| RGB 17×19, wait3 | 604.553 | 101.421 | 5,960827× |
| Gray 37×35, wait1 | 580.371 | 90.106 | 6,440981× |

Các tỷ số trên chỉ áp dụng cho đúng workload và điều kiện bộ nhớ tương ứng. Chúng không được dùng để suy ra tốc độ cho mọi ảnh hoặc mọi cấu hình bus.

### 3.2. Phần mềm S1 và DMA v2 H2

S1 giảm số lần đọc lặp theo phương ngang ở phần mềm. Kết quả M2 cho thấy S1 cải thiện rõ ở ảnh thông thường nhưng không phải lúc nào cũng nhanh hơn S0: các ca RGB 1×1 và 1×7 là kết quả âm được giữ lại. Điều này cho thấy overhead điều khiển có thể chi phối ở ảnh suy biến hoặc rất nhỏ.

H2 bổ sung line/window reuse trong phần cứng. Ma trận characterization đã kiểm tra ảnh xám tới 480×320 với tile32 và `memory_wait=1`:

| Kích thước | S1 (chu kỳ) | H1 (chu kỳ) | H2 (chu kỳ) | H1/H2 | S1/H2 | DMA reads H1 → H2 |
|---|---:|---:|---:|---:|---:|---:|
| 256×256 | 20.039.142 | 4.521.530 | 1.150.057 | 3,931570× | 17,424477× | 521.220 → 72.900 |
| 320×240 | 23.490.947 | 5.302.041 | 1.352.571 | 3,919972× | 17,367626× | 611.044 → 85.852 |
| 480×320 | 46.994.735 | 10.613.703 | 2.699.463 | 3,931783× | 17,408920× | 1.224.004 → 171.704 |

Kết quả cho thấy lợi ích chính của H2 đến từ giảm lưu lượng đọc DMA nhờ tái sử dụng dữ liệu. Với clock constraint 50 ns và memory contract của testbench, 2.699.463 chu kỳ tương ứng 134,97315 ms. Đây là thời gian suy ra từ chu kỳ mục tiêu, không phải FPS đo trên camera hoặc board.

### 3.3. H3: datapath dùng lại cho nhiều toán tử

H3 tách luồng đọc cửa sổ và datapath điều khiển khỏi operator, cho phép dùng chung hệ thống cho Sobel và Box. Các mốc đã nghiệm thu gồm tile feed/fault, ảnh lớn, word top, reset, UART boot/guard/runtime và host co-simulation.

Thử nghiệm `s2_h3_tilelarge_01` xử lý ảnh 480×320 bằng 1.200 job cho hai toán tử, tạo 307.200 pixel đầu ra đúng. Hệ thống dùng RAM mục tiêu hữu hạn gồm 64 KiB program/data và ba bank ảnh 512 byte; full frame thuộc phía host, không nằm trong target. Khoảng từ word RX đầu tiên tới word TX cuối cùng là 32.111.977 chu kỳ, trong đó tổng H3 busy là 5.311.800 chu kỳ. Phần chênh lệch còn chứa CPU, copy, điều khiển, output và host stalls; không được gọi là chi phí truyền thông thuần.

Mốc Python host/UART RTL đã kiểm tra đường đi hoàn chỉnh ở mức mô phỏng: Python gửi firmware và ảnh Gray 17×19 qua chân UART mô phỏng, PicoRV32 chạy firmware thật, H3 tạo Sobel/Box và dữ liệu quay lại host. Tất cả 8 job và 646 pixel đều đúng. Co-simulation này chưa thay thế bằng chứng serial vật lý, timing FPGA hoặc mapping BRAM.

## 4. Kết quả ASIC

### 4.1. PPA H1 và H2

Hai implementation dùng OpenLane Classic với SKY130. H2 là kết quả ECO/continuation đã audit; đây là mốc nghiên cứu phòng thí nghiệm, chưa phải tapeout sign-off.

| Chỉ số | H1 | H2 sau ECO |
|---|---:|---:|
| Standard-cell area (µm²) | 194.657 | 352.481 |
| Standard-cell count | 26.624 | 47.431 |
| Core area (µm²) | 437.820 | 730.358 |
| Die area (µm²) | 461.230 | 759.937 |
| Worst setup slack (ns) | +30,941661 | +14,336067 |
| Worst hold slack (ns) | +0,110721 | +0,106134 |
| Vectorless power, TT 25 °C, 1,80 V (mW) | 6,125478 | 7,807430 |
| Cap / slew / fanout violations | 0 / 0 / 0 | 0 / 0 / 0 |
| DRC / LVS / XOR / antenna | Đạt theo audit | Đạt theo audit |

H2 có standard-cell area bằng 1,810780 lần H1, tương đương tăng 81,08%. Đổi lại, trên Gray 480×320 H2 giảm 74,57% số chu kỳ so với H1 và giảm khoảng 85,97% số lượt đọc DMA. Power là vectorless; không có dữ liệu chuyển mạch workload thực và không có VSRC location cho phân tích IR. Vì vậy chưa công bố năng lượng trên frame.

So sánh H1/H2 còn có giới hạn phương pháp: hai implementation dùng một số thiết lập closure khác nhau và chỉ có một implementation cho mỗi phương án. Kết quả đủ để báo cáo mốc thực nghiệm hiện tại nhưng chưa phải ablation chỉ thay đổi RTL kiến trúc.

### 4.2. Phạm vi physical top H3

Physical top H3 có tên `picorv32_h3_logic_ppa`. Phạm vi tổng hợp gồm PicoRV32, native bus/arbiter, bộ điều khiển H3, khối đọc và sinh cửa sổ 3×3, Sobel operator, Box operator, write engine và giao diện bộ nhớ ngoài. Top có 108 I/O logic, ngoài hai chân nguồn VPWR/VGND.

Program RAM, image/frame RAM dung lượng lớn, UART, pad, package và camera không thuộc physical top này. Đây là chủ ý thiết kế: bộ nhớ khung hình được đặt ngoài boundary logic thay vì tổng hợp hàng trăm KiB RAM thành flip-flop/mux. Vì vậy kết quả H3 là PPA của **CPU + H3 logic + external-memory interface**, không phải toàn bộ chip có SRAM macro và I/O vật lý.

Constraint cuối của H3:

| Tham số | Giá trị |
|---|---:|
| Clock period | 40 ns |
| Tần số tương ứng | 25 MHz |
| Max fanout | 10 |
| Max transition | 1,5 ns |
| Max capacitance | 0,2 pF |
| PDK / library | sky130A / sky130_fd_sc_hd |
| Flow | OpenLane Classic |

### 4.3. Diễn tiến closure H3

RUN H3 ban đầu đạt setup/hold nhưng còn 133 antenna nets, 166 antenna pins, 27 slew, 101 capacitance và 259 fanout violations. Các RUN sau được dùng để chẩn đoán riêng từng nhóm lỗi thay vì tắt checker. Quá trình closure bao gồm:

1. Giảm fanout bằng buffer tree và ràng buộc fanout nhất quán qua CTS/post-placement.
2. Sửa slew/capacitance bằng các ECO có phạm vi giới hạn, dựa trên net/pin/corner thực tế.
3. Bảo toàn setup/hold trong khi thay đổi placement và routing.
4. Chạy lại DRT, antenna repair, RC extraction và STA chín corner sau mỗi thay đổi vật lý có ảnh hưởng.
5. Xử lý phần đuôi DRC/antenna/electrical theo từng net, không xóa hoặc ghi đè RUN cũ.
6. Chạy final signoff tail để tạo GDS/LEF/SPICE và kiểm tra DRC/LVS/XOR.
7. Chạy `s2_h3_c40_monolithic_06` từ RTL/config đã khóa. Flow dùng hash-gated guided rejoin với checkpoint đã hội tụ, sau đó vẫn thực thi DRT, antenna, fill, RCX, STA và final checks trong cùng RUN.

Mốc C30 RUN209 trước đó chỉ chứng minh routed timing closure và vẫn còn 28 slew, 94 cap, 32 fanout violations. Đây là mốc trung gian, không còn là trạng thái cuối của dự án. Kết quả cuối C40 thay thế nhận định “H3 chưa closure” trong các tài liệu trạng thái cũ.

### 4.4. Timing và electrical closure ở 40 ns

Kết quả STA post-route trên chín corner:

| Corner | Setup slack (ns) | Hold slack (ns) | Setup/Hold violations | Slew/Cap/Fanout |
|---|---:|---:|---:|---:|
| min_ss_100C_1v60 | +10,523479 | +0,700241 | 0 / 0 | 0 / 0 / 0 |
| min_tt_025C_1v80 | +21,270442 | +0,268818 | 0 / 0 | 0 / 0 / 0 |
| min_ff_n40C_1v95 | +24,125165 | +0,127634 | 0 / 0 | 0 / 0 / 0 |
| nom_ss_100C_1v60 | +9,022511 | +0,688969 | 0 / 0 | 0 / 0 / 0 |
| nom_tt_025C_1v80 | +20,967122 | +0,262976 | 0 / 0 | 0 / 0 / 0 |
| nom_ff_n40C_1v95 | +23,919111 | +0,122445 | 0 / 0 | 0 / 0 / 0 |
| max_ss_100C_1v60 | **+7,542642** | +0,676393 | 0 / 0 | 0 / 0 / 0 |
| max_tt_025C_1v80 | +20,691172 | +0,254652 | 0 / 0 | 0 / 0 / 0 |
| max_ff_n40C_1v95 | +23,733656 | **+0,116533** | 0 / 0 | 0 / 0 / 0 |

Worst setup xuất hiện tại max_ss_100C_1v60 và worst hold tại max_ff_n40C_1v95. TNS setup và hold đều bằng 0; số endpoint vi phạm bằng 0 ở mọi corner. Không suy Fmax đã kiểm chứng bằng cách lấy 40 ns trừ slack, vì closure ở một period mới cần flow/STA riêng.

Mỗi corner có raw unannotated count 351 nhưng native filtered count bằng 0. Raw count gồm các net thuộc nhóm được tool lọc theo phương pháp đã lưu; báo cáo không sửa raw count thành 0. Hai endpoint `ext_addr[0]` và `ext_addr[1]` được báo unconstrained ở cả chín corner, nhưng OpenDB read-only proof xác nhận mỗi bit được lái duy nhất bởi chân `LO` của `sky130_fd_sc_hd__conb_1`, giá trị hằng 0. Ngoại lệ này chỉ áp dụng cho đúng hai output trên.

### 4.5. PPA H3 ở 40 ns

| Chỉ số | H3 C40 |
|---|---:|
| Core area | 1.138.870 µm² |
| Die area | 1.176.680 µm² |
| Standard-cell/instance area | 477.911 µm² |
| Instance utilization | 41,9635% |
| Instance count | 64.421 |
| Internal power | 10,107018 mW |
| Switching power | 4,834442 mW |
| Leakage power | 0,000608 mW |
| Total power | 14,942068 mW |
| Routed wirelength | 2.675.321 µm |
| Routed vias | 407.777 |

Power H3 là kết quả theo activity/configured defaults của flow, không có SAIF/VCD workload mới. Vì vậy số 14,942068 mW là power estimate vectorless/tool-default, không phải công suất đo trên silicon và không được kết hợp với chu kỳ chức năng để tuyên bố energy/frame thực nghiệm.

H3 lớn hơn H2 vì phạm vi và mục tiêu khác nhau: H3 chứa infrastructure dùng chung cho nhiều operator và trải qua closure 40 ns với nhiều buffer/diode/timing-repair cell. Không nên dùng tỷ lệ area H3/H2 như một ablation chỉ của “generic operator interface”, vì physical scope, period và closure methodology không đồng nhất hoàn toàn.

### 4.6. Routing, antenna và layout verification

Các chỉ số cuối:

| Kiểm tra | Kết quả |
|---|---:|
| Route DRC errors | 0 |
| Disconnected pins | 0 |
| Critical disconnected pins | 0 |
| Antenna violating nets / pins | 0 / 0 |
| Magic DRC errors | 0 |
| KLayout DRC errors | 0 |
| XOR differences | 0 |
| Illegal overlaps | 0 |
| LVS errors | 0 |
| LVS unmatched nets / pins | 0 / 0 |

Detailed routing hội tụ về 0 DRC ở iteration 25 trong metrics được lưu. Manufacturing summary ghi Antenna, LVS và DRC đều Passed. Final artifacts gồm DEF, Magic GDS, KLayout GDS, LEF, ODB, gate-level netlist, powered netlist, SDC, SDF cho chín corner, SPEF min/nom/max, Liberty views và extracted SPICE.

`s2_h3_c40_final_signoff_02` có SHA-256 `b09bb207be90962139e5bc1fa126c09486aaaed5d05a878d16988358da9555ca`. Trạng thái audit là `C40_FINAL_CLASSIC_SIGNOFF_PASS_WITH_DOCUMENTED_LIMITS`.

`s2_h3_c40_monolithic_06` có SHA-256 `f2e782836919896c9a740b6d05a8f27f82beb15b91d9a0f716c2f983b9e9633`. RUN cấu hình 79 bước, tạo 76 step directories thực tế, exit code 0 sau 2.333,977 s và đạt `C40_MONOLITHIC_79_CLASSIC_PASS_WITH_DOCUMENTED_GUIDANCE`. Số directory khác 79 vì một số bước cấu hình được lồng/skip theo cấu trúc native flow; audit kiểm tra danh sách bước thay vì suy PASS từ phép đếm thư mục đơn giản.

### 4.7. IR drop

IR report chạy ở max_ss_100C_1v60, điện áp 1,60 V:

| Net | Average drop | Worst drop | Tỷ lệ worst drop |
|---|---:|---:|---:|
| VPWR | 47,4 µV | 322,7 µV | 0,02% |
| VGND | 47,9 µV rise | 356,6 µV rise | 0,02% |

Các shape nguồn được tool báo connected. Tuy nhiên `VSRC_LOC_FILES` không có và hoạt động chuyển mạch không lấy từ workload thực. Dự án cũng chưa đặt project-specific silicon acceptance threshold cho IR. Do đó đây là kết quả IR theo giả định nguồn/tải mặc định của flow, có giá trị kiểm tra phòng thí nghiệm nhưng không phải sign-off nguồn của package/silicon cuối.

### 4.8. Ý nghĩa của PASS 40 ns

Kết quả cho phép kết luận rằng implementation CPU + H3 logic đã đạt bộ kiểm tra OpenLane Classic được cấu hình ở 40 ns, gồm timing/electrical chín corner, routing, antenna, DRC, LVS và XOR, đồng thời đã xuất final views. Có thể gọi đây là **H3 C40 physical PASS với giới hạn được công khai**.

Không nên gọi là “tapeout-ready tuyệt đối” vì EQY bị tắt theo policy hiện hành, external RAM/UART/pads/package không thuộc top, power không dùng activity workload, IR không có vị trí nguồn package thực và chưa có silicon measurement. Những giới hạn này không phủ định PASS của phạm vi đã chạy; chúng xác định chính xác ranh giới của kết luận.

## 5. Kết quả FPGA và giao thức UART

### 5.1. RUN10: chức năng thực tế trên Basys3

RUN10 dùng clock hệ thống 50 MHz và UART 921.600 baud. Các artifact board cho thấy host đã nhận và kiểm tra đúng pixel ở nhiều phiên, trong đó:

| Phiên | Kích thước / kênh | Job | Pixel đầu ra | Host wall time |
|---|---|---:|---:|---:|
| `run10_board17x19_01` | Gray 17×19 | 8 | 646 | 4,725 s |
| `run10_gray32_03` | Gray 32×32 | 8 | 2.048 | 11,263 s |
| `run10_rgb64_auto_01` | RGB 64×64, ba phiên kênh | 96 tổng | 24.576 tổng | 137,602 s |
| `run10_rgb128_00000238_01` | RGB 128×128, ba phiên kênh | 384 tổng | 98.304 tổng | 543,066 s |

RUN10 boot lại và truyền riêng từng kênh RGB. Các thời gian trên là thời gian host end-to-end, đã chứa UART và điều khiển; không phải thời gian riêng của H3. RUN10 có negative timing slack theo hồ sơ dự án, do đó không được gọi là FPGA timing PASS dù đã chạy đúng trên board trong các phiên lưu bằng chứng.

### 5.2. RUN11: block UART và RGB một phiên

RUN11 giữ nguyên RUN10 và tạo một giao thức mới với các đặc điểm:

- boot firmware một lần cho toàn phiên RGB;
- ghép ba luồng job R/G/B với ID duy nhất;
- block đầu vào từ 1 đến 128 word;
- CRC32 cho từng block trước khi giải phóng dữ liệu cho CPU;
- ACK `0xA0` kèm sequence 32 bit sau khi block được tiêu thụ;
- DATA output giữ định dạng `0xD0` kèm word/pixel 32 bit.

RTL simulation RUN11 đã đạt `RUN11_BLOCK_SIM_AUDIT_PASS`. Ca hợp lệ kiểm tra RGB 17×19, hai toán tử, 24 job và 1.938 pixel. Các ca CRC sai và block count 0/129 cũng được từ chối đúng. Vivado timing và board test RUN11 vẫn `NOT_VERIFIED`; vì vậy chưa có số đo RX/H3/TX thực tế riêng hoặc speedup end-to-end so với RUN10.

## 6. Phương pháp kiểm chứng và truy xuất bằng chứng

Các PASS trong báo cáo dựa trên archive hoặc artifact thực tế, không dựa chỉ vào thông báo hoàn tất flow. Quy trình kiểm chứng gồm:

- khóa nguồn RTL, firmware, input và cấu hình bằng SHA-256;
- dùng PicoRV32 chạy firmware thay vì thay CPU bằng mô hình hành vi;
- kiểm tra từng pixel với golden model độc lập;
- kiểm tra tile/job, transaction, stall, counter và trường hợp biên;
- tách target cycles khỏi wall-clock simulation;
- giữ các ca âm và các RUN thất bại để tránh lựa chọn kết quả có lợi;
- phân biệt testbench/host software với phần cứng synthesizable.

### 6.1. Golden model và kiểm tra pixel

Sobel dùng cửa sổ 3×3, tính gradient theo hai hướng, lấy độ lớn theo arithmetic đã khóa và bão hòa về 8 bit. Box filter lấy trung bình cửa sổ theo quy tắc làm tròn đã định trong checker. Border handling, tile halo, địa chỉ nguồn/đích và byte strobe được giữ giống nhau khi so sánh các biến thể.

Checker không chỉ tìm marker “CPU complete”. Nó kiểm số lượng pixel, tọa độ, giá trị, thứ tự tile/job, vùng partial, guards của bộ nhớ, transaction bus và timestamp. Ảnh output chỉ được tạo sau khi toàn bộ pixel đã qua kiểm tra.

### 6.2. Phân biệt các loại thời gian

- `target cycles`: số chu kỳ trên thiết kế, dùng để so kiến trúc khi cùng clock/memory contract.
- `cycles × period`: thời gian suy ra ở clock đã nêu, không phải phép đo silicon.
- `simulation wall seconds`: thời gian simulator chạy trên máy host.
- `host session wall time`: thời gian PC gửi/nhận trong phiên UART thực hoặc mô phỏng.
- `H3 busy cycles`: thời gian accelerator bận; không tự bao gồm toàn bộ boot/RX/TX.

Các đại lượng trên không được cộng hoặc thay thế nhau nếu cửa sổ đo chồng lấn.

### 6.3. Đóng băng và audit

Mỗi RUN quan trọng lưu snapshot nguồn, firmware, input, command, tool/environment metadata và SHA-256. Audit đọc lại evidence gốc, tính lại metric và pixel khi có thể mà không chạy lại flow chỉ để thu báo cáo. RUN lỗi được giữ để truy vết tiến trình closure; RUN đạt không ghi đè RUN trước.

Các tài liệu bằng chứng chính:

- `M1_ACCEPTANCE_REVIEW.md`: baseline S0/H1.
- `M2_M3_UNIT_ACCEPTANCE.md` và `H2_FREEZE_REVIEW.md`: S1, DMA v2 unit và baseline H2.
- `H2_CHARACTERIZATION_ACCEPTANCE.md`: ma trận kích thước và Gray 480×320.
- `H1_H2_PPA_ACCEPTANCE.md`: PPA ASIC H1/H2.
- `H3_TILELARGE_ACCEPTANCE.md`: ảnh 480×320 qua RAM hữu hạn.
- `H3_WORDTOP_ACCEPTANCE.md`, `H3_UARTBOOT_ACCEPTANCE.md`, `H3_UARTGUARD_ACCEPTANCE.md`, `H3_UARTRUNTIME_ACCEPTANCE.md`: tích hợp và phục hồi UART/reset.
- `H3_HOSTCOSIM_ACCEPTANCE.md`: Python host ↔ UART RTL ↔ PicoRV32 ↔ H3.
- `fpga/basys3/runs/s2_basys3_11/SIM_ACCEPTANCE.json`: cổng simulation RUN11.
- `fpga/basys3/reports/`: các session board RUN10.
- `reports/s2_h3_c40_final_signoff_02_evidence.zip`: final H3 C40 signoff tail và final views.
- `reports/s2_h3_c40_monolithic_06_evidence.zip`: full Classic flow từ RTL với guided routed-checkpoint rejoin.

## 7. Thảo luận

### 7.1. Hiệu năng và lưu lượng bộ nhớ

Kết quả H1→H2 cho thấy tối ưu quan trọng nhất không nằm ở phép nhân/cộng của Sobel mà ở giảm đọc lặp từ bộ nhớ. Trên Gray 480×320, DMA reads giảm 85,9719% và cycles giảm 74,5662%. Đây là bằng chứng thực nghiệm cho hướng dùng line/window buffer trong accelerator ảnh 2D.

H3 không được thiết kế chỉ để thắng H2 về chu kỳ Sobel. Matched pilot cho thấy ở các ca nontrivial ban đầu, H3 có CPU-frame overhead 7,12–38,86% so với H2 dù traffic bằng nhau. Profiling xác định phần lớn delta nằm ở các chu kỳ không phát DMA request, liên quan tới control/handshake và backpressure. Đổi lại, H3 tách operator khỏi data movement và đã dùng cùng hạ tầng cho Sobel lẫn Box. Đây là trade-off giữa khả năng tái sử dụng kiến trúc và overhead điều khiển, cần được trình bày trung thực.

### 7.2. Đóng góp của đề tài

Các đóng góp kỹ thuật đã chứng minh gồm:

1. Xây dựng SoC PicoRV32 chạy firmware thật để so phần mềm và accelerator trong cùng môi trường.
2. Thiết kế H1 và H2, định lượng tác động của data reuse bằng cycles và traffic thay vì chỉ mô tả định tính.
3. Xây dựng H3 với window/data movement dùng lại cho nhiều toán tử.
4. Kiểm chứng theo chuỗi từ unit, CPU integration, ảnh lớn, ảnh tự nhiên, reset, UART đến host co-simulation và FPGA.
5. Hoàn tất physical implementation CPU + H3 tại 40 ns trên SKY130 với timing/electrical/layout checks sạch trong phạm vi đã định.
6. Duy trì evidence package có hash, raw reports, final views và các kết quả âm để tăng tính tái lập.

### 7.3. So sánh ASIC và FPGA

ASIC và FPGA trả lời hai câu hỏi khác nhau. ASIC H3 C40 chứng minh khả năng hiện thực logic trong SKY130 ở constraint 25 MHz và cung cấp area/power/timing/layout reports. FPGA chứng minh firmware, UART và image path có thể vận hành trên phần cứng lập trình được. LUT/FF/BRAM không được quy đổi thành µm² ASIC; clock FPGA không được dùng làm clock ASIC; board wall time không được dùng thay H3 busy cycles.

## 8. Giới hạn và công việc chưa hoàn tất

- PPA H1/H2 không gồm external RAM, pad, package và giao tiếp board.
- Power ASIC hiện là vectorless; IR thiếu mô hình nguồn/vị trí thực tế.
- H3 ASIC đã đạt C40 physical PASS trong phạm vi CPU + H3 logic. Tuy nhiên external RAM, UART, pads/package và camera chưa nằm trong physical top.
- EQY không được chạy; connectivity/layout/netlist checks hiện có không thay thế formal sequential equivalence đầy đủ.
- Hai output hằng `ext_addr[0:1]` được chứng minh tie-low bằng OpenDB nhưng vẫn xuất hiện là unconstrained trong check_setup.
- Raw unannotated count là 351 mỗi corner; native filtered count bằng 0. Hai số phải được báo cùng nhau.
- RUN11 chưa có routed timing, resource mapping hoặc board evidence.
- Chưa có số đo năng lượng thực, camera pipeline hoàn chỉnh hoặc RGB480 được nghiệm thu theo cùng đường dữ liệu.
- Wall-clock simulation phụ thuộc máy host và không được dùng thay target cycles.
- Kết quả từ ảnh synthetic hoặc một số ảnh thật đã chọn không chứng minh chất lượng thị giác trên mọi tập dữ liệu.

## 9. Kết luận

Đề tài đã hoàn thành chuỗi nghiên cứu từ baseline phần mềm, tăng tốc H1, tối ưu tái sử dụng dữ liệu H2, đến kiến trúc H3 đa toán tử và prototype FPGA/UART. Kết quả nổi bật ở cấp kiến trúc là H2 đạt tăng tốc 17,408920 lần so với S1 trên Gray 480×320 trong điều kiện kiểm thử đã khóa, với DMA reads giảm 85,9719% so với H1. H3 mở rộng đường dữ liệu dùng chung cho Sobel và Box, được kiểm chứng trên ảnh synthetic và ảnh tự nhiên 480×320, đồng thời hỗ trợ boot/UART/reset/host co-simulation theo các mốc riêng.

Kết quả nổi bật ở cấp hiện thực vật lý là H3 C40 đạt OpenLane Classic PASS tại 40 ns/25 MHz: setup, hold, slew, capacitance và fanout sạch ở chín corner; routing DRC, disconnected pins, antenna, Magic DRC, KLayout DRC, XOR và LVS đều bằng 0; final GDS và các view phục vụ phân tích tiếp theo đã được tạo. Worst setup slack là +7,542642 ns và worst hold slack là +0,116533 ns. Đây là kết quả hoàn chỉnh cho phạm vi CPU + H3 logic đã khai báo, với các giới hạn về RAM/UART/pad/package, EQY, vectorless power và IR assumptions được giữ công khai.

RUN10 FPGA chứng minh hệ thống có thể vận hành trên Basys3 với ảnh thật và đối chiếu từng pixel. RUN11 đã hoàn thiện thiết kế giao thức boot một lần, RGB một phiên, CRC và ACK theo block ở mức RTL simulation; phần đo RX/H3/TX và board closure của RUN11 là phần tiếp tục, không ảnh hưởng đến kết luận ASIC C40 đã đạt.

Phần tiếp theo nên tập trung vào hoàn tất RUN11 trên Vivado và board, đo riêng RX/H3/TX bằng timestamp/counter có cửa sổ xác định rõ, tích hợp memory macro hoặc memory subsystem phù hợp nếu mở rộng physical scope, và chuẩn hóa hình ảnh/layout/bảng số liệu cho luận văn hoặc bài báo.

## Phụ lục A. Bảng trạng thái kết quả

| Hạng mục | Trạng thái | Bằng chứng chính |
|---|---|---|
| PicoRV32 firmware + Sobel baseline | PASS | Stage 1 functional archives |
| M1 S0/H1 | PASS | `M1_ACCEPTANCE_REVIEW.md` |
| M2 S1 | PASS, có ca âm | `M2_M3_UNIT_ACCEPTANCE.md` |
| H2 DMA v2 unit/integration | PASS | `H2_FREEZE_REVIEW.md` |
| H2 characterization tới Gray480×320 | PASS | `H2_CHARACTERIZATION_ACCEPTANCE.md` |
| H1/H2 ASIC | PASS với giới hạn | `H1_H2_PPA_ACCEPTANCE.md` |
| H3 Sobel + Box functional | PASS | workload/natural acceptances |
| H3 finite-memory tilelarge | PASS | `H3_TILELARGE_ACCEPTANCE.md` |
| H3 UART boot/guard/runtime/hostcosim | PASS theo các ca đã chạy | các H3 UART acceptance |
| H3 ASIC 40 ns | PASS với giới hạn công khai | final_signoff_02 + monolithic_06 |
| FPGA RUN10 board function | PASS theo các session lưu | `fpga/basys3/reports` |
| FPGA RUN11 RTL block protocol | PASS | `SIM_ACCEPTANCE.json` |
| FPGA RUN11 routed timing/board | NOT_VERIFIED | chưa có evidence tương ứng |

## Phụ lục B. Quy tắc sử dụng số liệu

- Không gọi simulation wall time là chip latency.
- Không gọi vectorless power là công suất workload đo thực.
- Không nhân power estimate với cycles để công bố energy/frame nếu activity và scope không khớp.
- Không dùng Sobel-only hoặc CPU+H3-logic PPA làm PPA của chip hoàn chỉnh.
- Không dùng flow completion thay cho DRC/LVS/antenna/timing reports.
- Không dùng FPGA resources làm ASIC area.
- Không bỏ kết quả âm hoặc warning/exceptions có ảnh hưởng đến phạm vi kết luận.
