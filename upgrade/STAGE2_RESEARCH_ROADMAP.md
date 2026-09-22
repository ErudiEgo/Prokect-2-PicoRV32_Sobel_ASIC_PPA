# Stage 2 — SoC RV32 tăng tốc xử lý ảnh nhỏ, hướng công bố khoa học

Ngày: 2026-09-16. Trạng thái: kế hoạch nghiên cứu đề xuất theo yêu cầu nâng dự án thành dự án cá nhân. Không phải đặc tả đã triển khai hoặc kết quả thực nghiệm mới. Không chạy simulation/OpenLane trong phiên lập kế hoạch.

## 1. Quyết định định hướng

Phát triển một SoC RV32 điều khiển bộ tăng tốc xử lý ảnh cục bộ cho thiết bị hạn chế tài nguyên. Giữ PicoRV32 RV32I, Sobel, firmware thực thi thật, xuất kết quả theo vùng, OpenLane Classic và SKY130 sky130A/sky130_fd_sc_hd.

Mục tiêu nghiên cứu trước mắt: giảm chi phí di chuyển dữ liệu, đo tăng tốc toàn ứng dụng và đánh đổi diện tích/bộ nhớ. Sản phẩm minh họa: thiết bị tạo hiệu ứng ảnh phác thảo hoặc khối tiền xử lý ảnh cho đồ chơi/thiết bị giáo dục. Camera đồ chơi hoàn chỉnh là nhánh ứng dụng sau, không phải điều kiện hoàn thành bài báo đầu.

Giả định đề xuất cho “480px”: mỗi chiều không vượt 480 pixel; ảnh ứng dụng 320x240 và 480x320, kiểm tra giới hạn 480x480. Nếu ý định là 480p/VGA 640x480 thì phải mở rộng lại chiều rộng, dung lượng và băng thông; không coi hai mục tiêu này là một.

Đích đầu: ảnh tĩnh, xử lý theo vùng. Đích nâng cao có điều kiện: 480x320 gray ở 10 frame/s trong cửa sổ xử lý ứng dụng. Đây là yêu cầu thiết kế đề xuất, chưa phải khả năng đã đạt; camera-to-display phải đo riêng. RGB là chế độ mở rộng, không buộc đạt cùng FPS với gray.

## 2. Hiện trạng và mức tin cậy

Đã đọc README.md, OPENLANE_WORKFLOW_NOTES.md, ARCHITECTURE.md, RGB32_FIRST_RUN_REVIEW.md, RUN16_REVIEW.md, PERFORMANCE_OPTIMIZATION_PLAN.md, config.json và phần DMA RTL. Số liệu dưới đây dẫn lại hồ sơ đánh giá hiện có; phiên này không tái audit toàn bộ archive hay tạo số đo mới.

| Hạng mục | Hồ sơ hiện có | Giới hạn |
|---|---|---|
| CPU | PicoRV32 RV32I thực thi firmware SW/HW | CPU bên thứ ba, không tuyên bố tự thiết kế ISA/core |
| MMIO ban đầu | Có trường hợp HW chậm hơn SW | Giữ như kết quả âm và động lực tối ưu |
| Tile DMA gray32 | 453421 / 69406 cycles, khoảng 6.532879x | Chỉ RUN soc_shapes32_dma_01 và điều kiện của nó |
| RGB32 | 1352946 / 206960 cycles, 6.537234x; 3072 mẫu kênh, 4 sự kiện vùng đúng | RGB17x19 và hồi quy gray còn phải hoàn tất theo hồ sơ |
| Kích thước | Gray <=512x512; RGB <=256x256 | RGB480 chưa được hỗ trợ |
| RUN16 vật lý | 195012 um² instance area; setup/hold/slew/cap, DRC/LVS/antenna đạt các check đã chạy | Fanout còn 1; collector FAIL_OR_INCOMPLETE |
| Phạm vi vật lý | CPU, Sobel legacy, Tile DMA/core, arbiter/bus | Chưa có program/image RAM, pads/package, camera interface |
| Power/IR | Vectorless; IR theo giả định nguồn/tải | Chưa là năng lượng workload RGB hoặc số đo silicon |

Clock RUN16 là 50 ns = 20 MHz, không phải 50 MHz. Không suy Fmax bằng phép trừ một giá trị slack. Các đoạn lịch sử trong tài liệu có trạng thái cũ; khi lập bảng bài báo phải dùng đúng RUN và snapshot.

## 3. Đóng góp khoa học dự kiến

Câu hỏi chính: với một CPU RV32 nhỏ và bộ nhớ hữu hạn có độ trễ, việc tái sử dụng pixel trong DMA làm thay đổi số giao dịch, latency toàn ứng dụng và chi phí vật lý như thế nào?

Ba giả thuyết cần kiểm chứng:

1. Tái sử dụng hàng/cửa sổ giảm giao dịch đọc so với DMA đọc lại từng hàng xóm; lợi ích latency phụ thuộc instruction fetch, arbitration, packing và memory latency.
2. Strip/line buffering cho một điểm đánh đổi tốt hơn giữa dung lượng nội bộ, halo và thời gian xuất vùng đầu; không giả định một cấu hình thắng mọi trường hợp.
3. Sau khi tối ưu CPU software công bằng, phần cứng vẫn có vùng workload/memory mà nó đem lại lợi ích đáng kể.

Đóng góp có thể bảo vệ: thiết kế tích hợp tái lập; khảo sát thực nghiệm có ablation; mô hình chi phí đối chiếu với transaction/cycle đo thật; PPA sau route với phạm vi công khai. Line buffer, Sobel và RISC-V riêng lẻ không phải phát minh mới. Artifact công khai làm bằng chứng mạnh hơn nhưng không thay thế khoảng trống nghiên cứu.

Đọc sâu khoảng 8–15 công trình gần nhất trước khi viết tuyên bố novelty. Lập bảng: CPU/ISA, thuật toán, dataflow, bộ nhớ, software baseline, transfer overhead, technology/FPGA, diện tích, power methodology, artifact, giới hạn. Không xếp hạng speedup giữa các bài có baseline khác nhau và không quy đổi LUT thành um².

## 4. Kiến trúc mục tiêu và các nhánh

```text
Boot/firmware + bộ nhớ làm việc
              |
         PicoRV32 RV32I ---- MMIO/control/status
              |                      |
      arbiter/memory controller --- DMA + line/window buffer
              |                      |
    ảnh nguồn / ảnh kết quả       Sobel 3x3 -> optional threshold
              |
    giao tiếp host/camera/display (nhánh demo sau)
```

### Nhánh chính A: DMA tái sử dụng dữ liệu

Giữ DMA v1 làm baseline. Thiết kế DMA v2 với line/window buffer và backpressure rõ ràng. Một kernel Sobel trước; threshold có thể ghép sau Sobel khi A đã ổn định. Không đổi đồng thời CPU, bus, memory và thuật toán vì sẽ khó xác định nguyên nhân cải thiện.

DMA v1 hiện đọc word 32 bit rồi lấy một byte cho từng hàng xóm, không cache/tái sử dụng word: pixel nội ảnh thường cần 8 giao dịch đọc và một ghi byte. Điều này tạo hai cơ hội khác nhau: tái sử dụng cửa sổ và tận dụng các byte trong word. Phải tách chúng khi đánh giá.

Với streaming raster 3x3, hai dòng trước rộng 480 gray8 cần 2x480 = 960 byte (7680 bit), cộng cửa sổ, FIFO và trạng thái. Đây là dung lượng logic tối thiểu của cách tổ chức hai dòng, không phải diện tích SRAM hay tổng bộ nhớ SoC. RTL khai báo array không đảm bảo tool tự tạo SRAM macro; triển khai flip-flop có thể làm area/power tăng mạnh.

So sánh strip toàn chiều rộng với tile có halo. Với tile nội ảnh TxT, nạp vùng (T+2)x(T+2) có hệ số dữ liệu lý tưởng (T+2)^2/T^2: T=16 khoảng 1.266; T=32 khoảng 1.129; T=64 khoảng 1.063. Đây chỉ là phân tích lượng pixel, chưa tính word alignment, biên ảnh và tranh chấp bus. Full-width strip có thể giảm đọc lại nhưng thay đổi thứ tự hoàn thành vùng. Replay/checker phải dùng vùng thật đã hoàn thành; không vẽ sự kiện tile cũ cho stream mới.

Nếu đổi lịch vùng, so sánh riêng: (a) cùng granularity để kiểm tra chi phí kiến trúc; (b) cấu hình vận hành tốt nhất của mỗi thiết kế, kèm first-region latency. Không cộng các bộ đếm chu kỳ chồng lấn thành tổng.

### Nhánh B: bộ xử lý ảnh nhỏ đa chế độ

Sau A: bypass, Sobel, Sobel+threshold; cân nhắc blur 3x3 khi đã có câu hỏi nghiên cứu cho nó. Giữ phép toán bit-exact từng chế độ. Không mở sang CNN, JPEG, ISP Bayer đầy đủ, Linux, RVV hoặc nhiều lõi trong bài đầu.

RGB hiện là Sobel từng kênh rồi ghép ảnh biên màu. RGB->gray->Sobel là tác vụ khác; có thể phù hợp sản phẩm hơn nhưng phải đặt baseline riêng, đóng băng công thức/chính sách làm tròn. Không dùng chênh lệch hai tác vụ để tuyên bố tăng tốc cùng thuật toán.

### Nhánh C: thiết bị chạy thật

FPGA chạy cùng CPU/firmware/accelerator, bắt đầu nạp ảnh từ host để chứng minh boot và data path. Sau đó thêm camera hỗ trợ định dạng phù hợp, cấu hình I2C và giao tiếp dữ liệu có tài liệu. Không mặc định camera có sẵn RGB8; tránh bắt đầu với raw Bayer/MIPI vì làm mở rộng công việc đáng kể.

Màn hình/camera/bộ nhớ ngoài có thể chậm hơn kernel. Phải tính tất cả vào latency camera-to-display. UART có thể phù hợp debug/ảnh tĩnh; lựa chọn kênh dữ liệu phải dựa trên băng thông đo được.

### Nhánh D: test chip

Chỉ mở sau khi có đối tác/hạ tầng, ngân sách và bộ collateral bộ nhớ/I/O tương thích. Cần boot ROM/SRAM/controller, reset/clock, pad ring/ESD, nguồn, test/debug/DFT theo mục tiêu, packaging/PCB và kế hoạch bring-up. Chạy được GDS core không đồng nghĩa chip độc lập sẵn sàng chế tạo.

## 5. Bộ nhớ là điều kiện quyết định

| Kích thước | Gray8 một frame | RGB888 một frame | RGB input + output |
|---|---:|---:|---:|
| 320x240 | 76800 B = 75 KiB | 230400 B = 225 KiB | 450 KiB |
| 480x320 | 153600 B = 150 KiB | 460800 B = 450 KiB | 900 KiB |
| 480x480 | 230400 B = 225 KiB | 691200 B = 675 KiB | 1350 KiB |

Chưa gồm firmware, stack, buffers, descriptor hoặc double buffering. Cửa sổ input/output hiện tại mỗi cửa sổ 256 KiB không chứa được RGB480x320. Ảnh gray480 có thể nằm trong giới hạn dung lượng hiện tại nhưng hỗ trợ theo giới hạn không phải kết quả functional test480.

Hai lựa chọn hợp lệ:

- Mở memory map, giới hạn DMA và TB cho frame buffer lớn hơn: dễ giữ luồng cũ, nhưng đây vẫn là RAM mô hình nếu chưa có phần cứng tương ứng. Audit overflow, overlap, end address, stride và plane offsets.
- Chuyển sang stream/strip từ bộ nhớ ngoài hoặc sensor: ít storage nội bộ, cần flow control, halo, buffer ownership, ordering và giao tiếp có thể hiện thực được. Đây là lựa chọn chiến lược ưu tiên.

Trong bài báo có thể công bố SoC subsystem với memory interface và giả định external memory rõ ràng. Nếu gọi là chip vận hành độc lập thì phải bổ sung các khối còn thiếu. Không blackbox memory rồi bỏ chi phí bộ nhớ khỏi tuyên bố diện tích toàn chip.

Chọn flip-flop buffer nhỏ cho bước chức năng; chỉ chốt implementation ASIC sau khi đánh giá area và bộ SRAM views thực tế: RTL/model, Liberty các corner phù hợp, LEF/GDS, kết nối nguồn và quy trình kiểm tra. Không hứa macro chỉ vì tìm thấy tên một compiler SRAM.

## 6. Mô hình hiệu năng trước khi viết thêm RTL

- T_processing = C_application / f_verified.
- Speedup cùng clock = C_SW / C_HW.
- Khác clock: Speedup_time = (C_SW/f_SW) / (C_HW/f_HW).
- FPS_processing = f/C_frame; không gọi là camera FPS nếu chưa bao gồm acquisition/output.
- Energy_frame = tích phân P(t) dt trong cùng cửa sổ; P trung bình x T chỉ hợp lệ khi P phản ánh đúng workload/phạm vi.

Ví dụ ngân sách, không phải kết quả: ở 20 MHz và 480x320, 10 frame/s cho phép khoảng 13.02 cycles/spatial pixel cho toàn phần xử lý; 30 frame/s chỉ 4.34. 480x480 ở 10 frame/s còn 8.68. RGB tuần tự phải chia sẻ ngân sách này cho cả ba kênh và mọi overhead.

Luồng input+output tối thiểu cho 480x320 ở 10 frame/s là 3.072 MB/s với gray8 và 9.216 MB/s với RGB888, chưa tính protocol, instruction fetch, halo, reread hay buffer trung gian. Không dùng bandwidth lý thuyết bus thay bandwidth hữu ích đo thật.

Kernel có thể nhận một pixel mỗi cycle khi đã được pipeline và không stall; điều đó không tự chứng minh hệ thống đạt một pixel/cycle. Core Sobel hiện có handshake cần được tính trong lịch DMA mới.

## 7. Thực nghiệm và kiểm chứng

### Baseline và fairness

S0: software lịch sử, bảo toàn. S1: software được tối ưu hợp lý (row pointers, sliding reuse, border handling), cùng RV32I/compiler/options được ghi rõ. H0: MMIO từng pixel làm đối chứng lịch sử. H1: DMA v1. H2: DMA v2. Nếu thêm word packing hoặc fusion, tạo ablation riêng.

Benchmark hiệu năng chính chạy S1/H1/H2 dưới cùng CPU, memory model, ảnh, phép toán, output requirements và cửa sổ đo. Chạy SW fallback trên cùng cấu hình SoC để cô lập tốc độ; CPU-only physical build riêng nếu muốn định lượng chi phí area của accelerator. Không lấy power/area SoC accelerated gán cho CPU-only.

Hai cửa sổ báo cáo: steady application (gồm chuyển dữ liệu, control, polling/IRQ, store và event); cold-start/camera-to-display khi có triển khai tương ứng. Nếu CPU polling chiếm bus, đo rõ trước khi đề xuất IRQ; IRQ PicoRV32 hiện tắt nên là thay đổi riêng.

### Bộ kiểm tra

Directed tests: 1x1, 1xN, Nx1; ảnh nhỏ hơn kernel; 17x19; 31/32/33; 63/64/65; kích thước lẻ; 320x240, 480x320, 480x480. Ảnh: zero/full255, impulse, ramp, checkerboard, cạnh qua tile/strip, mẫu RGB lệch kênh, ngẫu nhiên có seed, ảnh thật tự chụp/được phép dùng.

Kiểm tra zero-padding chỉ ngoài toàn ảnh; không tạo viền giả ở tile. So từng pixel/kênh với reference độc lập: Gx/Gy signed đúng độ rộng, min(255,abs(Gx)+abs(Gy)), không đổi sang sqrt. Không chỉ dùng PSNR/SSIM để che lỗi số học bit-exact.

Giao thức: reset giữa job, start khi busy, descriptor sai, address overflow/overlap, stall kéo dài/ngẫu nhiên, ổn định request khi chờ ready, không ghi trùng/mất pixel, done sau store cuối, fairness và không deadlock. Input/output cùng vùng chỉ được phép nếu đã thiết kế an toàn, mặc định từ chối.

Line buffer: fill/drain, wrap cuối dòng, cột cuối, halo, đổi kích thước liên tiếp, lưu trạng thái khi backpressure. Với stream không thể backpressure camera, cần chính sách overflow/drop và counter, không âm thầm mất frame.

Thử formal có phạm vi cho FSM, handshake, address bounds nếu công cụ/harness phù hợp; không gọi formal toàn SoC khi chỉ chứng minh một số property. Compile/lint không phải functional simulation.

### Ma trận gọn, mở rộng theo bằng chứng

1. Smoke RGB17x19 memory_wait3 và gray regression hiện đang thiếu.
2. S1/H1/H2 trên ảnh32/64, delay 0/1/3/7, tile16/32/64 hoặc strip tương ứng; không cần full Cartesian product ngay.
3. Khóa 2–3 cấu hình đáng quan tâm, đo ảnh128/256/320x240 và ảnh480 sau khi hỗ trợ thật.
4. Khoảng 10–20 ảnh thật có phân loại và nguồn; dùng small random tests cho coverage, không ép mọi ảnh lớn qua mọi tổ hợp.
5. Sweep tĩnh seed/repeated runs chỉ khi có yếu tố ngẫu nhiên. RTL tất định không cần lặp vô ích; báo biến thiên host runtime riêng. Nếu chạy nhiều physical seeds, báo tất cả và rule chọn trước.

Số liệu: cycles, reads/writes và useful bytes, stalls, instructions nếu đo được, CPU/DMA arbitration, cycles/spatial pixel, samples/channel, latency vùng đầu/cuối, total runtime. Chuẩn hóa rõ spatial pixel vs channel sample trong RGB. Counter phải nằm đúng cửa sổ và đếm handshake, không đếm valid kéo dài thành nhiều giao dịch.

## 8. PPA và mức tuyên bố

Chỉ đưa 2–3 cấu hình functional đạt sang physical runs. Khóa tool/PDK revisions đã cài, config/constraints/corner/library và memory implementation trước RUN mới. Dùng OpenLane Classic theo workflow hiện hành, không chuyển flow để tìm số đẹp.

Giữ RUN16 bất biến với fanout1. Thiết kế cuối nhắm fanout0 cùng antenna/DRC/LVS/setup/hold/slew/cap đạt; thiếu checker ghi NOT_RUN/MISSING. Nếu chưa xử lý được, có thể viết nghiên cứu với hạn chế công khai nhưng không gọi full sign-off. Không đặt tiêu chí theo kết quả để hợp thức hóa PASS.

Báo cell area, macro area, core/die area riêng; cùng điều kiện so sánh. Timing phải có corner, SDC I/O assumptions, unconstrained endpoints giải thích được. Thay memory/bus làm thay critical path nên phải đo lại.

Power là mục tiêu bổ sung: hoạt động từ workload được ánh xạ hợp lệ sang netlist và nêu annotation coverage, parasitics/corner/voltage, clock, khoảng warm-up/active/idle. RTL VCD không tự bảo đảm power sau route đáng tin. Nếu flow không hỗ trợ/mapping chưa xác minh, chỉ báo vectorless estimate và không kết luận energy saving. Nếu không có đo bộ nhớ ngoài, energy chỉ của subsystem trong phạm vi đó.

Không dùng power giảm/clock gating như khẩu hiệu. Clock gating là nhánh sau, cần cell/gating checks và workload idle có ý nghĩa. FPGA power đo trên board cũng không phải ASIC power.

## 9. Lộ trình và cổng quyết định

Ước lượng cho một người làm đều khoảng 12–20 giờ/tuần; không gồm thời gian phản biện tạp chí, mua thiết bị hoặc chế tạo. Đây là dự trù, sẽ cập nhật sau profiling.

| Giai đoạn | Dự trù | Sản phẩm và điều kiện chuyển |
|---|---|---|
| 2.0 Khóa nghiên cứu | 1–2 tuần | Spec480, scope, evidence ledger, literature matrix; không còn nhầm current/historical |
| 2.1 Baseline đáng tin | 2–3 tuần | RGB partial + gray regression, S1, counters, golden độc lập; dữ liệu đủ xác định bottleneck |
| 2.2 DMA v2 | 3–5 tuần | Line buffer/packing có ablation, adversarial tests, bit-exact và không deadlock |
| 2.3 Mở workload480 | 2–3 tuần | Memory map/stream thực, kiểm tra giới hạn, ảnh thật; không suy từ RGB32 |
| 2.4 PPA cuối | 3–5 tuần | 2–3 cấu hình sau route, scope/checker đầy đủ; power estimate gắn đúng phương pháp |
| 2.5 Artifact + bài | 2–3 tuần | Dataset manifests, tables từ reports, limitations, bản thảo được người khác tái lập/review |

Tổng dự trù tuyến chính 13–21 tuần, nên dành thêm khoảng 20–30% dự phòng. Có thể viết related work/method từ đầu. FPGA demo thêm khoảng 4–8 tuần nếu đã có board phù hợp và kinh nghiệm, có thể làm sau khóa artifact chính. SRAM integration/tapeout không nằm trong dự trù này.

Cổng dừng: nếu H2 chỉ hơn H1 rất ít, phân rã stalls/transactions rồi quyết định tối ưu hay ghi nhận tradeoff; không bịa mục tiêu speedup. Nếu array làm area tăng quá lớn, thử strip nhỏ/memory implementation có view hợp lệ. Nếu novelty trùng mạnh, điều chỉnh câu hỏi trước khi tiếp tục ma trận lớn. Nếu power không đáng tin, tập trung latency/traffic/area thay vì tuyên bố low-power.

## 10. Tính khả thi và rủi ro

| Hạng mục | Đánh giá kỹ thuật | Rủi ro/điều kiện |
|---|---|---|
| Gray <=480 ở RTL | Cao từ nền hiện có | Chưa có test480; thời gian simulation/watchdog |
| RGB480 | Khả thi có điều kiện | Vượt cửa sổ RAM hiện tại, thay map/stream và regression |
| DMA line buffer | Khả thi | Area lưu trữ, arbitration, boundary/backpressure |
| Bài báo nghiên cứu thiết kế | Khả thi có điều kiện | Cần novelty có căn cứ và baseline mạnh; không bảo đảm nhận |
| FPGA chạy CPU thật | Khả thi có điều kiện | Board/memory/boot/peripheral chưa được xác định |
| Camera đồ chơi hoàn chỉnh | Nhánh dài hơn | Sensor/display/storage/I/O, công sức tích hợp và BOM |
| Silicon/tapeout | Chưa đủ cơ sở cam kết | Memory/IP/pads/test/funding/partner/PDK acceptance |

Không đề xuất mua board/camera hay chốt ngân sách giá thị trường trước khi có danh sách phần cứng hiện có. Chi phí phải chia: thiết kế/compute/storage, FPGA+camera+display, và silicon+package+PCB+bring-up. Có thể làm bài đầu với môi trường hiện có; không cần mua silicon để được gọi là nghiên cứu ASIC, miễn ghi rõ là kết quả thiết kế/mô phỏng.

Đồ chơi chụp ảnh là bối cảnh sử dụng, chưa phải bằng chứng thị trường. Sobel tạo ảnh biên chứ không cải thiện chất lượng nhiếp ảnh nói chung. Chip chuyên dụng phải chứng minh lợi ích của tác vụ cụ thể so với giải pháp MCU/module có sẵn trước khi gọi là sản phẩm cạnh tranh.

## 11. Công bố và uy tín cá nhân

Tiêu đề dự kiến, sẽ sửa theo kết quả: “Thiết kế và đánh giá SoC RV32 tích hợp bộ tăng tốc Sobel tái sử dụng dữ liệu cho xử lý ảnh độ phân giải thấp”. Nếu vẫn thiếu bộ nhớ thật, tên/abstract ghi rõ subsystem và phạm vi external memory.

Mạch bài: nhu cầu cụ thể -> related work và khoảng trống -> spec/dataflow -> phương pháp kiểm chứng -> functional/latency/traffic -> PPA -> ablation -> threats to validity -> limitations. Không đặt số speedup mục tiêu vào abstract trước khi có dữ liệu.

Ứng viên tìm hiểu trước: JST: Smart Systems and Devices của Đại học Bách khoa Hà Nội, dựa trên phạm vi thiết bị/hệ thống thông minh công bố tại website. Đây là đề xuất phù hợp chủ đề sơ bộ, không bảo đảm fit hoặc acceptance. Đọc bài chip/embedded gần đây và hướng dẫn tác giả trước khi chọn; có thể gửi scope inquiry bởi chính tác giả khi cần. Không tự gửi thư hay bản thảo trong kế hoạch này.

Khóa tạp chí mục tiêu trước định dạng cuối; kiểm tra ngôn ngữ, template, review, phí, data/code và AI disclosure hiện hành. Không suy chất lượng từ việc “trong nước”; phải có phản biện và phù hợp lĩnh vực. Không nộp đồng thời; tác giả/affiliation/đóng góp phải đúng, không mượn tên trường hoặc thêm đồng tác giả hình thức.

Artifact: mã với license/provenance, tag release bất biến, input hashes và quyền dữ liệu, compiler/PDK/tool revisions, RUN manifests, raw reports, checker, script tạo bảng/plot từ báo cáo thật, hướng dẫn tái lập, known limitations. Audit license PDK/CPU/dataset trước khi public; không tự công khai mọi archive. Tài liệu tái lập không yêu cầu chạy lại flow để chỉ đọc report.

Lập claim-evidence ledger: claim, RUN, snapshot hash, nguồn report/stage/corner, phép tính, phạm vi, trạng thái. Phân biệt MEASURED_RTL, REPORTED_POST_ROUTE_ESTIMATE, ANALYTICAL, TARGET, NOT_RUN; không lấp ô thiếu bằng 0.

Uy tín đến từ cả kết quả âm: MMIO chậm hơn SW, area tăng do closure, fanout còn lại và những cấu hình không đáng dùng. Release đầu cùng báo cáo kỹ thuật có thể có giá trị trước khi được tạp chí chấp nhận. Nên có một người làm vi mạch đọc phương pháp/claims và một người thử tái lập từ hướng dẫn; chỉ ghi đồng tác giả khi đóng góp thực chất.

## 12. Bước gần nhất

1. Chốt bản yêu cầu theo giả định 480 ở mục 1; tách target ứng dụng và stress test.
2. Bảo toàn baseline/snapshot hiện có; lập evidence ledger cho các kết quả sẽ dùng.
3. Hoàn tất RGB17x19 và gray regression đang thiếu, theo RUN mới do người dùng thực thi.
4. Profiling H1 và tối ưu S1 công bằng; thiết kế memory budget và spec DMA v2 từ số liệu.
5. Implement/check tĩnh trước; chỉ sau functional evidence mới mở physical RUN mới.

Không đưa lệnh chạy một thiết kế chưa tồn tại. Khi bước triển khai được mở, chuẩn bị lệnh Ubuntu tách riêng với RUN tên mới, precheck và điều kiện thành công dự kiến theo OPENLANE_WORKFLOW_NOTES.md. Không tái sử dụng tên RUN16 hoặc các launcher lịch sử.

## 13. Nguồn ngoài đã đối chiếu

Các nguồn dưới đây hỗ trợ hướng kiến trúc và kiểm tra tiền lệ; không phải tổng quan tài liệu đã hoàn tất. Truy cập 2026-09-16.

- PicoRV32 upstream, cấu hình/ISA/license và mục tiêu thiết kế: https://github.com/YosysHQ/picorv32
- Tiền lệ RISC-V coprocessor với Sobel: “A Reconfigurable Convolutional Neural Network-Accelerated Coprocessor Based on RISC-V Instruction Set”, Electronics 2020, 9(6), 1005. https://www.mdpi.com/2079-9292/9/6/1005
- AMD Window2D, nguyên lý line/window buffer và data reuse; chỉ tham khảo kỹ thuật, không coi FPGA là ASIC PPA: https://docs.amd.com/r/2024.1-English/Vitis-Tutorials-Hardware-Acceleration/Window2D-Line-and-Window-Buffers
- JST Smart Systems and Devices, phạm vi và hướng dẫn: https://jst.vn/index.php/ssad/guide-for-authors
- SKY130 open PDK status; phải đánh giá revision/collateral và yêu cầu nhà chế tạo cho mọi kế hoạch test chip: https://skywater-pdk.readthedocs.io/en/main/status.html
