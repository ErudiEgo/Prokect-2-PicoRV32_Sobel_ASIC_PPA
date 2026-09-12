# PicoRV32 Sobel ASIC PPA

**Đồ án:** Thiết kế hệ thống PicoRV32 tích hợp bộ tăng tốc Sobel và đánh giá PPA bằng OpenLane.

**Nền tảng đã chốt:** OpenLane Classic, SKY130 `sky130A / sky130_fd_sc_hd`. Người dùng chạy simulation và OpenLane; trợ lý chuẩn bị nguồn, kiểm tra tĩnh, phân tích và sửa lỗi.

## Trạng thái ngày 2026-09-12

**Mới nhất:** `repair_08` còn antenna 4 net/5 pin, slew max_ss 12/nom_ss 6, cap 2 và fanout 25; LVS/DRC PASS, flow chưa đạt. Đã chuẩn bị và precheck `repair_09`: dùng native post-DRT antenna repair để giữ dây làm đầu vào và cập nhật routing theo net thay đổi. Đi từ checkpoint RUN 7 (2/2) để giữ mốc tốt hơn. Xem [chẩn đoán RUN 8](ASIC_REPAIR08_REVIEW.md) và [lệnh chạy](ASIC_RUN_GUIDE.md). RUN 9 chưa chạy.

Đã có RTL tích hợp CPU + Sobel MMIO, hai firmware RV32I, testbench CPU thực thi, checker từng pixel/sự kiện theo vùng và desktop replay. **Người dùng đã chạy `soc_image_smoke_01`: core/MMIO và hai bản CPU đạt kiểm tra chức năng cho ảnh 37 × 35. SW = 573.713 chu kỳ; HW = 774.758 chu kỳ, nhiều hơn 35,04%.** Trợ lý đã đối chiếu lại ZIP, hash, toàn bộ pixel và sự kiện tile mà không chạy lại mô phỏng. Xem [đánh giá simulation](FIRST_RUN_REVIEW.md).

Firmware hiện có SW 1.600 byte và HW 1.416 byte, GCC 13.2.0, RV32I/ILP32 `-O2`. HEX và hash đã kèm trong `firmware/generated`; lần test đầu không cần cài compiler RISC-V. Icarus 12.0 compile được cả hai cấu hình; mỗi cấu hình có hai warning upstream về sensitivity của mảng `cpuregs`. Chưa phải kết quả lint OpenLane.

Phần ASIC dự kiến tổng hợp là **CPU + Sobel + bus interface**, không gồm program/image RAM ngoài do testbench mô hình hóa. [ARCHITECTURE.md](ARCHITECTURE.md) ghi memory map, phạm vi và phép đo.

**Lịch sử base_01:** ASIC `picorv32_sobel_clk50_base_01` đã chạy, DRC/LVS/XOR sạch nhưng chưa đạt antenna (14 net/15 pin), slew (33), capacitance (8) và fanout (61). Đã sửa cấu hình vật lý và lỗi hiển thị stage trong collector; config/lint/SDC-load bản sửa đã qua precheck. Bản repair_02 sau đó đã chạy; kết quả mới nhất và lệnh repair_04 ở đầu tài liệu. Xem [chẩn đoán base_01](ASIC_BASE01_REVIEW.md). Lint vẫn có 33 ngoại lệ style upstream được ghi nhận; không có checker vật lý nào bị tắt.

## Chạy mốc CPU xử lý ảnh — nhập trong Ubuntu

Các lệnh dưới đây ghi lại quy trình RUN đầu tiên. **RUN `soc_image_smoke_01` đã hoàn tất; giữ nguyên, không chạy lại hoặc ghi đè.** RUN tiếp theo sau khi sửa nguồn phải dùng tag mới. Copy giữ nguyên RUN/evidence cũ.

**1. Copy nguồn Windows sang Ubuntu:**

```bash
bash "/mnt/e/aa. PPA_Project_List/aaa.PicoRV32_Sobel_ASIC_PPA/scripts/00_copy_to_ubuntu.sh"
```

**2. Vào thư mục chạy:**

```bash
cd "$HOME/openlane_projects/picorv32_sobel_asic_ppa"
```

**3. Kiểm tra tĩnh, không mô phỏng:**

```bash
bash scripts/01_precheck.sh
```

Điều kiện tiếp tục: `STATIC CHECK PASS`. Kiểm tra compile core, MMIO và hai cấu hình SoC, cú pháp script và hash firmware/input. Nếu lỗi, gửi log tại đường dẫn Evidence được in ra.

**4. Người dùng chạy simulation, RUN đầu tiên:**

```bash
bash scripts/03_run_soc_tests.sh soc_image_smoke_01
```

RUN chạy unit test core/MMIO rồi CPU SW/HW trên cùng ảnh 37 × 35, tile 32, `memory_wait=1`. Terminal hiển thị TILE từ CPU. Mọi nguồn chạy được đóng băng trong RUN. Timeout mỗi subprocess 600 giây, watchdog TB 100 triệu chu kỳ; timeout cần chẩn đoán từ log, không tự coi là lỗi số học.

Điều kiện thành công **sau khi chạy thật**, không phải kết quả đã đạt:

```text
TEST PASS: sobel_core 1283 vectors; latency, busy, done, reset checked
TEST PASS: sobel_mmio register, handshake, arithmetic, error and reset checks
PIXEL CHECK PASS: sw, 1295 pixels, all tile events verified
PIXEL CHECK PASS: hw, 1295 pixels, all tile events verified
FUNCTIONAL TEST PASS: soc_image_smoke_01
```

Chỉ có `CPU EXECUTION COMPLETE` chưa đủ: cần pixel checker thành công. Lỗi sẽ lưu failure.json, log và ZIP bằng chứng đang có. **Không xóa/chạy đè tag**; sau sửa dùng `soc_image_smoke_02`.

**5. Xem bản tổng hợp hiện có:**

```bash
cat reports/soc_image_smoke_01/SUMMARY.txt
```

**6. Copy bằng chứng về Windows, kể cả RUN bị lỗi:**

```bash
bash scripts/04_export_sim.sh soc_image_smoke_01
```

File về `E:\aa. PPA_Project_List\aaa.PicoRV32_Sobel_ASIC_PPA\reports\soc_image_smoke_01.zip`. Gửi ZIP hoặc báo đã export để trợ lý đọc. Chụp terminal có FUNCTIONAL TEST PASS và SW/HW cycles để lưu minh chứng. Không chạy lại chỉ để đọc số liệu.

RUN gồm SUMMARY.txt, comparison.json nếu PASS, run_config.json, tool_versions.json, commands.json, log test, firmware/RTL/input snapshot và hash. Mỗi thư mục sw/hw có pixels.csv, tiles.csv, execution.json và output.pgm sau khi kiểm chứng. Thời gian simulator trên máy tính được tách riêng với chu kỳ mục tiêu.

## Xem hoạt ảnh từ RUN đã PASS

Đây là **replay**, chỉ đọc output và sự kiện CPU đã chạy. Trên Ubuntu có Tkinter:

```bash
python3 scripts/replay.py reports/soc_image_smoke_01
```

Hoặc giải nén ZIP tại Windows thành thư mục cùng tên trong reports, rồi dùng **PowerShell** với Python có Tkinter:

```powershell
python "E:\aa. PPA_Project_List\aaa.PicoRV32_Sobel_ASIC_PPA\scripts\replay.py" "E:\aa. PPA_Project_List\aaa.PicoRV32_Sobel_ASIC_PPA\reports\soc_image_smoke_01"
```

Giao diện có ảnh vào, SW/HW, Play/Pause, thanh kéo và tốc độ cycles/giây màn hình. Tile hiện ở mốc hoàn thành thật, hai phương án cùng thang chu kỳ. RUN đầu tiên cho thấy HW tốn nhiều chu kỳ hơn SW. Đã có trace thật được kiểm chứng; giao diện replay chưa được kiểm tra trực quan trong phiên này.

## Thử ảnh và điều kiện khác sau mốc đầu

Ảnh tối đa 512 × 512, không bắt buộc 32 × 32; tile mặc định mới là 32 × 32. Chuyển PNG/JPEG sang pixel xám cần Pillow; không tự resize hay ghi đè. Đổi đường dẫn nguồn bên dưới thành file ảnh thật:

```bash
python3 scripts/prepare_image.py --source "/duong/dan/anh.png" --output inputs/my_image_01
```

```bash
bash scripts/03_run_soc_tests.sh soc_real_image_01 --image inputs/my_image_01
```

Đổi điều kiện bộ nhớ với cùng ảnh demo:

```bash
bash scripts/03_run_soc_tests.sh soc_wait3_01 --memory-wait 3
```

Có thể thêm `--vcd` để bắt bus khi cần; không cần cho RUN đầu tiên. Core test kiểm tra 1.283 cửa sổ cộng giao thức/reset; một ảnh đầu tiên không thay kiểm chứng toàn bộ kích thước, dữ liệu và độ trễ.

## Biên dịch lại firmware khi nguồn thay đổi

Chỉ cần sau sửa C/assembly/linker hoặc muốn dùng compiler khác. Trên Ubuntu đã cài gcc-riscv64-unknown-elf và binutils-riscv64-unknown-elf:

```bash
bash scripts/build_firmware.sh
```

Đây là compilation, không chạy CPU. Script tạo build/firmware_... mới lưu nguồn, ELF/disassembly/map; cập nhật HEX hiện hành và manifest. RUN cũ giữ firmware riêng. Khi build qua WSL tại Windows workspace, script dùng được compiler giải nén trong build/toolchain; compiler không được copy sang project Ubuntu.

## Mốc tiếp theo

Người dùng chạy `scripts/06_run_openlane.sh picorv32_sobel_clk50_repair_06 picorv32_sobel_clk50_repair_04` theo ASIC_RUN_GUIDE.md để đánh giá bản sửa vật lý. Giữ base_01 để so sánh lỗi, area/power/timing và congestion. Mục tiêu DRC/LVS/antenna sạch cần actual reports; không suy ra PASS từ precheck hay 81/81.

Xem [quy trình OpenLane](OPENLANE_WORKFLOW_NOTES.md), [so sánh PDK](PDK_COMPARISON.md) và [nguồn PicoRV32](third_party/picorv32/PROVENANCE.md).
