# RGB tuần tự trên nền RUN16

Nhánh: `codex/rgb-from-run16`, từ tag `run16-baseline`, commit `e9ff741064810c1ce893745581a2d89917b0b238`.
Ngày chuẩn bị: 2026-09-15. **RGB32 đã FUNCTIONAL PASS**: `soc_rgb32_smoke_01`, SW1352946/HW206960 chu kỳ. ZIP/hash/pixel/timestamp đã audit; xem [đánh giá](RGB32_FIRST_RUN_REVIEW.md). **ASIC mới: CHƯA CHẠY.** Các lệnh bước2 là lịch sử RUN đã hoàn tất; không chạy lại tag01. Tiếp theo: bước3.

## Những gì thay đổi

- Một CPU thực thi một chương trình cho toàn ảnh; mỗi tile xử lý R rồi G rồi B. DMA/core RUN16 được tái sử dụng, không có ba core song song.
- SW và HW cùng dùng ảnh RGB8 planar, zero-padding tại biên toàn ảnh, phép Sobel `min(255, abs(Gx)+abs(Gy))` độc lập trên từng kênh. Cả hai chương trình cùng compiler/flags RV32I `-O2`; không thêm delay vào SW.
- Mỗi tile chỉ hoàn thành khi đã ghi đủ cả ba kênh. Chu kỳ đo bao gồm vòng lặp kênh, fetch ảnh, tính toán/điều khiển CPU, MMIO, DMA, ghi kết quả và tile events. Không đo thời gian Pillow giải mã/đóng gói ảnh hay replay; loại trừ giống nhau ở SW/HW.
- Replay hiển thị ảnh gốc RGB đã giải mã 8 bit và hai kết quả biên RGB từ RTL được kiểm chứng. Không tô màu giả cho Sobel xám. Màu đường biên không phải màu ảnh gốc được khôi phục.
- Giữ tương thích đầu vào/replay xám cũ. Firmware mới có thêm điều khiển kênh nên phải đo lại; không mặc định chu kỳ bằng firmware RUN16 cũ.
- RGB: 1..256 trên mỗi trục. Gray: 1..512. Công cụ từ chối RGB512 trước khi tạo RUN.

## Vì sao RGB512 chưa nằm trong phiên bản này

RUN16 có guard địa chỉ ngay trong RTL DMA: input `[0x10000,0x50000)`, output `[0x50000,0x90000)`, mỗi vùng 256 KiB. Ba plane 256x256 chiếm 196608 byte/vùng và vừa; RGB512 cần 786432 byte/vùng nên không vừa. Tăng RAM testbench một mình không khắc phục được guard phần cứng. Phiên bản này giữ nguyên RTL; RGB512 cần một thiết kế staging có đo chi phí CPU copy hoặc nâng cấp địa chỉ và kiểm chứng vật lý riêng.

RAM ngoài testbench vẫn là 1 MiB, không được tính như SRAM đã tổng hợp trong chip.

| Địa chỉ | Nội dung |
|---|---|
| 0xf000 / 0xf004 / 0xf008 | width / height / tile |
| 0xf00c | channels: 1 hoặc 3, testbench ghi trước khi CPU chạy |
| 0x10000 + c×W×H | input plane c (0=R, 1=G, 2=B) |
| 0x50000 + c×W×H | output plane c |

Nguồn ảnh được chuyển bằng Pillow RGB8, không resize, không EXIF rotation, bỏ alpha và không áp ICC profile. File `original.ppm` lưu RGB đã giải mã đúng kích thước đưa vào test; metadata lưu tên và SHA256 file nguồn. Không coi đây là quy trình quản lý màu chuyên nghiệp.

## Bước 1 — copy vào Ubuntu riêng

Nhập trong Ubuntu; không dùng thư mục chạy RUN16 cũ.

```bash
bash "/mnt/e/aa. PPA_Project_List/aaa.PicoRV32_Sobel_ASIC_PPA/scripts/00_copy_to_ubuntu.sh"
```

```bash
cd "$HOME/openlane_projects/picorv32_sobel_rgb_asic_ppa"
bash scripts/01_precheck.sh
```

Cần thấy `STATIC CHECK PASS`. Precheck chỉ compile và chạy kiểm tra Python host, không thực thi CPU/RTL. Hai cảnh báo sensitivity của mảng cpuregs upstream có thể xuất hiện ở mỗi cấu hình. Firmware HEX đã kèm; không cần compiler để chạy simulation.

## Bước 2 — RGB 32x32, tile16

Ảnh chẩn đoán màu gốc đã kèm `inputs/rgb_smoke32_v1`. Output RUN01 đã lưu trong reports và ZIP; giữ nguyên.

```bash
bash scripts/03_run_soc_tests.sh soc_rgb32_smoke_01 --image inputs/rgb_smoke32_v1 --tile 16 --memory-wait 1 --timeout-seconds 600 --max-cycles 100000000
```

Điều kiện thành công **cần quan sát sau chạy**, không phải kết quả đã đạt:

- Unit tests core/MMIO/tile/arbiter đạt.
- `PIXEL CHECK PASS` ở SW và HW: 1024 pixel / 3072 channel samples, 4 tile events đã kiểm chứng.
- HW profile: DMA writes=3072, tile starts=12. SW không dùng DMA.
- `FUNCTIONAL TEST PASS: soc_rgb32_smoke_01`.

Sau PASS, mở replay (không tự bật khi mô phỏng hoàn tất):

```bash
python3 scripts/replay.py reports/soc_rgb32_smoke_01
```

Export cả khi thất bại để phân tích:

```bash
bash scripts/04_export_sim.sh soc_rgb32_smoke_01
```

ZIP về Windows `reports/soc_rgb32_smoke_01.zip`; không ghi đè file đã có. Trong Ubuntu giữ thư mục `reports/soc_rgb32_smoke_01/` và ZIP. File `SUMMARY.txt`, `comparison.json`, `run16_rtl_basis.json`, snapshots và SHA256 phục vụ kiểm chứng.

## Bước 3 — biên lẻ và regression xám

RGB17x19 tạo bốn tile với cạnh lẻ; mỗi plane323 byte nên G/B không cùng word alignment. Đây là ca quan trọng để phát hiện nhầm byte lane/kênh. Memory-wait=3 kiểm tra stalled bus.

```bash
bash scripts/03_run_soc_tests.sh soc_rgb17x19_partial_01 --image inputs/rgb_partial17x19_v1 --tile 16 --memory-wait 3 --timeout-seconds 600 --max-cycles 100000000
```

Kỳ vọng sau PASS: 323 pixel /969 samples, 4tile, HW969 DMA writes/12tile starts.

```bash
bash scripts/04_export_sim.sh soc_rgb17x19_partial_01
```

Regression xám37x35 trên firmware mới:

```bash
bash scripts/03_run_soc_tests.sh soc_gray_rgbfw_regression_01 --image inputs/demo --tile 16 --memory-wait 1 --timeout-seconds 600 --max-cycles 100000000
```

```bash
bash scripts/04_export_sim.sh soc_gray_rgbfw_regression_01
```

Mỗi tag chỉ dùng một lần. Khi sửa/chạy lại, đổi `_01` thành `_02` trong cả lệnh test, replay, export. Không xoá RUN cũ.

## Sau các ca nhỏ PASS — ảnh màu thật 256x256

Bước này nặng hơn nhiều, chỉ thực hiện sau khi xem kết quả các ca nhỏ. Pillow hiện đã có trong Ubuntu được kiểm tra; nếu môi trường khác thiếu PIL, cài `python3-pil` trước.

```bash
python3 scripts/prepare_image.py --source "/mnt/e/aa. PPA_Project_List/aaa.PicoRV32_Sobel_ASIC_PPA/test image/256x256/4.1.03.tiff" --color rgb --output inputs/rgb256_4103_01
```

Chỉ chạy tiếp khi có `INPUT READY` (không tạo lại cùng thư mục input):

```bash
bash scripts/03_run_soc_tests.sh soc_rgb256_4103_01 --image inputs/rgb256_4103_01 --tile 16 --memory-wait 1 --timeout-seconds 7200 --max-cycles 500000000
```

```bash
bash scripts/04_export_sim.sh soc_rgb256_4103_01
```

```bash
python3 scripts/replay.py reports/soc_rgb256_4103_01
```

Đổi ảnh: sửa `--source`, chọn `--output inputs/<case_mới>`, rồi dùng đúng `--image` và RUN name mới. Dùng `--color gray` cho xám. Không cần đổi RTL để chọn ảnh.

## Evidence và phạm vi PPA

`pixels.csv` RGB có `cycle,x,y,channel,value`; `tiles.csv` giữ một sự kiện cho toàn RGB tile. `execution.json` tách số pixel không gian, channels và samples. Checker đối chiếu từng sample với convolution3x3 độc lập, kiểm tra đủ dữ liệu, không lặp, thứ tự tile và thời điểm. `output.ppm` chỉ xuất sau kiểm tra đúng; gray giữ `output.pgm`.

`run16_rtl_basis.json` xác minh 6 file RTL/CPU theo Git blob RUN16 và ghi SHA256 snapshot hiện tại. Chỉ là quan hệ nguồn: không phải chạy lại PNR hay xác nhận RGB power. RUN16 vẫn có một vi phạm fanout; điện năng từng ảnh RGB và power có activity chưa được đo. Không lấy vectorless power RUN16 làm power đo riêng của RGB. Config/SDC/pinout và RTL giữ nguyên. Không chạy launcher baseline08 trong nhánh này: tên RUN lịch sử vẫn là baseline_06 đã tồn tại.

## Bảo toàn Git

- RUN16 tag/main không thay đổi.
- RUN17/18 nằm trong stash commit `9655c28f108e231d3df66c4824e54f60c41e770f`, được giữ bằng nhánh `codex/preserved-run17-run18`; phần file untracked nằm trong parent thứ ba của stash. Chưa xoá stash.
- Nhánh RGB chưa tự commit/push. Ảnh chẩn đoán nhỏ và firmware HEX được theo dõi; dataset và reports lớn vẫn nằm ngoài Git.
- Không apply stash RUN17/18 lên nhánh RGB. Nếu cần khôi phục thí nghiệm, tạo nhánh riêng từ e9ff741 rồi `git stash apply 9655c28f108e231d3df66c4824e54f60c41e770f` khi working tree sạch.


## Kiểm tra chuẩn bị đã thực hiện

- GCC13.2.0 biên dịch RV32I/ILP32 -O2 -Wall -Wextra -Werror: SW1772byte, HW804byte; manifest/hash hợp lệ.
- Icarus compile core/MMIO/tile/arbiter và cả hai cấu hình SoC đạt; giữ cảnh báo upstream cpuregs đã nêu.
- Năm nhóm kiểm thử Python host: độc lập ba kênh; giới hạn/hash đầu vào; TIFF sang planar và giữ original RGB; đối chiếu/timestamp cho RGB và gray; từ chối sai kênh/pixel, trùng hoặc thiếu sample. Trace kiểm thử là fixture tạm thời, không phải kết quả RTL.
- Nguồn RTL/CPU khớp Git RUN16; config/SDC/pin order không đổi. Kiểm tra đường dẫn copy và import Tkinter/Pillow đạt.
- Tại thời điểm chuẩn bị chưa chạy CPU/RTL; sau đó người dùng đã chạy soc_rgb32_smoke_01 PASS và export ZIP. Trạng thái cập nhật ở đầu tài liệu; ca partial17x19 và gray regression vẫn chưa có kết quả. Chưa chạy OpenLane mới.
