# Test ảnh nhỏ Shapes — kế hoạch đang áp dụng

**Cập nhật 2026-09-13:** bản Tile DMA đã được triển khai và compile/lint, chưa chạy simulation. Bước hiện tại là `soc_shapes32_dma_01` theo [TILE_DMA_RUN_GUIDE.md](TILE_DMA_RUN_GUIDE.md). Các lệnh/diễn giải baseline dưới đây là lịch sử; chưa chạy OpenLane cho bản mới.


Cập nhật 2026-09-13 theo yêu cầu người dùng: 32x32 trước, 64x64 sau.
Hoãn bộ SIPI 256/512. RUN soc_shapes32_00_01 đã được người dùng chạy và đã kiểm chứng PASS; các RUN tiếp theo chưa được xác nhận.

## Kiểm tra đầu vào

- output_32x32: 20 PNG, tất cả đúng 32x32, mode L 8-bit, một frame, đọc được.
- output_64x64: 20 PNG, tất cả đúng 64x64, mode L 8-bit, một frame, đọc được.
- Mỗi nhóm có 20 hash riêng. Tên output_* là đầu ra của script trích xuất ảnh,
  nhưng được dùng làm INPUT cho Sobel, không phải kết quả Sobel đã tính sẵn.
- Script người dùng extract_shapes_x32x64.py đọc X_train từ shapes.npz, tạo PNG
  xám 64x64 và resize LANCZOS xuống 32x32. Trợ lý chỉ đọc script, không chạy lại.
  Hash dưới đây nhận diện các PNG thực tế; chưa xác minh nguồn dataset hoặc phiên bản
  Pillow đã dùng lúc trích xuất. label_0/label_1 không được dùng làm golden Sobel.
- Ảnh có cả mức xám trung gian; không threshold, tăng tương phản hoặc resize lại.
  So sánh SW/HW trên đúng byte ảnh đang có. Resize có thể làm biên khác ảnh 64;
  không yêu cầu output 32 phải bằng output 64 thu nhỏ.

## Bốn RUN đầu tiên, chạy tuần tự

| RUN | Input đã chuẩn bị | Pixels | Tile | Số vùng mỗi SW/HW |
|---|---|---:|---|---:|
| soc_shapes32_00_01 | inputs/shapes32_00_01 | 1024 | 16x16 | 4 |
| soc_shapes32_01_01 | inputs/shapes32_01_01 | 1024 | 16x16 | 4 |
| soc_shapes64_00_01 | inputs/shapes64_00_01 | 4096 | 16x16 | 16 |
| soc_shapes64_01_01 | inputs/shapes64_01_01 | 4096 | 16x16 | 16 |

Mỗi input lấy shape_00_label_0 hoặc shape_01_label_1 tương ứng. Trợ lý đã chạy
scripts/prepare_image.py để tạo input.pgm, image.hex, image.json và kiểm tra toàn bộ
byte/hash nguồn. Đây chỉ là chuẩn bị dữ liệu, không thực thi CPU hay tạo ảnh Sobel.
Pillow 12.3.0 dùng ở Windows để chuẩn bị; Ubuntu không cần Pillow cho bốn RUN này.

Dừng sau mỗi RUN để đọc kết quả. Khi hai RUN 32 đạt thì sang 64; sau bốn RUN đạt
mới mở rộng 18 ảnh còn lại mỗi kích thước, theo lô nhỏ. Chưa cấp lệnh chạy đồng loạt 40 ảnh.
Giữ test 37x35 cũ làm bằng chứng về tile cuối không đầy. Tile16 được chọn để có nhiều
vùng trên ảnh nhỏ; không so tốc độ với RUN tile32 cũ như cùng điều kiện.

## Lệnh Ubuntu — bắt đầu bằng RUN đầu tiên

Copy đầu vào đã chuẩn bị và nguồn; RUN cũ vẫn giữ nguyên:

```bash
bash "/mnt/e/aa. PPA_Project_List/aaa.PicoRV32_Sobel_ASIC_PPA/scripts/00_copy_to_ubuntu.sh"
```

```bash
cd "$HOME/openlane_projects/picorv32_sobel_asic_ppa"
```

Người dùng chạy simulation thực tế:

```bash
bash scripts/03_run_soc_tests.sh soc_shapes32_00_01 --image inputs/shapes32_00_01 --tile 16 --memory-wait 1
```

Điều kiện đạt: core/MMIO unit tests PASS; PIXEL CHECK PASS cho sw và hw với 1024
pixel, xác minh đủ 4 vùng mỗi phương án; FUNCTIONAL TEST PASS: soc_shapes32_00_01.
CPU EXECUTION COMPLETE riêng lẻ chưa đủ. Nếu lỗi gửi log/failure.json, không chạy đè tag.

Export bằng chứng kể cả simulation lỗi:

```bash
bash scripts/04_export_sim.sh soc_shapes32_00_01
```

Xem replay sau PASS, cần Tkinter/GUI ở Ubuntu:

```bash
python3 scripts/replay.py reports/soc_shapes32_00_01
```

Chỉ sau khi đã kiểm tra RUN trước, các lệnh tiếp theo là:

```bash
bash scripts/03_run_soc_tests.sh soc_shapes32_01_01 --image inputs/shapes32_01_01 --tile 16 --memory-wait 1
```

```bash
bash scripts/03_run_soc_tests.sh soc_shapes64_00_01 --image inputs/shapes64_00_01 --tile 16 --memory-wait 1
```

```bash
bash scripts/03_run_soc_tests.sh soc_shapes64_01_01 --image inputs/shapes64_01_01 --tile 16 --memory-wait 1
```

Với mỗi RUN, thay đúng tên trong lệnh export/replay ở trên. Timeout giữ 600 giây
mỗi subprocess và watchdog giữ 100 triệu chu kỳ. Chưa có lý do sửa giới hạn cho bộ nhỏ;
đây không phải bảo đảm thời gian chạy. Không bật VCD mặc định, trace pixels/tiles đủ replay.

## Kết quả và phạm vi

Ảnh Sobel SW/HW phải khớp từng pixel với golden 3x3: zero padding biên toàn ảnh,
min(255,abs(Gx)+abs(Gy)). CPU chạy firmware thật trong RTL simulation. Ghi cycles,
wall time và timestamp vùng, gồm đọc ảnh/MMIO/control/ghi output. Replay dùng output
đã kiểm chứng; tốc độ phát khác tốc độ ASIC. Không hứa bản HW nhanh hơn SW.

Không sửa RTL/firmware/SDC, không chạy OpenLane lại vì đổi ảnh. RUN10 vẫn là mốc
Antenna/LVS/DRC/slew/cap đạt, fanout27 còn cần xử lý. Các ảnh thử mới không tự tạo
power theo workload; power vật lý hiện vẫn vectorless.

## Hash PNG gốc được kiểm tra

- `images 2/output_32x32/shape_00_label_0_32x32.png`: `6fe73a97d97358c070ec1cce8e6d6d56490847a00576b12ac49340c72873db76`
- `images 2/output_32x32/shape_01_label_1_32x32.png`: `d283b13394eeadafbabbfbbdf3a63a596f99ac6dade063980013a4206cc44191`
- `images 2/output_32x32/shape_02_label_1_32x32.png`: `2cdb05b4891cff4e76bd1cd480340361d8b01c192fe863533bdb48a5cf92034c`
- `images 2/output_32x32/shape_03_label_0_32x32.png`: `1727794cb3638af75b80c6eae27e2e173572fc22e3bceb738ef6fb38365b7691`
- `images 2/output_32x32/shape_04_label_0_32x32.png`: `970f37ff3d59dca3e7af673c914b79ce15487b00a591796be5f22dac7530796a`
- `images 2/output_32x32/shape_05_label_0_32x32.png`: `d7e05279d380c80fd1df85c292736243c5dd139b9b8bfc973711712d55476179`
- `images 2/output_32x32/shape_06_label_0_32x32.png`: `8b0758a14173ec0835b2bab980fdfcb403c37b817cbe51b97bb47d733f4e27e6`
- `images 2/output_32x32/shape_07_label_0_32x32.png`: `784c959a274f38f92e860b2ef2003f9acb95f969af861a3952b22a2313ead83b`
- `images 2/output_32x32/shape_08_label_0_32x32.png`: `637b89b2e15f07dcdbfeca65a4c413e0157948bbccb8321a822255f6d6a06f6b`
- `images 2/output_32x32/shape_09_label_0_32x32.png`: `6b90840ca93bd28fcc634f527b93b84f4e98d4a71f816eefe3ee57d20f74d966`
- `images 2/output_32x32/shape_10_label_1_32x32.png`: `b2c6a49a60298cf9e1035fe41a27aa77c06058e6cc9d0215942069efaafa07b3`
- `images 2/output_32x32/shape_11_label_0_32x32.png`: `d1f0f94d12ee0c4f2ed1ba0617d6627d449c44a0a83b8f0b3e0afe00e75b6004`
- `images 2/output_32x32/shape_12_label_0_32x32.png`: `c31ae9d50607081d165d60ba5a49c30471a2031fdb1788ff2f81049787cb6439`
- `images 2/output_32x32/shape_13_label_0_32x32.png`: `f595ad2608187b3477b61889be116ea412cd4869466109f2246f81153e39877e`
- `images 2/output_32x32/shape_14_label_0_32x32.png`: `8fb13859c09e7450f57417e0546678698237584ba66540ae304fea739eac7cd7`
- `images 2/output_32x32/shape_15_label_1_32x32.png`: `45268d1cb87d51215459498a6499b76472a60d97bfe6ca5c84ed071af942e3df`
- `images 2/output_32x32/shape_16_label_0_32x32.png`: `f41c722a83c41a4e07657a201d9461b33b622b20e4d706c2ed89348787053d09`
- `images 2/output_32x32/shape_17_label_0_32x32.png`: `8f6402c5e5929ecccb5b9bc98ff94cba61e3732453ff3ebac4cad7d788a6326b`
- `images 2/output_32x32/shape_18_label_1_32x32.png`: `fb5751abf867415efef37399fec26e16acfc25f7fa85976b88386761140017d5`
- `images 2/output_32x32/shape_19_label_0_32x32.png`: `e8f7ecf4fec66fd82472d3c87ff157c7ff7717a79158eb7dab4e3ce0ab0f3938`
- `images 2/output_64x64/shape_00_label_0_64x64.png`: `1b3875e29dcfc39b004adf2e22a38b413f635b397e3378236aa167c4f41a7a36`
- `images 2/output_64x64/shape_01_label_1_64x64.png`: `c351b25b5508e4a3ec036b63a2b38e5453e91b337bd235043e242c3010e4a009`
- `images 2/output_64x64/shape_02_label_1_64x64.png`: `a247efda9272c88904adc4043029a78789f206a39a62e58ae1c4f0799560b007`
- `images 2/output_64x64/shape_03_label_0_64x64.png`: `1688d562280665e1094fdaeba7378027a258da68c9dee09faad01ae97e2ca076`
- `images 2/output_64x64/shape_04_label_0_64x64.png`: `2699adff6e8f1089b5cbbbacedbc79a88a378fb06331f47bed30a5852aa8cfb9`
- `images 2/output_64x64/shape_05_label_0_64x64.png`: `d44a21ffba5cb578371c83f2a76e678ca10c1edc941b03e2b26e32839ccaa8f8`
- `images 2/output_64x64/shape_06_label_0_64x64.png`: `398c2215697868528a936424ae37f306276ab1a1bb357bbb4633fa134b29ee67`
- `images 2/output_64x64/shape_07_label_0_64x64.png`: `d66de074819c3ff3f9418c0f5c10fc2ff86de70fd0051572970d0c663dd0e47f`
- `images 2/output_64x64/shape_08_label_0_64x64.png`: `4037e4b15a5b37173346bf2162f4597b94789f915fd999ab877790adc536f3be`
- `images 2/output_64x64/shape_09_label_0_64x64.png`: `5f0d414ce5347d3ff130a1bc423e943f6e8fc8a63b639fceebae1b8677b49918`
- `images 2/output_64x64/shape_10_label_1_64x64.png`: `9f61861d6ad080e0bea5ca0f66549055813c7bce34d8e350aa604de8292e5112`
- `images 2/output_64x64/shape_11_label_0_64x64.png`: `52c906fd3854785bd5123ef10e4281178964545485259ebef30e9d52a2b0c119`
- `images 2/output_64x64/shape_12_label_0_64x64.png`: `288783f29de049a217c2f8ce55f52ae15ba87021930dc9037fff78df45bcee45`
- `images 2/output_64x64/shape_13_label_0_64x64.png`: `4465e60ebb7e3160d11213e1fe46303cb0b61cd121b8b077d172c6af2aa229a9`
- `images 2/output_64x64/shape_14_label_0_64x64.png`: `dcff0833d44af3dbabfaed2ea71295cd56c0f7d41d0abfd40d75a8ae53de29a8`
- `images 2/output_64x64/shape_15_label_1_64x64.png`: `4abbc458182d673c75c4c802e3ca4f18af3e117a4c3b533f6606834fc0835173`
- `images 2/output_64x64/shape_16_label_0_64x64.png`: `d664f3a76c60d1cd3f68fcd82facaafded3ae0818d0064ce4bd37d1913f67fad`
- `images 2/output_64x64/shape_17_label_0_64x64.png`: `020a7723d45f5dcc52a922f4b3769c5906f4133b2f59a18d2292e4cbef9c0c3c`
- `images 2/output_64x64/shape_18_label_1_64x64.png`: `675dc9905f3bc72da496901510cfca33326b5561a1cc0182850116be1397a5bb`
- `images 2/output_64x64/shape_19_label_0_64x64.png`: `685713f4a24b7532aeb248f1db32bcd94e4860c1b653d3d0d67fc8fe867f58f7`

## Kết quả soc_shapes32_00_01 đã xác minh — 2026-09-13

Archive reports/soc_shapes32_00_01.zip đã export về Windows.
SHA256: `666a49591ec9b10856aea196717a9cfbcb660b40ec7833e565e381124995dd0c`.
Trợ lý đọc bản sao audit, không chạy lại mô phỏng: toàn bộ input/output hash đúng,
firmware hợp lệ; RTL/TB/firmware/vendor hiện hành khớp snapshot; cả 1024 pixel và
4 tile mỗi SW/HW khớp golden và timestamp hợp lệ; PGM gốc khớp byte sau đối chiếu.

| Phương án | Chu kỳ đo | Wall time vvp trên host |
|---|---:|---:|
| CPU chạy Sobel bằng phần mềm | 453421 | 10.081 s |
| CPU + Sobel MMIO | 613171 | 14.993 s |

SW/HW = 0.739469. Bản HW cần nhiều hơn 159750 chu kỳ, tương đương 35.2322%.
Đúng chức năng, chưa chứng minh tăng tốc. Kiến trúc hiện tại CPU vẫn đọc pixel,
ghi start/data MMIO, polling và đọc result từng pixel; chưa có counter phân loại
chi phí để xác định từng phần đóng góp vào độ chậm.

TILE cycle là mốc tuyệt đối trong testbench. Khoảng đo bỏ phần boot trước start:
SW 453720-299=453421; HW 613484-313=613171. $finish là kết thúc bình thường sau PASS.
Warning cpuregs là sensitivity upstream đã gặp ở smoke test, không phải pixel mismatch.
ASIC checks NOT_RUN trong summary này nghĩa là RUN simulation không thực hiện PNR;
không phủ nhận RUN vật lý repair_10. FAIL_OR_INCOMPLETE của collector ASIC trước đó
vẫn do 27 fanout, không phải lỗi của test ảnh vừa chạy.

Bước tiếp theo: mở replay RUN này, rồi chạy soc_shapes32_01_01 theo lệnh bên trên.
Không chạy đè soc_shapes32_00_01 và chưa chuyển lên ảnh SIPI lớn.
