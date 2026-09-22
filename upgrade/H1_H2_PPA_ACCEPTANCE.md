# H1 / H2 — nghiệm thu PPA và bàn giao 2026-09-23

**H2_ECO_EVIDENCE_AUDIT_ACCEPTED_WITH_LIMITATIONS.** H2 ECO đạt các kiểm tra flow đã báo cáo; đã audit archive, netlist và báo cáo gốc. Đây là mốc nghiên cứu phòng thí nghiệm, không phải tapeout sign-off.

## Kết quả thực tế

| Chỉ số | H1 | H2 sau ECO |
|---|---:|---:|
| Standard-cell area (µm²) | 194,657.000000 | 352,481.000000 |
| Standard-cell count | 26,624.000000 | 47,431.000000 |
| Core area (µm²) | 437,820.000000 | 730,358.000000 |
| Die area (µm²) | 461,230.000000 | 759,937.000000 |
| Worst setup slack (ns) | 30.941661 | 14.336067 |
| Worst hold slack (ns) | 0.110721 | 0.106134 |
| Vectorless power, nom TT 25°C 1,80V (mW) | 6.125478 | 7.807430 |
| Cap / slew / fanout violations | 0 / 0 / 0 | 0 / 0 / 0 |
| DRC / LVS / XOR / antenna | đạt theo audit H1 | đạt theo audit H2 |

Diện tích standard-cell H2/H1 = **1.810780×**, tăng **81.08%**. H2 có slack setup thấp hơn, nhưng vẫn đạt mục tiêu 50 ns. Không suy Fmax đã kiểm chứng từ slack. Không so số tổng power lấy ở các corner khác nhau. Toàn bộ chín corner power nằm trong JSON đi kèm.

## Hiệu năng chức năng đã có

Gray480×320, tile32, memory_wait1: S1 = 46.994.735 cycles; H1 = 10.613.703; H2 = 2.699.463. H1/H2 = **3,931783×**, S1/H2 = **17,408920×**. DMA reads giảm 1.224.004 → 171.704. Đây là ma trận synthetic đã audit, không phải benchmark ảnh tự nhiên mới.

Với giả định clock 50 ns và đúng memory contract của testbench, thời gian tính từ cycles là H1 530,68515 ms và H2 134,97315 ms. Không phải thời gian camera hoàn chỉnh đo trên phần cứng; không nhân vectorless power với thời gian này để công bố energy/frame đo thực. Giữ các ca RGB1×1 và RGB1×7 H2 chậm hơn H1 trong bộ kết quả.

## Bằng chứng đã đối chiếu

- Archive SHA256: `e1ee1a54bed2982dd53fed5d301bb2e95b650bea460354d9deb9b5ce9fb4a112`.
- 133 tệp trong READY và 77 tệp manifest nguồn khớp hash; execution gắn đúng READY và parent repair01. Collector metrics khớp final metrics; 89/89 check PASS.
- 48.052 instance netlist tại checkpoint gốc được giữ nguyên. Sau khi co bốn cạnh buffer không đảo, connectivity của mọi pin instance gốc được giữ; khai báo port và assign không đổi. Không chỉ dựa vào marker PASS trong log.
- Flow thêm đúng 4 buf_8 và 3 diode_2; các instance bổ sung khác là filler/decap. Antenna sau ECO: 2 net/2 pin → 0/0.
- Báo cáo checks.rpt của chín corner: không vi phạm cap/slew/fanout; setup/hold slack đều dương. LVS match uniquely; Magic DRC no errors; KLayout DRC state 0; XOR 0.
- RTL vật lý dùng chung và SDC giữa H1/H2 khớp hash. Resolved config khác đúng wrapper H1/H2 và bốn setting closure nêu dưới.

## Điều kiện so sánh phải công khai

H1 dùng GRT_ANTENNA_MARGIN=30 và SOBEL_POST_FANOUT_MARGIN_PCT=70. H2 parent repair01 dùng 10 và 80, rồi bật SOBEL_ANTENNA_ONLY/SOBEL_OUTPUT_BUFFER_REPAIR cho continuation. Vì vậy đây là so sánh hai implementation đạt constraint với cách closure khác nhau, không phải ablation chỉ thay duy nhất RTL. Nếu bài báo muốn tách riêng tác động kiến trúc khỏi physical optimization, phải thiết kế thêm đối chứng; chưa tự mở thêm RUN.

H2 chạy tiếp từ checkpoint và dùng CTS kế thừa. Runtime 1.337,503878 giây chỉ là continuation, không so với runtime full H1. Các RUN H2 thất bại vẫn giữ nguyên lịch sử. `pair=MISSING` là nhãn không có trong launcher continuation, không phải thiếu parent/hash; không sửa archive đã đóng băng.

## Giới hạn còn lại

- 2 endpoint unconstrained ext_addr[0:1] được truy lại tới conb_1.LO, là tie-low. Hai warning thiếu antenna diffusion information vẫn phải ghi trong phụ lục.
- Mỗi corner có 193 driver chưa annotate thô: 191 clkload và hai chân HI không dùng của tie cell; filtered count = 0. Không báo raw count = 0.
- EQY bị skip. Audit netlist bảo toàn kết nối là kiểm tra cấu trúc, không phải formal sequential equivalence đầy đủ.
- Wirelength threshold chưa đặt; IR không có VSRC_LOC_FILES; power vectorless; cảnh báo unsupported LEF constructs còn tồn tại.
- Scope gồm CPU/accelerator/arbiter/local buffers; external program/frame RAM, controller hiện thực, pads/package không nằm trong số PPA này.
- Docker không khả dụng trong WSL khi audit ngày 23/09; kiểm tra ODB độc lập NOT_RUN. Đã dùng netlist archive đã hash để audit connectivity. Không thay đổi Docker hay khởi động flow.
- Một implementation mỗi phương án, chưa có nhiều seed hoặc đánh giá biến thiên. RGB480, ảnh tự nhiên, FPGA và camera hoàn chỉnh chưa được nghiệm thu.

## Bước kế tiếp

1. Giữ H2 hiện tại làm mốc kết quả; ưu tiên artifact Paper1: bảng đầy đủ mười workload, corner power, kết quả âm và truy xuất nguồn từng claim.
2. Task A: lập ma trận ảnh tự nhiên có nguồn/license/hash, border/arithmetic thống nhất, một golden độc lập và tiêu chí PASS trước khi giao lệnh simulation. Không chạy lại synthetic chỉ để làm đẹp bảng.
3. Task C: soạn và review spec H3 tách engine đọc/window khỏi operator; xác định interface/stall/reset/buffer budget, chọn operator thứ hai để chứng minh reuse. Chưa viết RTL H3 trước review theo chỉ thị dự án.
4. Task D/E (FPGA/camera) là các mốc riêng sau khi chốt scope bộ nhớ và tài nguyên; không coi camera đã hoàn tất nhờ Sobel.

Bản audit ở `build/h2_eco_independent_audit_01/`; gói bàn giao trong `reports/s2_h1_h2_ppa_audit_20260923_01.zip`. Không cần người dùng chạy OpenLane ở bước audit này.
