# Kế hoạch thử ảnh USC-SIPI cho PicoRV32 + Sobel

**HOÃN từ 2026-09-13:** theo yêu cầu người dùng, ưu tiên bộ Shapes 32x32 rồi 64x64.
Áp dụng [SMALL_IMAGE_TEST_PLAN.md](SMALL_IMAGE_TEST_PLAN.md); chưa chạy các lệnh 256/512 bên dưới. Đây là kế hoạch giai đoạn sau.

Kiểm tra ngày 2026-09-12. Đây là kế hoạch test, chưa có simulation RUN mới.
Không thay đổi TIFF gốc, RTL, firmware, giới hạn test hoặc kết quả cũ.

## Kết quả kiểm kê

20 TIFF đều giải mã đầy đủ bằng Pillow 12.3.0, một frame, không có thẻ orientation.
14 ảnh 256x256 (8 RGB, 6 xám); 6 ảnh 512x512 (5 RGB, 1 xám).
Mỗi kênh 8 bit; không có TIFF 16-bit hoặc nhiều trang cần quy tắc xử lý bổ sung.
Không có hash file trùng nhau. Việc giải mã thành công chưa chứng minh ảnh là bản
nguyên gốc từ máy chủ; hash dưới đây nhận diện chính xác các file người dùng cung cấp.

Tên mô tả đối chiếu theo [USC-SIPI Miscellaneous](https://sipi.usc.edu/database/database.php?volume=misc&image=18).
Trang người dùng dẫn tới ảnh 5.1.13, Resolution chart, 256x256 xám.

| File trong images | Mô tả theo SIPI | Kích thước | Mode |
|---|---|---|---|
| `4.1.01.tiff` | Female (NTSC test image) | 256x256 | RGB |
| `4.1.02.tiff` | Couple (NTSC test image) | 256x256 | RGB |
| `4.1.03.tiff` | Female (from Bell Labs?) | 256x256 | RGB |
| `4.1.04.tiff` | Female | 256x256 | RGB |
| `4.1.05.tiff` | House | 256x256 | RGB |
| `4.1.06.tiff` | Tree | 256x256 | RGB |
| `4.1.07.tiff` | Jelly beans | 256x256 | RGB |
| `4.1.08.tiff` | Jelly beans | 256x256 | RGB |
| `4.2.01.tiff` | Splash | 512x512 | RGB |
| `4.2.03.tiff` | Mandrill / Baboon | 512x512 | RGB |
| `4.2.05.tiff` | Airplane (F-16) | 512x512 | RGB |
| `4.2.06.tiff` | Sailboat on lake | 512x512 | RGB |
| `4.2.07.tiff` | Peppers | 512x512 | RGB |
| `5.1.09.tiff` | Moon surface | 256x256 | L |
| `5.1.10.tiff` | Aerial | 256x256 | L |
| `5.1.11.tiff` | Airplane | 256x256 | L |
| `5.1.12.tiff` | Clock | 256x256 | L |
| `5.1.13.tiff` | Resolution chart | 256x256 | L |
| `5.1.14.tiff` | Chemical plant | 256x256 | L |
| `5.2.08.tiff` | Couple (NTSC test image) | 512x512 | L |

## Bộ test chính và thứ tự

| Bước | Ảnh | Tile 32 | Mục đích | RUN dự kiến |
|---|---|---:|---|---|
| 1 | 5.1.13, 256x256 | 64 vùng | Đường nét, mẫu tần số cao; thử luồng TIFF xám và đo thời gian thực tế | soc_sipi_chart256_01 |
| 2 | 4.1.05, 256x256 | 64 vùng | Ảnh nhà, đường viền kiến trúc; thử chuyển RGB sang xám, demo dễ đọc | soc_sipi_house256_01 |
| 3 | 5.1.14, 256x256 | 64 vùng | Chi tiết công nghiệp phức tạp hơn | soc_sipi_plant256_01 |
| 4 | 4.2.07, 512x512 | 256 vùng | Ảnh màu với đường cong, mở rộng workload | soc_sipi_peppers512_01 |
| 5 | 4.2.03, 512x512 | 256 vùng | Nhiều texture, đánh giá đầu ra dày cạnh và clipping | soc_sipi_mandrill512_01 |

Chạy tuần tự, kiểm tra từng RUN trước khi tiếp tục. Chưa cần chạy cả 20 ảnh.
Các ảnh còn lại là bộ mở rộng; 5.1.12 Clock có thể dùng thay ảnh nhà cho demo xám.
Đây là lựa chọn test dựa trên loại nội dung, không phải dự đoán ảnh nào tăng tốc hơn.
Giữ test 37x35 trước đây để kiểm tra tile cuối không đầy và đường nối vùng: bộ ảnh
256/512 chia hết cho 32 nên không thay thế được test đó.

## Chuẩn hóa đầu vào

- Giữ TIFF gốc trong images; không cần đổi JPEG, tránh thêm nén mất dữ liệu.
- scripts/prepare_image.py đã dùng Pillow nên có thể đọc TIFF dù help chỉ nêu PNG/JPEG/PGM.
- Chuyển RGB rồi L theo đúng pipeline hiện tại, xuất input.pgm, image.hex, image.json.
  Với ảnh L 8-bit, đường chuyển này giữ giá trị xám. Không resize/crop/auto-contrast/sharpen.
- Ghi hash TIFF, kích thước, cách chuyển và phiên bản Pillow vào provenance.
- CPU không giải mã TIFF: host chuyển file thành byte; testbench nạp byte vào RAM ngoài.
- Giới hạn bộ nhớ phù hợp 512x512 xám: input 0x10000..0x4ffff,
  output 0x50000..0x8ffff, nằm trong RAM 1 MiB của testbench. RAM này không nằm trong GDS.
- images đang bị gitignore. Script copy sang Ubuntu chỉ copy inputs, chưa copy images.
  Do đó lệnh chuẩn bị đọc TIFF trực tiếp từ /mnt/e, không giả định Ubuntu có images.
- Giữ hash/tên nguồn trong Git qua tài liệu này; chưa đưa TIFF hoặc trace lớn vào Git.

## Giới hạn cần giải quyết trước khi chạy ảnh lớn

Mốc đo thật 37x35: SW 573713 chu kỳ / 14.755 s; HW 774758 chu kỳ / 19.508 s.
Nếu ngoại suy tuyến tính theo số pixel (chỉ để dự trù, không phải kết quả benchmark):
256x256 khoảng SW 29 triệu / HW 39 triệu chu kỳ, tổng thời gian host khoảng 29 phút;
512x512 khoảng SW 116 triệu / HW 157 triệu chu kỳ, tổng thời gian host khoảng 116 phút.
Nội dung, phép nhân địa chỉ, overhead cố định và máy host có thể làm số thật khác nhiều.
Không ghi các dự trù này vào bảng kết quả đo.

- Timeout hiện tại 600 giây MỖI subprocess: có nguy cơ dừng cả ảnh 256.
  Dùng tham số sẵn có --timeout-seconds 3600 cho RUN 256 đầu tiên; không bỏ timeout.
- tb/tb_sobel_soc.sv hiện watchdog cố định 100000000 chu kỳ toàn simulation.
  Tăng wall timeout không sửa được watchdog. CHƯA chạy 512 trước khi chuẩn bị watchdog
  có cấu hình/hữu hạn, ghi vào run_config và frozen snapshot, compile kiểm tra lại.
- Không sửa watchdog trong RUN cũ hoặc tự coi timeout là lỗi số học. Cần đọc tiến độ tile/log.
- Không bật --vcd cho benchmark lớn mặc định. pixels.csv/tiles.csv đã đủ cho replay.
- Ubuntu hiện chưa có Pillow. Cần python3-pil ở bước chuẩn bị TIFF; replay GUI cần
  python3-tk và WSLg/display. Icarus/vvp đã dùng trong RUN trước, kiểm tra lại nếu môi trường đổi.

## Lệnh cho RUN 256 đầu tiên — người dùng chạy, không chạy cả bộ cùng lúc

Các lệnh này là bước thực hiện kế hoạch khi sẵn sàng. Không có lệnh OpenLane mới.
Nếu đường dẫn input hoặc tag đã tồn tại, chọn tên mới; không xóa/ghi đè.

```bash
sudo apt install python3-pil python3-tk
```

```bash
bash "/mnt/e/aa. PPA_Project_List/aaa.PicoRV32_Sobel_ASIC_PPA/scripts/00_copy_to_ubuntu.sh"
```

```bash
cd "$HOME/openlane_projects/picorv32_sobel_asic_ppa"
```

```bash
python3 scripts/prepare_image.py --source "/mnt/e/aa. PPA_Project_List/aaa.PicoRV32_Sobel_ASIC_PPA/images/5.1.13.tiff" --output inputs/sipi_chart256_01
```

```bash
bash scripts/03_run_soc_tests.sh soc_sipi_chart256_01 --image inputs/sipi_chart256_01 --tile 32 --memory-wait 1 --timeout-seconds 3600
```

Điều kiện đạt: SW và HW đều PIXEL CHECK PASS với 65536 pixel và 64 tile mỗi phương án,
rồi FUNCTIONAL TEST PASS: soc_sipi_chart256_01. CPU EXECUTION COMPLETE riêng lẻ chưa đủ.

Thu bằng chứng kể cả khi lỗi:

```bash
bash scripts/04_export_sim.sh soc_sipi_chart256_01
```

Sau PASS, mở replay trên Ubuntu có GUI:

```bash
python3 scripts/replay.py reports/soc_sipi_chart256_01
```

## Kết quả cần thu và cách diễn giải

Mỗi RUN: ảnh xám đầu vào; output.pgm SW/HW; đối chiếu golden từng pixel, zero padding
biên toàn ảnh, min(255,abs(Gx)+abs(Gy)); timestamp và thứ tự 64/256 tile; cycle count;
wall time từng simulation; tỷ lệ SW cycles/HW cycles; nguồn/firmware/ảnh/config đóng băng.
Hai phương án dùng cùng ảnh, tile, memory_wait và tính đủ đọc pixel/MMIO/control/ghi kết quả.

Replay cho thấy các vùng hoàn thành từ trace CPU thật. Đây là phát lại sau simulation,
chưa phải renderer live hay mô phỏng netlist hậu layout. Tốc độ phát không phải MHz ASIC.
Không chạy lại OpenLane cho từng ảnh khi RTL/config vật lý chưa đổi. Thay ảnh đổi workload,
không tự sinh một số area hoặc power mới. Power RUN 10 hiện vectorless, chưa phải power
đo theo switching activity của từng TIFF. PPA hiện là CPU + Sobel, không gồm RAM/pads/package.
Không dùng diện tích/power CPU+Sobel làm baseline vật lý CPU-only. Fanout 27 còn là việc riêng.

## SHA256 ảnh gốc

- `4.1.01.tiff`: `c3ea2466396790c8aa0e4a60bc5031c44a3288da666cfd6a4f732ae0fec5efad`
- `4.1.02.tiff`: `31d1e7aafff59f5754ee38b77287ee6cfa05a095e63bb245fc44af87fa9d0329`
- `4.1.03.tiff`: `3d9cf65ca9a43a674cd7fd80192902458921aa81885a16bdcf9dd738e406af62`
- `4.1.04.tiff`: `abb652cfa55da20b95941834f8887d0dccfa71e33c94dc16ec0c473111dac15e`
- `4.1.05.tiff`: `6cecbf11be31a64a8397463b24b32cc753a657a616a80b147c93e4579f4c734e`
- `4.1.06.tiff`: `f09642b452f6c82bccd1282f45b46e4603630c2863708f27079a676e65c928ef`
- `4.1.07.tiff`: `ee21b55963d29ed18effeef9a4dc3edc85208d9b79690bf2339c14649dcf41f6`
- `4.1.08.tiff`: `8fd360f5cf6d230eff7934599edf0024995b6da69146e9c85bbaaf327d4a2abc`
- `4.2.01.tiff`: `f27f806d2f5e3d6b66e4223bad6a9fcd38756c715491eafb38c43a9befe89cfd`
- `4.2.03.tiff`: `3f590b52279fb59b81906f1e928ae713a5357b1afc1a2017a103adb563fb4494`
- `4.2.05.tiff`: `ae9eba12b80df955e47585bf4a16332ea0dadc753668d3457c509564934dbd40`
- `4.2.06.tiff`: `aa00ff3defadcd99e2e5fb5fbd06d12d6570284822a37186e3f8827f9bb4ca73`
- `4.2.07.tiff`: `676c21edcc56b517ebd54764d6026d2befe7e15014ec3f0c9e6f2ce1d9ad74bf`
- `5.1.09.tiff`: `64210a233aeaf4c8d76232daa2b8e9dabd251c89e00771b5b316b60e4844d2e4`
- `5.1.10.tiff`: `046ade1c2ee9a92117a0373b54db79d27e2fdc724649c7c15ae3fdb95fca0522`
- `5.1.11.tiff`: `475b9329d3def5f97c2e73c82d2d532accbcdd50de2999e72e47cfcdeb6a7c13`
- `5.1.12.tiff`: `ec07e39dd5a342e91d56852a971d45bd3ec31ccca778ade7ebcfe47a2fc215ac`
- `5.1.13.tiff`: `92ef9dd86f3c0edbbcdad50d63229d6633df560308b60b96cb045e570be02e18`
- `5.1.14.tiff`: `d42dc6b19d2f041a0ada000ac8d028e9caa9a3a4a1f4396110191ecf137a7050`
- `5.2.08.tiff`: `000a3e36a04b954cefd86d8ab2ac61676034e6cc9e3c0bbab8aaa95bcff03b93`
