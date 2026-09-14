# Tile DMA v1 — bản tối ưu chuẩn bị ngày 2026-09-13

**Cập nhật 2026-09-13:** RUN `soc_shapes32_dma_01` đã hoàn tất FUNCTIONAL PASS: SW453421/HW69406 chu kỳ, speedup6,532879×, giảm84,692813% tại cùng clock. Không chạy lại tên RUN này. Phần chuẩn bị/compile bên dưới ghi lịch sử trước lần chạy; xem [đánh giá và RUN tiếp theo](TILE_DMA_FIRST_RUN_REVIEW.md). ASIC mới vẫn NOT_RUN.

## Mục tiêu và trạng thái

Mục tiêu người dùng: tăng tốc tối thiểu khoảng 15-20%, cao hơn nếu có thể.
Để không nhập nhằng, báo cả speedup=SW_cycles/HW_cycles và mức giảm thời gian
100*(1-HW_cycles/SW_cycles) ở cùng clock. Giảm thời gian 20% tương đương speedup1.25x.
Không thay đổi benchmark để tạo kết quả đạt mục tiêu. Chưa có số đo phiên bản này.

Baseline cũ soc_shapes32_00_01: SW453421, HW613171 cycles, 32x32/tile16/memory_wait1.
Bản mới giữ nguyên byte firmware SW (1600 byte, HEX SHA256
`df573f5febf0a4072dbcd4c853bdce07fb97ef6427cc9042225b5209c0c22f3e`).
Firmware HW mới 652 byte, GCC13.2 RV32I/ILP32 -O2; file manifest đã cập nhật.

Đã chạy compilation/static checks cho core/MMIO/tile/arbiter/cả hai SoC,
Verilator lint nguồn vật lý, kiểm tra hash và Bash/Python syntax.
Không chạy vvp, synthesis, OpenLane hoặc bất kỳ physical step nào.
Chưa gọi unit test là PASS chỉ vì compile được.
Audit compile: build/static_l8oXk3Dj; lint: build/tile_lint_ReV31Yin.

## Thay đổi cụ thể

- Giữ nguyên sobel_core.v và sobel_mmio.v cũ, gồm ID/giao thức xử lý từng pixel.
- Thêm sobel_tile.v: CPU cấu hình một vùng rồi phần cứng tự đọc tám hàng xóm,
  gọi core Sobel, ghi từng byte kết quả vào RAM ngoài. Không cache/line buffer,
  không lưu toàn ảnh trong ASIC, không có phép nhân địa chỉ trong engine.
- Thêm native_bus_arbiter.v: CPU và DMA dùng cùng cổng RAM ngoài, cùng memory_wait.
  Transaction không bị ngắt khi đang chờ; chọn DMA trước khi rảnh, thả quyền sau
  handshake và một khoảng chuyển tiếp. CPU có thể bị chờ thật, thời gian đó được đo.
  Bản CPU-only bypass arbiter; không cố ý làm chậm SW để tạo speedup.
- Bản HW CPU vẫn boot, thực thi firmware, cấu hình và đợi từng tile rồi ghi tile event.
  Testbench không tính Sobel thay phần cứng; chỉ cung cấp RAM và thu bằng chứng.
- Toàn bộ register cấu hình tile và đợi done nằm trong measurement window. Chỉ ID
  và boot ban đầu ở ngoài, giống baseline. Tile event được CPU gửi sau mọi output store.
- Giữ zero-padding ở biên toàn ảnh; qua biên tile đọc pixel thật của ảnh bên cạnh.
  Byte lane của RAM32-bit được chọn theo địa chỉ, một byte ghi mỗi pixel.

## ABI TIL1 tại SOBEL_BASE=0x40000000

| Offset | Chức năng |
|---|---|
| 0x00..0x14 | Giao tiếp Sobel từng pixel cũ, không thay đổi |
| 0x80 | Control: bit0 start, bit1 clear error, bit2 clear done; ghi đủ word |
| 0x84 | Status: bit0 busy, bit1 sticky done, bit2 sticky error |
| 0x88 | height[31:16], width[15:0], mỗi chiều1..512 |
| 0x8c | tile_y[31:16], tile_x[15:0] |
| 0x90 | tile_height[31:16], tile_width[15:0], mỗi chiều1..64 |
| 0x94 | Địa chỉ pixel input góc trên trái của tile: 0x10000+y*width+x |
| 0x98 | Địa chỉ pixel output góc trên trái của tile: 0x50000+y*width+x |
| 0x9c | ID read-only 0x54494c31 (TIL1) |

CPU chịu trách nhiệm tính pointer đúng origin/width; engine kiểm tra descriptor
và vùng địa chỉ, không nhân lại y*width để xác minh pointer. DMA chỉ đọc input region
0x10000..0x4ffff, chỉ ghi output region0x50000..0x8ffff. Mọi DMA request alignedword;
byte lane giữ tọa độ byte thật. Partial MMIO, địa chỉ MMIO sai và ghi khi busy đặt
sticky error; ghi khi busy không sửa descriptor hoặc khởi động lại. Reset toàn hệ
thống hủy giao dịch trong engine và arbiter, xóa done/error.

## Kiểm chứng đã chuẩn bị để người dùng chạy

- Unit test cũ sobel_core và sobel_mmio vẫn chạy.
- tb_sobel_tile: ảnh1x1, kích thước lẻ, tile nội bộ/biên/không đầy, byte lanes,
  golden từng pixel, không ghi ngoài tile hoặc lặp pixel, memory backpressure,
  sửa descriptor khi busy, descriptor lỗi, partial writes, reset trong transaction.
- tb_native_bus_arbiter: CPU/DMA tranh chấp, nhiều độ trễ, owner giữ ổn định,
  không acknowledge hai master cùng lúc, kiểm tra số transaction và reset.
- SoC chạy SW và HW cùng ảnh. Checker golden/pixel/tile cũ không đổi.
- Profile TB theo valid&&ready, không lái DUT. Các nhóm CPU idle/fetch/MMIO/data
  chia toàn khoảng end-start; CPU wait, DMA wait và busy là số chồng lấp, không cộng
  vào tổng lần hai. Assert số DMA output writes đúng width*height, starts đúng số tile;
  SW phải không dùng DMA. profile.json được hash cùng trace để đưa vào evidence.

## Người dùng chạy RUN nhỏ đầu tiên trong Ubuntu

```bash
bash "/mnt/e/aa. PPA_Project_List/aaa.PicoRV32_Sobel_ASIC_PPA/scripts/00_copy_to_ubuntu.sh"
```

```bash
cd "$HOME/openlane_projects/picorv32_sobel_asic_ppa"
```

```bash
bash scripts/03_run_soc_tests.sh soc_shapes32_dma_01 --image inputs/shapes32_00_01 --tile 16 --memory-wait 1
```

Lệnh gồm bốn unit test rồi SW/HW CPU simulation. Cần TEST PASS ở từng unit,
PIXEL CHECK PASS cho 1024 pixel/4 tile mỗi phương án, và FUNCTIONAL TEST PASS.
Time reduction vs SW là số đo từ RUN, tách riêng với chức năng PASS.
Nếu chưa đạt tốc độ, không sửa nhãn PASS hoặc giấu kết quả; đọc profile trước.

Thu bằng chứng kể cả khi lỗi:

```bash
bash scripts/04_export_sim.sh soc_shapes32_dma_01
```

Sau khi PASS, mở replay từ trace thực:

```bash
python3 scripts/replay.py reports/soc_shapes32_dma_01
```

Giữ tên mới nếu phải sửa/chạy lại; không ghi đè soc_shapes32_00_01 hoặc *_dma_01.
Sau khi xem kết quả lần đầu, mở rộng ảnh32 thứ hai, ảnh64 và demo37x35, cùng điều kiện
đối chứng; thử memory_wait0 và3 để kiểm tra backpressure. Hoãn ảnh256/512 như yêu cầu.

## Phạm vi ASIC và bước còn lại

Physical top mới gồm PicoRV32, legacy MMIO+core, tile controller+core riêng và arbiter.
Hai core tồn tại để giữ giao tiếp cũ; chi phí diện tích phải được tính đầy đủ. External
program/image/output RAM, testbench, profiler, host event logger, GUI/pads/package
không nằm trong ASIC. Bus pinout và SDC chưa đổi, nhưng netlist và đường timing đã đổi.

RUN10 là PPA của kiến trúc cũ, không chứng minh antenna/timing/area/power của bản mới.
Chưa chạy OpenLane mới. Config đã thêm đúng RTL mới; physical precheck yêu cầu
archive soc_shapes32_dma_01 và hash nguồn mới, không nhận evidence smoke cũ thay thế.
Raw config khác baseline nên không tiếp tục từ checkpoint repair_10 cho netlist mới.
Sau chức năng và benchmark đạt mới chuẩn bị RUN ASIC đầy đủ và đánh giá lại fanout,
Antenna/LVS/DRC/timing/area/utilization/power; power vẫn vectorless nếu chưa có activity.
