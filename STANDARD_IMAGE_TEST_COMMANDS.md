# Lệnh test bộ ảnh chuẩn — Ubuntu

Ảnh gốc nằm trong Windows `test image`. Không đổi tên/xóa bộ ảnh cũ.
Mỗi RUN thực thi SW baseline và DMA HW cùng ảnh xám8bit, tile16, memory_wait1.
Đổi ảnh không cần đổi RTL hoặc chạy lại OpenLane. Script không tự resize ảnh.

## Chuẩn bị một lần sau cập nhật script

```bash
bash "/mnt/e/aa. PPA_Project_List/aaa.PicoRV32_Sobel_ASIC_PPA/scripts/00_copy_to_ubuntu.sh"
```
```bash
cd "$HOME/openlane_projects/picorv32_sobel_asic_ppa"
```
Nếu Ubuntu chưa có Pillow (ModuleNotFoundError: PIL), cài gói để đọc PNG/JPEG/TIFF:
```bash
sudo apt update
sudo apt install python3-pil
```

## Ý nghĩa tham số

- prepare_image.py --source: đường dẫn FILE gốc, đặt trong dấu ngoặc kép nếu có khoảng trắng.
- prepare_image.py --output: THƯ MỤC INPUT mới, chứa image.hex, image.json, input.pgm; không phải kết quả Sobel.
- 03_run_soc_tests.sh: đối số đầu tiên là tên RUN duy nhất, không trùng RUN cũ.
- --image: thư mục INPUT đã chuẩn bị, không nhận JPEG/TIFF trực tiếp.
- --tile16: mỗi vùng16×16; không phải kích thước toàn ảnh. Giữ nguyên để so sánh.
- --memory-wait1: độ trễ RAM chung SW/HW; giữ nguyên trong bộ benchmark chính.
- --timeout-seconds: giới hạn thời gian máy chạy mỗi subprocess; không thay đổi clock mô phỏng.
- --max-cycles: watchdog số chu kỳ tổng mỗi phương án, không thay đổi số chu kỳ hoàn thành.

A/B là tên do ta đặt trong input/RUN, không tự chọn ảnh. File --source mới quyết định ảnh nào được dùng.
Nếu test lại cùng input, bỏ lệnh prepare, giữ --image và đặt RUN mới (..._02). Không xóa RUN cũ.
Nếu đổi ảnh, đặt input mới và RUN mới. Không ghi đè input cũ.

## Ví dụ đầy đủ cho từng trường hợp

Chạy lần lượt từng lệnh của MỘT trường hợp. Chỉ chạy simulation sau khi INPUT READY.
Nếu simulation lỗi, export bằng chứng rồi gửi log; không chạy lại cùng tag.

### 32×32 — ảnh A: shape_00_label_0_32x32.png

Chuẩn bị dữ liệu (chỉ một lần cho input này):
```bash
python3 scripts/prepare_image.py --source "/mnt/e/aa. PPA_Project_List/aaa.PicoRV32_Sobel_ASIC_PPA/test image/32x32/shape_00_label_0_32x32.png" --output inputs/std32_a_01
```
Chạy CPU simulation:
```bash
bash scripts/03_run_soc_tests.sh soc_std32_a_01 --image inputs/std32_a_01 --tile 16 --memory-wait 1 --timeout-seconds 600 --max-cycles 100000000
```
Xuất ZIP về Windows khi kết thúc:
```bash
bash scripts/04_export_sim.sh soc_std32_a_01
```
Xem replay sau FUNCTIONAL TEST PASS:
```bash
python3 scripts/replay.py reports/soc_std32_a_01
```

### 64×64 — ảnh A: 00001.png

Chuẩn bị dữ liệu (chỉ một lần cho input này):
```bash
python3 scripts/prepare_image.py --source "/mnt/e/aa. PPA_Project_List/aaa.PicoRV32_Sobel_ASIC_PPA/test image/64x64/00001.png" --output inputs/std64_a_01
```
Chạy CPU simulation:
```bash
bash scripts/03_run_soc_tests.sh soc_std64_a_01 --image inputs/std64_a_01 --tile 16 --memory-wait 1 --timeout-seconds 600 --max-cycles 100000000
```
Xuất ZIP về Windows khi kết thúc:
```bash
bash scripts/04_export_sim.sh soc_std64_a_01
```
Xem replay sau FUNCTIONAL TEST PASS:
```bash
python3 scripts/replay.py reports/soc_std64_a_01
```

### 128×128 — ảnh A: 00000002.jpg

Chuẩn bị dữ liệu (chỉ một lần cho input này):
```bash
python3 scripts/prepare_image.py --source "/mnt/e/aa. PPA_Project_List/aaa.PicoRV32_Sobel_ASIC_PPA/test image/128x128/00000002.jpg" --output inputs/std128_a_01
```
Chạy CPU simulation:
```bash
bash scripts/03_run_soc_tests.sh soc_std128_a_01 --image inputs/std128_a_01 --tile 16 --memory-wait 1 --timeout-seconds 1800 --max-cycles 100000000
```
Xuất ZIP về Windows khi kết thúc:
```bash
bash scripts/04_export_sim.sh soc_std128_a_01
```
Xem replay sau FUNCTIONAL TEST PASS:
```bash
python3 scripts/replay.py reports/soc_std128_a_01
```

### 128×128 — ảnh B: 00000007.jpg

Chuẩn bị dữ liệu (chỉ một lần cho input này):
```bash
python3 scripts/prepare_image.py --source "/mnt/e/aa. PPA_Project_List/aaa.PicoRV32_Sobel_ASIC_PPA/test image/128x128/00000007.jpg" --output inputs/std128_b_01
```
Chạy CPU simulation:
```bash
bash scripts/03_run_soc_tests.sh soc_std128_b_01 --image inputs/std128_b_01 --tile 16 --memory-wait 1 --timeout-seconds 1800 --max-cycles 100000000
```
Xuất ZIP về Windows khi kết thúc:
```bash
bash scripts/04_export_sim.sh soc_std128_b_01
```
Xem replay sau FUNCTIONAL TEST PASS:
```bash
python3 scripts/replay.py reports/soc_std128_b_01
```

### 256×256 — ảnh A: 4.1.05.tiff

Chuẩn bị dữ liệu (chỉ một lần cho input này):
```bash
python3 scripts/prepare_image.py --source "/mnt/e/aa. PPA_Project_List/aaa.PicoRV32_Sobel_ASIC_PPA/test image/256x256/4.1.05.tiff" --output inputs/std256_a_01
```
Chạy CPU simulation:
```bash
bash scripts/03_run_soc_tests.sh soc_std256_a_01 --image inputs/std256_a_01 --tile 16 --memory-wait 1 --timeout-seconds 3600 --max-cycles 100000000
```
Xuất ZIP về Windows khi kết thúc:
```bash
bash scripts/04_export_sim.sh soc_std256_a_01
```
Xem replay sau FUNCTIONAL TEST PASS:
```bash
python3 scripts/replay.py reports/soc_std256_a_01
```

### 512×512 — ảnh A: 4.2.07.tiff

Chuẩn bị dữ liệu (chỉ một lần cho input này):
```bash
python3 scripts/prepare_image.py --source "/mnt/e/aa. PPA_Project_List/aaa.PicoRV32_Sobel_ASIC_PPA/test image/512x512/4.2.07.tiff" --output inputs/std512_a_01
```
Chạy CPU simulation:
```bash
bash scripts/03_run_soc_tests.sh soc_std512_a_01 --image inputs/std512_a_01 --tile 16 --memory-wait 1 --timeout-seconds 7200 --max-cycles 250000000
```
Xuất ZIP về Windows khi kết thúc:
```bash
bash scripts/04_export_sim.sh soc_std512_a_01
```
Xem replay sau FUNCTIONAL TEST PASS:
```bash
python3 scripts/replay.py reports/soc_std512_a_01
```

## Lưu kết quả ở đâu?

- Input chuẩn bị trong Ubuntu: ~/openlane_projects/picorv32_sobel_asic_ppa/inputs/<INPUT>/.
- Kết quả Ubuntu: ~/openlane_projects/picorv32_sobel_asic_ppa/reports/<RUN>/.
- ZIP tự tạo khi runner kết thúc: reports/<RUN>.zip (kể cả failure nếu runner đã tạo RUN).
- Sau script04: E:\aa. PPA_Project_List\aaa.PicoRV32_Sobel_ASIC_PPA\reports\<RUN>.zip.
- SUMMARY.txt/comparison.json: số chu kỳ, speedup, host time, trạng thái.
- sw/ và hw/: output.pgm, pixels.csv, tiles.csv, profile.json, log thực thi.
- inputs/ trong RUN: nguồn RTL/TB/firmware và ảnh đóng băng, hash đi kèm.
- script04 không xuất thư mục input làm việc riêng, nhưng ZIP bao gồm input đóng băng đủ để đối chiếu RUN.
- Reports và raw images ngoài Git. Backup riêng; Git push không thay việc lưu ZIP.

Đóng cửa sổ replay để trở lại prompt terminal trước khi gõ lệnh mới, hoặc dùng terminal Ubuntu khác.
Không kill Ubuntu trong khi simulation đang chạy.

## Kết quả cần có

| Ảnh | Pixel mỗi SW/HW | Tile16 mỗi SW/HW |
|---|---:|---:|
|32×32|1024|4|
|64×64|4096|16|
|128×128|16384|64|
|256×256|65536|256|
|512×512|262144|1024|

Bốn unit TEST PASS, PIXEL CHECK PASS cho cả hai phương án, cuối cùng FUNCTIONAL TEST PASS.
512 chưa được thực thi: 250M watchdog là giới hạn chuẩn bị, không phải số đo/đảm bảo PASS.
Từ RUN256 có thể dự trù SW~118Mcycles, host tổng~53phút nếu tỷ lệ tuyến tính; nội dung/máy có thể đổi số thực.
Không bật VCD mặc định ở ảnh lớn để tránh file trace nặng. Pixel/tile/profile vẫn được lưu.

Các kích thước trong bộ hiện chứa nội dung ảnh khác nhau; bảng này là nhiều workload,
không phải thí nghiệm chỉ thay đổi độ phân giải của cùng ảnh. Muốn kết luận scaling thuần,
cần thêm cùng một ảnh chuẩn ở nhiều độ phân giải với quy tắc resize được ghi nhận.

## Thay đổi công cụ phục vụ512

Testbench có plusarg max_cycles, runner có --max-cycles ghi vào run_config.json và commands.json.
Mặc định100M giữ nguyên; kiểm tra khoảng1..2 tỷ. Áp dụng cùng giới hạn cho SW/HW.
Không đổi RTL, firmware, phép đo hoặc pixel checker. Compile/static PASS; chưa chạy simulation mới.
