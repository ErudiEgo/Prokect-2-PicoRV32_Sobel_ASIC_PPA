# Định hướng dự án PicoRV32 Low-Resolution Image-Processing SoC/SubSystem

Ngày: 2026-09-21. Tài liệu hợp nhất chỉ thị cấp dự án 1–23 và bổ sung 24–35 do người dùng cung cấp. Đây là định hướng và các gate phát triển, không phải specification H3 đã duyệt hoặc bằng chứng triển khai mới. Chỉ thị mới thay thế cách định vị mục tiêu tổng chỉ là “PicoRV32 + Sobel”; không thay đổi lịch sử hay số liệu đã đo.

Phạm vi task hiện tại: **chỉ tạo tài liệu này**. Không sửa RTL/firmware/checker/config, không chạy simulation/OpenLane/Vivado, không tạo số đo mới. Chưa thực hiện freeze/tag H2, tạo branch H3 hoặc sửa kiến trúc.

## 1. Mục tiêu tổng và ba cấp độ định vị

**Dự án tổng:** Phát triển kiến trúc SoC/subsystem xử lý ảnh độ phân giải thấp dựa trên PicoRV32 và bộ tăng tốc phần cứng; Sobel được sử dụng làm workload/operator đầu tiên để nghiên cứu cơ chế offload, di chuyển dữ liệu và tái sử dụng pixel.

**H2:** H2 là Sobel-specific accelerator với line-buffer/data reuse.

**H3 tương lai:** H3 hướng tới tách data movement/window generation khỏi processing operator để tạo nền xử lý ảnh 2D có thể tái sử dụng.

Ứng dụng định hướng gồm thiết bị hình ảnh nhỏ, camera giáo dục/đồ chơi, image preprocessing hệ nhúng và thiết bị quan sát tài nguyên hạn chế. Không tự mở sang GPU3D, AI accelerator, full ISP, JPEG engine hoặc camera product hoàn chỉnh. Sobel là operator đầu tiên, không phải giới hạn cuối cùng.

Tên mô tả hiện phù hợp: **PicoRV32-based low-resolution image-processing SoC/subsystem architecture**. Chưa gọi complete camera SoC hoặc fabricated imaging chip. Paper1 là checkpoint, không kết thúc dự án.

## 2. Lịch sử phải bảo toàn

```text
PicoRV32 software
  → Legacy MMIO Sobel
  → H1: Sobel DMA không spatial reuse
  → H2: Sobel DMA line-buffer/data reuse
  → [tương lai] H3: generic 2D dataflow
  → multiple operators
  → FPGA / real-memory prototype
  → imaging SoC mở rộng
```

Không viết lại lịch sử như thể H3 đã tồn tại từ đầu. Không thay thế hoặc xóa baseline cũ. Chuỗi trên mô tả evolution, không ngụ ý H2/H3 đã có physical implementation: RUN16 vật lý thuộc baseline H1 lịch sử.

| Đối tượng | Bản chất và trạng thái |
|---|---|
| Stage1/RUN16 | Baseline vật lý SKY130 có CPU, Sobel, DMA/bus. External RAM chưa nằm trong ASIC; chưa pads/package/camera/display, chưa silicon. Power là estimate; còn fanout violation; không tapeout-ready. Firmware execution có bằng chứng RTL riêng, không phải CPU chạy trên silicon. |
| S0/S1 | Software gốc/software tối ưu; bảo toàn compiler/options/binary. Không gọi S1 là software tối ưu tuyệt đối. |
| H1 | Sobel DMA v1, đọc lại hàng xóm cho từng output, làm đối chứng nghiên cứu/PPA. |
| H2 | Sobel DMA v2; hai line buffer66byte cộng taps/FSM. 132byte chỉ là hai dòng, không phải toàn RAM. Vẫn dùng một byte từ mỗi read bus32, chưa word packing. |
| H3 | Hướng phát triển kiến trúc, chưa có specification được review hoặc RTL H3. Thêm vài OPCODE không đủ chứng minh generic. |

## 3. Đã hoàn thành và chưa hoàn thành

Theo các audit đã có trước task này: M1 ba workload đạt; M2 sáu workload đạt; H2 unit181ca đạt; M3 tích hợp bảy workload đạt pixel/tile/profile và binding nguồn/firmware. S1 có profile giống nhau trên v1/v2 trong bảy ca. Bộ regression đạt không chứng minh mọi trạng thái hoặc thay thế formal verification.

Ví dụ evidence lịch sử, không đo mới: RGB32 H1=206960/H2=57515cycles, DMA reads23436→3468; gray64/tile64 H1=278200/H2=68287cycles. Kết quả âm: RGB1×1 H1=864/H2=999cycles; RGB1×7 H1=5116/H2=5347cycles. Giữ cả các ca S1 chậm hơn S0. Không khái quát H2 luôn thắng.

Chưa hoàn thành: freeze H2 có tên logic/provenance Git rõ ràng; characterization gray scaling/tile/wait đầy đủ; PPA H1/H2 có kiểm soát; H3 spec/review/RTL; operator thứ hai; FPGA fit/hardware prototype; literature/novelty/bản thảo. RGB480 không bắt buộc và chưa được hỗ trợ.

Một số trạng thái cũ trong README/stage2.json chưa phản ánh audit M3 mới nhất; không sửa chúng trong task tài liệu này. Dùng PROJECT_HANDOFF_2026-09-21.md và build/m3_all_exported_audit_01.json để đối chiếu trạng thái hiện tại. Việc đồng bộ metadata sau phải giữ tương thích contract runner, không đổi nhãn để giả tạo evidence.

## 4. H2 là baseline nghiên cứu cần freeze

Tên logic dự kiến: **H2_LINEBUFFER_BASELINE**. Chưa tuyên bố tên này là tag đã tồn tại. H2 phải được bảo toàn cho benchmark, characterization, PPA, ablation, so sánh H1 và H3; không generic hóa tại chỗ.

Gate freeze yêu cầu snapshot không ghi đè, inventory và hash RTL/TB/checker/runner/firmware/input/config; commit/tag thực tế liên kết snapshot; ghi parent/ref và trạng thái working tree. Không gán working tree chưa commit thành commit sạch. Firmware giữ source, compiler/options, HEX, ELF/disassembly, manifest và build archive. Liên kết unit181, bảy ZIP M3, audit và raw traces; giữ M1/M2/RUN16 và kết quả âm.

**PASS freeze:** snapshot/tag/provenance được xác minh; file/evidence cần thiết đầy đủ và hash khớp; ghi rõ missing/unrun checks. Lỗi sau freeze mở revision/RUN mới, không sửa baseline cũ. H3 phát triển trên branch riêng khi đủ gate; task hiện tại chưa tạo branch đó.

## 5. Phân loại module: reuse và refactor

| Khối | Loại | Hướng H3 |
|---|---|---|
| PicoRV32 RV32I | Infrastructure | Reuse core/config đã kiểm chứng, không viết lại CPU. |
| Native bus/arbiter/external interface | Infrastructure | Reuse; không tự chuyển AXI, cache hoặc bus64. |
| MMIO/descriptor/control/status | Infrastructure có ABI hiện hữu | Reuse framework, thiết kế ABI H3 tường minh; giữ TIL1/TIL2 cho baseline. |
| Address/read/write/bounds/stride | Infrastructure đang nằm trong tile engine | Tách khỏi operator; read/address không biết công thức Sobel. |
| Line buffer/window/stream handshake | Infrastructure | Tách storage/window generation, quy định stall/metadata/ownership; FIFO chỉ thêm khi có lý do. |
| Gx/Gy/magnitude/saturation | Operator-specific | Đóng gói Sobel block window→result, không main-memory address/DMA/arbitration. |
| Threshold/coefficients/post-processing | Operator-specific | Chưa thêm; chỉ chọn một operator sau H3 Sobel PASS. |
| Firmware framework/verification/OpenLane | Infrastructure | Kế thừa framework, golden độc lập và flow; không xây lại toàn SoC. |
| Profiling/replay | Verification infrastructure | Profiler hiện ở TB, không gọi hardware counter. FPGA cần counter synthesizable riêng. |

Phần refactor chủ yếu là chức năng accelerator hiện gom trong candidate/sobel_tile_v2.v và giao diện operator; H2 frozen không sửa. Các module tương lai ở bảng là phân chia trách nhiệm dự kiến, chưa phải RTL đã module hóa.

Không tự thêm Linux, shader, rasterizer, CNN, JPEG, multicore, descriptor chain/frame scheduler phức tạp hoặc multiple outstanding khi chưa có evidence cần thiết.

## 6. Architecture diagram H3 — mục tiêu, chưa triển khai

```text
                     PicoRV32
                        │ command/MMIO
                        ▼
              Descriptor / Control / Status
                        │
Frame/System RAM ↔ native bus/arbiter ↔ external-memory interface
                                        │                 ▲
                                 Read/Address Engine      │
                                        ↓                 │
                                Small Local Buffer        │
                                        ↓                 │
                                  Window Generator        │
                                        ↓                 │
                        Processing interface valid/ready  │
                         window + center + metadata       │
                                        ↓                 │
                             Operator: Sobel đầu tiên     │
                                        ↓                 │
                              Result valid/ready          │
                                        ↓                 │
                                  Write Engine ───────────┘
```

Sơ đồ không mặc định read/write song song, pipeline1pixel/cycle hoặc nhiều outstanding. Sobel chỉ window→calculation→result; không biết tile memory layout hoặc external RAM.

Specification trước RTL phải chốt: trách nhiệm module; bit-width/signedness/rounding; layout window/center; metadata; valid/ready và payload ổn định khi stall; backpressure cả hai phía; reset/abort/flush/error/done; bounds/alignment/stride; border semantics; tile/stream semantics; ordering/số output; partial/degenerate; buffer ownership/warm-up; operator latency và giới hạn buffering.

Các mục trên là checklist review, chưa là giao thức đã duyệt. H3 Sobel phải bit-exact với golden/H2 cùng specification/input trước khi thêm operator thứ hai. Operator đó phải chứng minh dùng lại movement/window interface, không chọn chỉ để demo đẹp. Threshold, blur3×3, sharpen, Conv3×3 là ứng viên; programmable convolution chưa mặc định vì width/area/timing/control.

## 7. Quy tắc memory architecture

Phân biệt **memory capacity**, **memory bandwidth/latency**, **local data reuse**. Tăng frame RAM chủ yếu cho phép ảnh lớn/nhiều buffer hơn, không mặc định tăng throughput. Hiệu năng còn phụ thuộc transactions/pixel, useful bytes/word, wait, reuse, overlap, arbitration và khả năng read/write song song.

```text
Registers/control
    ↓
Local accelerator storage: line buffer/window/FIFO/scratchpad
    ↓
System/frame memory: input/output/firmware/data
    ↓
Host/camera/storage
```

Local buffer nhỏ phục vụ dataflow; không cần chứa toàn frame hoặc tăng theo diện tích ảnh. Frame memory không phải accelerator-local storage. RAM mô hình TB không phải SRAM ASIC hay BRAM FPGA.

Hiện input/output mỗi vùng256KiB. Gray480×320 vừa về capacity nhưng chưa có functional evidence kích thước này. RGB hiện giới hạn256×256, không tự bỏ guard. Ưu tiên Gray8:32×32,64×64,128×128,256×256,320×240,480×320;480×480 khi phù hợp. Ghi đầy đủ kích thước, không gọi “480” là VGA640×480.

Trước đổi memory/bus cần hypothesis và profiler: useful bytes/transaction, transactions/pixel, cycles/pixel, memory waits và arbitration. Full-word bus bytes không phải unique/useful bytes. Bus32 vẫn dùng1byte/read thì ưu tiên khảo sát packing/reuse trước bus64. Capacity256KiB→1MiB không gọi performance optimization nếu workload chưa bị capacity giới hạn.

Physical top gần hạn: **CPU + bus + accelerator + local buffer + external-memory interface**. Không đưa framebuffer hàng trăm KiB/MiB vào top bằng standard-cell FF/mux chỉ để nói có RAM. Buffer nhỏ cũng phải đo area/timing, không tự gọi SRAM. SRAM macro là milestone riêng cần macro/model chức năng, timing/Liberty corners, physical abstract/layout, power model, floorplan/PDN/routing và verification tương ứng.

## 8. Roadmap, gate và tiêu chí PASS

| Mốc/nhóm | Điều kiện và công việc | PASS/evidence |
|---|---|---|
| Freeze H2 / A | M3 đã audit; chưa sửa accelerator | Baseline bất biến, commit/tag/snapshot/manifest và hash liên kết đầy đủ evidence. |
| Characterization / A | Freeze đạt; kế hoạch benchmark rõ | Gray scaling tới480×320; tile16/32/64 trên cùng input; wait0/1/3 trên cùng workload; giữ37×35/17×19/partial và1×1/1×N/N×1. Golden, cycles/traffic/latency thật, input/source/config/tool binding. Giữ kết quả âm; không cần Cartesian product. |
| H1/H2 PPA / B | Functional evidence đúng snapshot, tool/PDK đã xác minh | Physical runs mới cùng PDK/library/flow/constraint/methodology và scope so sánh được. Báo area/timing/power estimate/checks, violations và NOT_CHECKED. Chỉ gọi đạt check nào khi report chứng minh; exit0 không full sign-off. |
| H3 specification / C | H2 freeze, characterization/PPA được review | Chỉ viết spec: boundaries, read/buffer/window/operator/write/MMIO, stall/border/tile/reset và verification plan. Chưa code. |
| H3 architecture review / C | Spec đầy đủ | Review được ghi nhận, vấn đề chặn được giải quyết; plan thay/reuse/hypothesis/PASS/regression/evidence rõ. Sau đó mới RTL trên branch riêng. |
| H3 Sobel / C | Review đạt | Bit-exact golden/H2; stall/reset/border/partial/degenerate và CPU integration đạt; overhead/traffic đo thật, không ép speedup. |
| Operator thứ hai / C | H3 Sobel PASS | Một operator, arithmetic/golden riêng; tái sử dụng movement/window interface; Sobel regression vẫn đạt. |
| FPGA Gate A / D | Task độc lập, top tối thiểu | Vivado synthesis/implementation/timing/utilization; LUT/FF/BRAM/DSP, WNS/TNS và clock được kiểm chứng. Không kết luận Basys3 đủ/thiếu trước report. |
| FPGA Gate B / D | Kiến trúc/H3 ổn định, real memory/I/O | CPU boot thực; PC gửi nhiều ảnh mới không regenerate bitstream; FPGA xử lý/trả output bit-exact; counter phần cứng, test failure rõ, timing/resources được lưu. |
| Paper1 / A+B | Dữ liệu frozen, methodology và literature đủ | Claims truy evidence; so S0/S1/H1/H2 traffic/cycles/PPA, negative results, reproducibility và limitations. Kỹ thuật PASS không bảo đảm novelty/publication. |
| Application/demo / E | Yêu cầu riêng và prerequisite liên quan đạt | Camera/display/GUI có scope/evidence riêng; không ép scheduling để đẹp hình. |

Ưu tiên hiện tại: **freeze H2 → characterize H2 → H1/H2 PPA → H3 spec → review → H3 implementation/Sobel → mở rộng khi đủ gate**. Operator thứ hai chỉ sau H3 Sobel PASS. FPGA full prototype sau khi ổn định; FPGA Gate A có thể làm sớm như task D độc lập, không làm gián đoạn H2/Paper1. Paper1 không phải chờ toàn bộ H3/FPGA và không kết thúc project.

## 9. Ba track liên kết nhưng không thay thế nhau

```text
                    PROJECT
                       │
        ┌──────────────┼──────────────────┐
        ▼              ▼                  ▼
 Research/ASIC     Architecture       FPGA validation
 S0/S1/H1/H2       H3 generic          Gate A: fit
 characterization dataflow            Gate B: hardware
 H1/H2 PPA        operators           PC→FPGA→PC
 Paper1           extensions          real memory/I/O
```

H3 không xóa H2; FPGA không thay ASIC; ASIC không là prerequisite cho FPGA; FPGA không là prerequisite cho PPA. Không tự triển khai nhiều track cùng lúc chỉ vì liên quan.

**FPGA Gate A:** top synthesizable tối thiểu clock/reset Basys3 + PicoRV32 + bus + accelerator + bộ nhớ BRAM nhỏ. Chưa cần camera/VGA/GUI/full UART/ảnh480/full application. Phải có synthesis, implementation, timing và utilization để biết headroom. Báo constrained/operating clock và timing có căn cứ, không suy Fmax tùy ý từ slack. Nếu không fit, giảm resolution prototype/stream hoặc board lớn hơn về sau; không làm méo kiến trúc ASIC để ép vừa Basys3.

**FPGA Gate B:** branch implementation riêng. Nạp bitstream một lần; CPU boot từ FPGA memory; PC gửi ảnh mới qua real host link; input được lưu/stream; CPU cấu hình accelerator; FPGA thật xử lý; output về PC dựng ảnh và so golden độc lập. Chạy nhiều ảnh liên tiếp, có hardware cycle counter, timing/resource reports và test failure rõ. Không đưa tb_sobel_soc hoặc RAM/file-I/O simulation lên FPGA như phần cứng. PC chỉ decode/encode/format/transfer/visualize/reference, không tính operator thay FPGA.

Tách **processing time** từ counter FPGA và **PC↔FPGA end-to-end time**; nếu UART chậm phải báo communication bottleneck. FPGA báo actual clock/cycles/time/LUT/FF/BRAM/DSP/Vivado timing. ASIC báo RTL cycles/SKY130 STA/cell-core-die area/physical checks/power methodology. Không quy đổi LUT sang ASIC area, không dùng FPGA Fmax cho ASIC. Khi có CPU, firmware/data memory, accelerator và host I/O thực, có thể gọi FPGA prototype of the image-processing SoC architecture.

**Paper1:** CPU software→H1→H2, memory traffic, cycles và PPA trade-off. Literature review trước novelty. Giá trị integration/resource constraints/controlled evolution/reproducibility phải được đánh giá, không mặc định mới. Paper/extension sau có thể về H3/operators/FPGA. Chưa chọn venue hoặc đưa trích dẫn chưa kiểm chứng.

Visualization đi theo hardware execution→instrumentation/log→replay. Pixel replay dùng timestamp output-write thật; tile view chỉ gọi tile/job completion visualization. GUI không quyết định ngược scheduling của hardware.

## 10. Risk register

| Rủi ro | Kiểm soát/gate |
|---|---|
| Scope lệch Sobel-only hoặc full ISP/GPU | Giữ ba câu định vị và phân loại task A–E. |
| Mất H2 reproducibility khi refactor | Freeze trước, H3 branch riêng, evidence/hash bất biến. |
| H2 nhanh nhưng area/timing/power bất lợi | H1/H2 PPA thật cùng methodology; báo trade-off, không đoán trước. |
| Buffer FF/mux/descriptor logic tốn tài nguyên | Local buffer nhỏ được đo; cấm framebuffer FF lớn; macro là milestone riêng. |
| Nhầm capacity với throughput | Profiler bottleneck trước bus/RAM change. |
| H3 generic trên tên nhưng vẫn Sobel-specific | Read/address độc lập công thức; interface operator; operator thứ hai chứng minh reuse. |
| Stall/reset làm mất/lặp/misorder pixel | Spec payload/ownership/backpressure/reset/done và regression đối kháng. |
| Over-engineering Conv/AXI/cache/outstanding | Chỉ mở khi evidence/hypothesis cần; một operator mỗi bước. |
| Workload nhỏ không đại diện scaling | Gray scaling và same-input tile/wait sensitivity; giữ negative. |
| Memory model xa phần cứng thực | Ghi giả định TB; FPGA real-memory milestone riêng. |
| Basys3 thiếu resource/timing | Gate A reports; điều chỉnh prototype, không kết luận trước. |
| Host communication che processing | Counter nội FPGA và end-to-end timer riêng. |
| PPA khác scope hoặc energy claim sai | Pin tool/PDK/config/scope; không ghép power RUN16 với H2 cycles. |
| Thiếu novelty/cherry-pick | Literature, controlled comparison, raw data và negative results. |

## 11. Những điều tuyệt đối không được tuyên bố

- H2 là generic accelerator; H3 đã tồn tại chỉ vì có OPCODE.
- RAM TB là SRAM ASIC; line buffer là tổng frame memory; full-frame FF RAM là cách tích hợp mặc định.
- Tăng capacity/bus width tự động tăng tốc; resolution chưa test/chứng minh đã hỗ trợ.
- H2 luôn thắng; loại ca xấu hoặc gán dữ liệu phiên bản khác.
- RUN16 là PPA H2; vectorless power là năng lượng workload thực; exit0/78–81stage là full sign-off.
- Complete camera SoC/fabricated chip/tapeout-ready khi chưa đúng mức tích hợp.
- Basys3 fit trước Vivado; FPGA speed/Fmax/resource là ASIC speed/Fmax/area.
- Novelty từ riêng RISC-V/Sobel/DMA/line buffer/Conv3×3/FPGA hoặc bảo đảm publication.
- Pixel/cycles/PPA/timestamp dựng; nới checker để PASS; replay được gọi là hardware live execution.

## 12. Evidence phải bảo toàn

Đường dẫn sau tương đối với upgrade, trừ Stage1 ở thư mục cha.

| Nhóm | Evidence |
|---|---|
| Stage1 | ../RUN16_REVIEW.md, ../reports/picorv32_sobel_dma_clk50_baseline_06_collect_20260914T045526219194Z.tar.gz; run/snapshot Ubuntu và RUN12 backup. |
| Import nền | baseline/stage1_import.zip, import_manifest.json; provenance working tree, không giả commit sạch. |
| RTL | rtl/, third_party/picorv32/, candidate/sobel_tile_v2.v, candidate/picorv32_sobel_soc_m3.v, hai testbench candidate. |
| Firmware | firmware/generated, firmware/s1, firmware/h2; nguồn/start/linker, HEX/manifest/build_evidence.zip. |
| Verification | tb/, scripts/run_m3_tests.py, audit_m3.py, profile_m3.py, evidence.py và dependencies; frozen checker mỗi RUN. |
| Inputs | inputs/*: metadata/HEX/provenance/hash; không thay ảnh trong RUN cũ. |
| M1/M2 | Ba s2_m1_*.zip, sáu s2_m2_*.zip và biên bản audit. |
| H2 unit | reports/s2_m3_unit_01.zip; unit181cases/logs/hash. |
| H2 integration | Bảy ZIP M3 liệt kê dưới; snapshot/config/tool versions/commands, pixel/tile CSV, execution/profile/metrics/comparison/output images/summary. |
| Audit/handoff | build/m3_all_exported_audit_01.json; PROJECT_HANDOFF_2026-09-21.md có bảng archive hashes; M2_M3_UNIT_ACCEPTANCE.md; M3_RGB32_REVIEW.md. Build thường không thuộc Git: audit cần được đưa vào gói freeze có manifest, không chỉ giữ trong build. |
| Physical/FPGA tương lai | Commit/tag/source/firmware/config/input/test-condition hashes; tool/PDK/OpenLane RUN/raw reports; Vivado part/XDC/version/bitstream/firmware/host protocol và hardware output/counters. |

Bảy integration RUN: s2_m3_soc_rgb32_w1_01; s2_m3_soc_rgb17x19_w3_01; s2_m3_soc_gray37x35_w1_01; s2_m3_soc_rgb1x1_w0_01; s2_m3_soc_rgb1x7_w3_01; s2_m3_soc_gray9x1_w1_01; s2_m3_soc_gray64_t64_w1_01. Đây là evidence đã có, không phải yêu cầu chạy lại.

## 13. Gate vận hành task tiếp theo

Trước thay đổi lớn phân loại **A Paper1 characterization; B ASIC/PPA; C H3 architecture evolution; D FPGA implementation; E application/demo**. Task trộn nhóm phải nêu trước và tách scope, không tự làm đồng thời.

Proposal bắt buộc: module thay; module giữ; hypothesis; PASS criteria; regression; evidence sinh ra; cách bảo toàn baseline. Sau milestone báo thay đổi/file/tests/PASS-FAIL-NOT_RUN/số liệu thật/limitations, handoff khi yêu cầu. Review spec trước H3 RTL là yêu cầu trực tiếp của người dùng.

Trợ lý chuẩn bị nguồn/scripts/constraints, static/compile/lint và audit. Người dùng chạy simulation/OpenLane và flow implementation nặng, gồm Vivado khi được giao. Lệnh từng bước, RUN tường minh, điều kiện thành công, terminal progress và export evidence kể cả lỗi. Không overwrite hoặc rerun chỉ để xem report.

**Task định hướng kết thúc ở tài liệu này. Bước kế tiếp theo ưu tiên là A — freeze H2 M3, rồi characterization; không phải code H3 hoặc thêm operator ngay.**
