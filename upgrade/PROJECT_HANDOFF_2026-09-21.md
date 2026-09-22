# Bàn giao dự án để thảo luận — 2026-09-21

Tài liệu tự chứa, tổng hợp từ hồ sơ dự án và audit bảy ZIP M3 xuất bởi người dùng. Không triển khai bước mới, không chạy lại simulation/OpenLane. Các khuyến nghị là đề xuất để thảo luận, chưa phải chỉ thị thực hiện. Tài liệu trạng thái cũ giữ nguyên để bảo toàn lịch sử; dùng tài liệu này khi trao đổi trạng thái hiện tại.

## 1. Mục tiêu và phạm vi

Dự án cá nhân phát triển SoC PicoRV32 RV32I tích hợp bộ tăng tốc Sobel, hướng tới bài báo khoa học nghiêm túc tại trường đại học/tạp chí chuyên ngành trong nước và xây dựng uy tín cá nhân. Cần số liệu thật, tái lập được, công khai kết quả âm và hạn chế. Chưa chọn nơi gửi bài, chưa chứng minh novelty và chưa bảo đảm được chấp nhận.

Bài đầu tập trung vào bộ xử lý ảnh và hệ thống RV32. Camera đồ chơi là nhánh phát triển sau: còn thu nhận ảnh, giao tiếp camera, lưu trữ, hiển thị, điều khiển, xử lý định dạng/màu và đo camera-to-display. Hiện chưa có sản phẩm camera hoàn chỉnh, FPGA demo vật lý hay chip silicon stage2.

Định hướng ảnh nhỏ có cạnh dài tối đa480. Lộ trình trước giả định mỗi chiều<=480; 480×320 là workload ứng dụng đề xuất, 480×480 kiểm tra giới hạn. Không đồng nhất với VGA640×480/480p. Mục tiêu10fps từng được nêu như ngân sách thiết kế có điều kiện, chưa được cam kết/đạt. Người dùng cần chốt lại kích thước, gray/RGB và yêu cầu tốc độ nếu muốn biến chúng thành tiêu chí nghiệm thu.

## 2. Tổ chức, workflow và kỷ luật

- Windows gốc/stage1: E:\aa. PPA_Project_List\aaa.PicoRV32_Sobel_ASIC_PPA.
- Mọi thay đổi stage2 nằm trong upgrade; stage1 và RUN16 bảo toàn.
- Ubuntu stage2: ~/openlane_projects/picorv32_sobel_stage2.
- Bằng chứng người dùng chạy được export về upgrade/reports; tuyệt đối không ghi đè RUN/archive cũ.
- Trợ lý viết RTL/firmware/TB/checker/scripts, compile/lint/static và audit evidence. Người dùng nhập lệnh chạy RTL simulation và OpenLane. Không tự chạy nặng, không tự đổi OpenLane Classic sang ORFS.
- Nền tảng vật lý: SKY130 sky130A / sky130_fd_sc_hd. Trước RUN vật lý mới phải xác minh phiên bản tool/PDK, clock, constraints và phạm vi top.
- Mỗi RUN đóng băng nguồn/firmware/input/checker, hash, version tool, log, exit code, kết quả pixel/tile/profile. Sai thì chẩn đoán từ evidence, không tắt checker hoặc sửa số đo để PASS.

## 3. Kiến trúc và phép toán đang có

PicoRV32 RV32I -> MMIO điều khiển Sobel/DMA; CPU và DMA tranh chấp bus bộ nhớ native32bit qua arbiter. Program/image/output RAM nằm ngoài top và được testbench mô hình hóa. CPU thực thi binary RV32 trong mô phỏng RTL, không phải host Python chạy thay CPU. Chưa là thử nghiệm trên silicon.

Phép toán: Sobel3×3, magnitude=min(255,abs(Gx)+abs(Gy)), zero-padding tại biên toàn frame. Tile không tạo biên zero riêng; cần halo từ các tile lân cận. RGB hiện xử lý tuần tự từng mặt phẳng R/G/B rồi tạo ảnh biên màu, không phải RGB->gray->Sobel. Sự kiện hoàn thành tile chỉ phát sau khi đủ các kênh.

Các biến thể:

- S0: phần mềm gốc, bảo toàn làm đối chứng lịch sử.
- S1: phần mềm dùng row pointers và trượt cửa sổ ngang để tái sử dụng cột; vẫn RV32I, cùng compiler/options -O2 và volatile memory contract. Chưa tuyên bố là software tối ưu tuyệt đối.
- H1: DMA v1, đọc lại các hàng xóm cần thiết cho mỗi output. Mỗi read bus32 chọn một byte; chưa tận dụng các byte còn lại. ABI TIL1.
- H2: DMA v2 quét tile+halo, hai line buffer66byte, cộng taps và FSM; tái sử dụng dữ liệu trong tile. Hai line buffer tổng132byte, KHÔNG phải tổng RAM của hệ thống. Vẫn một mẫu byte mỗi read bus32, halo giữa tile có thể đọc lại. Core Sobel đa chu kỳ giữ nguyên; chưa phải1pixel/cycle. ABI TIL2.

SoC M3 chọn DMA_VERSION1 hoặc2 lúc elaboration; chỉ một DMA engine trong mỗi cấu hình. Bốn lần thực thi mỗi workload: s1_v1, h1, s1_v2, h2. CPU/arbiter/RAM/input/tile/wait giữ nguyên, khác accelerator. S1 dùng cùng binary trên cả hai để kiểm tra ảnh hưởng của DMA nghỉ. Không gọi v1/v2 là hai phần cứng hoàn toàn giống nhau.

Firmware: S0=1772byte, H1=804byte, S1=1500byte, H2=808byte. RV32I/ILP32 GCC13.2.0, cùng nhóm flags nền. Build S1/H2 đã rebuild S0/H1 và khớp byte với HEX bảo toàn. H2 phát triển từ H1 với ID TIL2 và identity3; trình tự điều khiển/thuật toán được giữ. Manifest và build_evidence.zip liên kết source/HEX/ELF/disassembly/options.

## 4. Các mốc đã làm

| Mốc | Trạng thái xác minh |
|---|---|
| Stage1/RUN16 | Có baseline vật lý lịch sử, còn giới hạn sign-off bên dưới |
| M0 | Workspace upgrade và baseline archive/hash đã có |
| M1 | Ba workload nền đã nghiệm thu; profiling transactions/cycles/tile |
| M2 | Sáu workload S0/S1/H1 đã audit đạt; baseline software mạnh hơn |
| M3 unit | DMA v2 đạt181 ca unit, biên/tile/lane/stall/reset/descriptor guards |
| M3 integration | Bảy workload SoC đã audit đạt, đúng pixel/tile/profile và nguồn/firmware |
| M4 | Chưa kiểm chứng workload480; RGB480 chưa triển khai |
| M5 | Chưa có OpenLane/PPA mới cho stage2/H2 |
| M6 | Chưa hoàn tất related work, novelty, lựa chọn nơi gửi hoặc bản thảo |

M3 integration đạt bộ regression đã định, không phải chứng minh toàn bộ không gian trạng thái, formal verification hoặc full-chip sign-off. Chưa có kiểm chứng workload ảnh480 và khảo sát tham số đủ cho bài báo.

## 5. Kết quả M3 đã audit từ ZIP

S1 có cùng chu kỳ và toàn bộ profile trên v1/v2 cho cả bảy workload. Các tỷ số dưới đây là tỷ số chu kỳ trong cùng điều kiện workload, không phải tốc độ ASIC đã đo.

| Ảnh | Tile/wait | S1 cycles | H1 cycles | H2 cycles | H1/H2 | S1/H2 | DMA reads H1→H2 |
|---|---|---:|---:|---:|---:|---:|---|
| Gray 37×35 | 16/1 | 421749 | 90106 | 27688 | 3.254334 | 15.232194 | 9932→1599 |
| Gray 64×64 | 64/1 | 1221362 | 278200 | 68287 | 4.073982 | 17.885718 | 32004→4096 |
| Gray 9×1 | 16/1 | 3834 | 1134 | 1076 | 1.053903 | 3.563197 | 16→9 |
| RGB 17×19 | 16/3 | 430613 | 101421 | 30762 | 3.296957 | 13.998212 | 7116→1197 |
| RGB 1×1 | 1/0 | 2414 | 864 | 999 | 0.864865 | 2.416416 | 0→3 |
| RGB 1×7 | 2/3 | 21378 | 5116 | 5347 | 0.956798 | 3.998130 | 36→39 |
| RGB 32×32 | 16/1 | 959301 | 206960 | 57515 | 3.598366 | 16.679145 | 23436→3468 |

Kết quả âm cần giữ: H2 dùng nhiều chu kỳ hơn H1 ở RGB1×1 (999 so với864) và RGB1×7 (5347 so với5116). V1 không đọc center cho Sobel1×1, còn H2 vẫn nạp mẫu/khởi động cửa sổ. Dữ liệu traffic xác nhận trường hợp này không giảm read; overhead cụ thể muốn phân rã cần thêm phân tích trace. Không tuyên bố H2 luôn nhanh hơn.

Ở M2, S1 cũng chậm hơn S0 ở RGB1×1/1×7; S1 nhanh hơn S0 khoảng1,61–1,70× ở ba ảnh2D RGB17×19/RGB32/gray37×35. Không lấy số SW M1 làm S0 M2: M1 SW bỏ accelerator/arbiter còn M2 dùng hardware accelerator-present để so sánh công bằng hơn.

Cửa sổ đo gồm xử lý ảnh, instruction fetch trong cửa sổ, MMIO/control, transfer, output và tile events. Boot, host decode và replay nằm ngoài. Có first/last-region latency và CPU/DMA/bus counters trong evidence; các counter wait/busy có thể chồng lấn, không cộng tùy ý. Wall-clock simulation time không phải target execution time. Chưa dùng clock vật lý mới để tính FPS/energy.

## 6. Stage1/RUN16: có gì và không có gì

Theo hồ sơ RUN16_REVIEW.md, RUN picorv32_sobel_dma_clk50_baseline_06 hoàn tất OpenLane Classic81stage, exit0. Antenna/LVS/DRC/setup/hold/slew/cap đạt các kiểm tra đã chạy; vẫn còn1fanout violation: actual11, limit10, net có một buffer load và mười diode chống antenna. Collector giữ FAIL_OR_INCOMPLETE. Không gọi full sign-off/tapeout.

Instance area195012µm², không phải die area. Clock constraint50ns=20MHz, không phải50MHz và không tự là Fmax. Physical top gồm CPU, Sobel legacy, tile DMA/core và arbiter; loại trừ external program/image/output RAM, pads/package. Power vectorless; IR phụ thuộc giả định vị trí nguồn/tải. Dữ liệu antenna/PDK/parser và một số check thiếu được ghi trong RUN16_REVIEW.md.

Những số này thuộc DMA v1 stage1. Không ghép diện tích/power RUN16 với cycles H2 để báo PPA hoặc năng lượng H2. Flow78/81bước là quy trình triển khai vật lý, khác các ca kiểm thử chức năng RTL đang chạy.

## 7. Bộ nhớ và mục tiêu480 — điểm quyết định tiếp theo

Hiện gray<=512×512, RGB<=256×256; tile<=64. Input0x10000–0x50000 và output0x50000–0x90000, mỗi vùng256KiB. Giới hạn dimension không có nghĩa đã test mọi kích thước. V2 kiểm tra cả phạm vi frame suy ra từ origin/stride trước start. Bộ nhớ testbench không phải RAM silicon đã tích hợp.

| Frame | Gray8 một frame | RGB888 một frame | RGB input+output |
|---|---:|---:|---:|
| 320×240 | 75KiB | 225KiB | 450KiB |
| 480×320 | 150KiB | 450KiB | 900KiB |
| 480×480 | 225KiB | 675KiB | 1350KiB |

Chưa gồm program/stack/descriptors/double buffering. Gray480 vừa các vùng hiện tại; RGB480×320/480×480 không vừa một vùng256KiB. RGB320×240 về dung lượng một frame có thể vừa, nhưng firmware/checker đang giới hạn mỗi chiều256 nên hiện vẫn không được hỗ trợ.

Hai hướng mở RGB480: mở memory map/các guard/firmware/TB theo dung lượng mới, tiếp tục công khai external RAM; hoặc chuyển stream/strip với ownership/backpressure/halo rõ ràng. Hướng sau mở rộng nghiên cứu và công việc lớn hơn. Chưa tự chọn hoặc triển khai.

## 8. Kế hoạch đề xuất để thảo luận, chưa thực hiện

1. Chốt phạm vi bài đầu: SoC subsystem + external memory interface, Sobel gray/RGB như hiện tại; hay bắt buộc RGB480/camera. Đề xuất giữ bài đầu hẹp, ưu tiên kiểm chứng gray480 và nghiên cứu reuse/traffic/PPA.
2. Thiết kế bộ benchmark trước khi chạy thêm: ảnh chuẩn có nguồn/quyền sử dụng rõ ràng và pattern chẩn đoán, kích thước tăng dần tới320×240/480×320/480×480 gray, tile16/32/64, vài mức wait. Dùng tập nhỏ có lý do thay vì quét tổ hợp vô hạn; giữ cả ca bất lợi.
3. Với cùng frame, khảo sát tile/wait để phân biệt tác động tile và kích thước. Gray64/tile64 hiện không tự chứng minh tile64 tốt hơn tile16 vì workload khác. Nếu thêm word packing/streaming, giữ thành biến thể ablation riêng; không thay đổi nhiều yếu tố cùng lúc.
4. Làm related work và chốt câu hỏi nghiên cứu trước khi mở rộng RTL: Sobel, line buffer và RISC-V riêng lẻ không phải phát minh. Cần đối chiếu công trình và baseline, xác định đóng góp từ tích hợp/tái sử dụng/traffic/latency/PPA/tái lập. Chưa thực hiện tra cứu literature cập nhật trong bản tổng hợp này.
5. Chốt snapshot H1/H2, memory scope, clock, cùng flow/PDK/corner và constraint rồi chuẩn bị OpenLane. Người dùng chạy. So sánh area/timing/power theo đúng report, công khai violation/missing checks; nếu muốn energy theo workload cần methodology switching activity phù hợp, không suy từ vectorless tùy ý.
6. Đóng gói scripts tái tạo bảng/đồ thị, raw evidence, provenance, limitations và bản thảo; chọn tạp chí/trường phù hợp sau khi kiểm tra yêu cầu thật. Bài đăng/FPGA demo/tapeout là các mức hoàn thành khác nhau.

Rủi ro: 132byte line array có thể thành flop/mux, chưa có SRAM macro mapping; descriptor multipliers có thể tốn area; timing mới có thể khác v1; giảm transactions không bảo đảm giảm power; external memory thực có đặc tính khác wait cố định; regression hiện có chưa thay thế formal/randomized coverage; ảnh nhỏ không đủ suy ra480; novelty/paper acceptance chưa được xác nhận. Mục tiêu rút thời gian còn2–3ngày là mong muốn phối hợp, không cam kết hoàn tất silicon/PPA/bài báo.

## 9. Những câu hỏi cần ChatGPT giúp thảo luận

- Câu hỏi nghiên cứu và đóng góp nào có thể bảo vệ từ dữ liệu hiện tại, còn thí nghiệm/related work gì thiếu?
- Bài đầu nên chốt gray480 hay bắt buộc RGB480? Có cần sửa memory architecture ngay không?
- Bộ benchmark/tile/wait tối thiểu nào đủ thuyết phục và không lãng phí thời gian chạy?
- Có nên giữ H2 hiện tại để lấy PPA trước, hay word packing là ablation cần thiết cho câu hỏi bài báo?
- Phạm vi SoC subsystem với RAM ngoài cần được đặt tên và mô tả thế nào để không quá lời?
- Tiêu chí hoàn thành cho bài nghiên cứu cá nhân khác gì tiêu chí cho camera demo và chip tapeout?

Yêu cầu dành cho người tư vấn: phân biệt đã đo/ước tính/đề xuất; không bịa novelty, số liệu, trích dẫn hoặc nơi xuất bản; không dùng PPA RUN16 làm PPA H2. Sau thảo luận, người dùng sẽ chỉ thị bước tiếp theo. Hiện không cần chạy thêm.

## 10. Đường dẫn và bằng chứng

Trong upgrade: candidate/sobel_tile_v2.v, candidate/picorv32_sobel_soc_m3.v, candidate/tb_sobel_soc_m3.sv; firmware/s1 và firmware/h2; scripts/run_m3_tests.py, audit_m3.py, profile_m3.py. Các lệnh23/24 là lịch sử của RUN đã hoàn thành, không chạy lại cùng tag.

Bằng chứng nguyên gốc trong reports/*.zip; tổng audit hiện tại build/m3_all_exported_audit_01.json. Trong phiên này audit đã kiểm tra bảy ZIP, hash snapshot/evidence, output golden, profile, firmware/architecture binding và khớp nguồn chức năng hiện tại. Không mô phỏng lại. Bảng hash:

| Archive | SHA256 |
|---|---|
| s2_m3_soc_gray37x35_w1_01.zip | 85b8fc7227d30de4b4790f93ce4619d421c08f2f56b04282f5a0099e0f4cf43f |
| s2_m3_soc_gray64_t64_w1_01.zip | 77e7aeae7583a8b3e068e5b23827fc65efa8c3c263083669535e0aeb7ae65ee5 |
| s2_m3_soc_gray9x1_w1_01.zip | 831537a1c0a3303bf06991363c4fac562c69a0db1aef282a1f3c040deef1a737 |
| s2_m3_soc_rgb17x19_w3_01.zip | 51ca53da36b8f48d14bda1838d4ac31a596771b985e0bd36f9f5046d2ea59cea |
| s2_m3_soc_rgb1x1_w0_01.zip | f6bf3f797c3d3745f5aa73135a6591d0de7d4bb64150afde4d30836d0e642ae2 |
| s2_m3_soc_rgb1x7_w3_01.zip | 316151377ce2e08984e82a9a12e62b8be2f8e1a3b9982dfd28ae50278e742072 |
| s2_m3_soc_rgb32_w1_01.zip | 575f4ca3e7ec995412b3935d7143cd052151a4cea6f40fe4dc0f6ad3688d376a |
