# RGB extension on RUN16 hardware

Current branch adds sequential per-channel RGB firmware, testbench/evidence and replay; synthesizable RTL remains RUN16. See [RGB_RUN_GUIDE.md](RGB_RUN_GUIDE.md) for the current ABI, memory limits and commands. Config word 0xf00c selects 1 or 3 channels. Input/output remain within the existing 256 KiB windows: RGB <=256x256, gray <=512x512. CPU emits one tile event after all channels. RGB32 functional evidence is now PASS (see RGB32_FIRST_RUN_REVIEW.md); new RGB PPA is NOT_RUN.

The text below records the original grayscale architecture and historical development stages.

# Kiến trúc và phạm vi đo — mốc kiểm chứng CPU

**Cập nhật 2026-09-13:** Tile DMA v1 đang ở mức compile/lint, chưa simulation/PNR. Xem [ABI và quy trình mới](TILE_DMA_RUN_GUIDE.md). RUN10 là kiến trúc cũ.

Cập nhật 2026-09-12. Người dùng đã chạy simulation soc_image_smoke_01: ảnh SW/HW đúng từng pixel; đã có kết quả ASIC base_01 nhưng chưa đạt đủ checker; xem ASIC_BASE01_REVIEW.md. Chi tiết tại FIRST_RUN_REVIEW.md.

## Phần cứng

Top `picorv32_sobel_soc` gồm PicoRV32 RV32I, giải mã bus và ngoại vi Sobel MMIO. CPU có 32 thanh ghi, register file dual-port, barrel shifter và bộ đếm; không bật M/D, compressed instructions, IRQ hoặc PCPI. Nguồn CPU giữ nguyên commit `ef203c2b0a3fb793280f5114941416c425c5b461`, giấy phép ISC tại `third_party/picorv32/COPYING`.

`ENABLE_SOBEL=0`: CPU và bus ngoài, ngoại vi trả ID bằng 0. `ENABLE_SOBEL=1`: thêm Sobel core và thanh ghi điều khiển/dữ liệu. Hai biến thể dùng cùng thông số CPU và cùng mô hình bộ nhớ ngoài.

```text
  Ngoài phạm vi ASIC                      RTL top dự kiến tổng hợp
  +------------------------+       +--------------------------------+
  | Testbench              |       | PicoRV32 RV32I                 |
  | RAM byte 1 MiB         | <---> |        | native memory bus     |
  | Firmware + input image | ext_* |   Giải mã địa chỉ              |
  | Output image           |       |        |                       |
  | Ghi CSV + mốc chu kỳ   |       | Sobel MMIO + sobel_core        |
  +------------------------+       +--------------------------------+
            |
  Python: đối chiếu golden, PGM, desktop replay
```

**Program/data/stack RAM, ảnh vào/ra và host ghi log nằm trong testbench, ngoài physical top.** Register file của CPU và thanh ghi Sobel thuộc RTL tổng hợp. Không có SRAM macro, frame buffer hoặc tile RAM trong top hiện tại. Chưa có pad ring, PHY bộ nhớ hay controller DRAM. `ext_*` là bus song song mức logic, chưa phải giải pháp kết nối bộ nhớ trên bo thật.

PPA tương lai phải ghi “CPU + Sobel + giao tiếp bus; không gồm bộ nhớ chương trình/ảnh ngoài”. Không gọi đây là PPA của chip độc lập đã chứa đầy đủ bộ nhớ. Hướng này giữ bài thực hành gọn và vẫn chạy instruction CPU thật; nếu thêm RAM macro sau này, cần thay đổi phạm vi và RUN khác.

## Bản đồ địa chỉ

| Địa chỉ | Ý nghĩa | Nơi hiện thực |
|---|---|---|
| `0x00000000..0x00007FFF` | Ngân sách code/rodata/data/bss 32 KiB; reset PC=0 | RAM ngoài trong TB |
| `0x00008000..0x0000EFFF` | Dự phòng/stack; SP=`0xF000`, tăng trưởng xuống | RAM ngoài trong TB |
| `0x0000F000 / 0xF004 / 0xF008` | width / height / tile, mỗi giá trị 32 bit | TB nạp cấu hình |
| `0x00010000..0x0004FFFF` | Tối đa 512 × 512 pixel vào, mỗi pixel 1 byte | RAM ngoài trong TB |
| `0x00050000..0x0008FFFF` | Pixel đầu ra | RAM ngoài trong TB |
| `0x40000000..0x400000FF` | Sobel MMIO | RTL trong top |
| `0x40010000..0x40010020` | Ghi dấu đo/hoàn thành/lỗi | Host model trong TB |

TB mô hình RAM 1 MiB; ASIC không có RAM 1 MiB. Cả SW/HW dùng cùng độ trễ instruction/load/store. `memory_wait=N` thêm N cạnh đợi trước khi TB đưa ready=1; CPU nhận giao dịch tại cạnh tiếp theo. N=0 vẫn có bắt tay đồng bộ, không phải bộ nhớ zero-cycle.

## Sobel MMIO

Truy cập đúng địa chỉ thanh ghi; ghi đủ 32 bit (`wstrb=1111`). Truy cập lỗi được acknowledge và đặt sticky error.

| Offset | Đọc | Ghi |
|---|---|---|
| `0x00` | 0 | bit 0 start, bit 1 clear error, bit 2 clear done |
| `0x04` | bit 0 active, bit 1 done sticky, bit 2 error sticky | Không hỗ trợ |
| `0x08` | 4 pixel thấp | p00, p01, p02, p10 từ byte thấp lên cao |
| `0x0C` | 4 pixel cao | p12, p20, p21, p22 từ byte thấp lên cao |
| `0x10` | Kết quả 8 bit, bit cao bằng 0 | Không hỗ trợ |
| `0x14` | ID `0x534F424C` | Không hỗ trợ |

Start/ghi pixel khi active đặt error, không thay dữ liệu đang tính. Đọc sai địa chỉ trả `0xDEADBEEF` và đặt error. Bit control chưa định nghĩa bị bỏ qua. Reset đồng bộ xóa dữ liệu, trạng thái và giao dịch đang xử lý.

Core nhận 8 hàng xóm, bỏ pixel giữa; Gx/Gy signed 11 bit, tổng độ lớn 12 bit rồi bão hòa 255. Start được nhận ở cạnh N khi idle, kết quả/done tại N+1. Độ trễ core không phải thời gian xử lý một pixel của toàn hệ thống: CPU còn truyền dữ liệu, start, polling và đọc result.

## Firmware và ảnh

- GCC RV32I/ILP32, `-O2`, cùng source với `USE_ACCEL=0/1`. Host không xử lý ảnh thay CPU.
- Ảnh từ 1 đến 512 pixel mỗi chiều; tile từ 1 đến 64, mặc định 32. Không tự resize.
- SW CPU duyệt pixel theo từng tile. HW CPU cấu hình tile; engine DMA duyệt pixel và đọc8 hàng xóm từ RAM ngoài, không lưu toàn tile vào RAM nội bộ.
- Ngoài biên **toàn ảnh** lấy 0. Qua ranh giới tile vẫn lấy pixel thật từ vùng bên cạnh.
- Kernel Gx=[-1,0,1;-2,0,2;-1,0,1], Gy=[-1,-2,-1;0,0,0;1,2,1]. Output=`min(255,abs(Gx)+abs(Gy))`.
- SW tính số học trên CPU. HW cấu hình một descriptor mỗi tile, chờ done; DMA ghi từng byte output. CPU gửi tile event sau khi cả vùng đã ghi xong. Legacy MMIO từng pixel vẫn được giữ.
- Demo 37 × 35 là đầu vào tự tạo, có 4 tile với tile=32, gradient thấp, cực trị, đường qua x/y=32 và vùng cuối thiếu kích thước. Không phải output giả lập sẵn.

Compiler có thể tạo instruction khác nhau cho hai đường xử lý. Đây là phép đo ứng dụng từ cùng source và mức tối ưu; không hứa HW nhanh hơn. Chi phí truyền pixel/MMIO có thể lấn át số học tiết kiệm được. Số liệu đầu tiên sẽ quyết định có cần gom nhiều pixel hoặc thêm line buffer.

## Chứng cứ và phép đo

RUN đóng băng RTL, vendor/giấy phép, firmware, checker và input; compiler/simulator/checker dùng bản sao đó. Hash liên kết HEX với C/assembly/linker; hash toàn snapshot ở `inputs.sha256.json`.

`pixels.csv` ghi cycle,x,y,value tại cạnh bus RAM chấp nhận store của CPU (SW) hoặc DMA (HW). `tiles.csv` ghi cycle,x,y,width,height,ordinal tại cạnh CPU chấp nhận tile event. Python đối chiếu **từng pixel** với phép tích chập độc lập, kiểm tra số lượng/vị trí, thứ tự tile, vùng cuối và timestamps. Chỉ sau khi kiểm chứng mới tạo `comparison.json` PASS và `output.pgm`.

Khoảng đo từ store start-marker được chấp nhận đến store end-marker được chấp nhận: bao gồm đọc ảnh, tính toán, MMIO, polling, ghi output và tile events. Không gồm boot/ID check ban đầu, host đọc file/golden/replay. Thời gian host chạy `vvp` lưu riêng bằng monotonic clock, không gọi là thời gian chip.

`SW cycles / HW cycles > 1` mới là tăng tốc về chu kỳ trong điều kiện đo. Chưa có Fmax: mỗi biến thể cần timing report riêng. Khi có clock được kiểm chứng mới tính thời gian mục tiêu bằng cycles × period, kèm corner và điều kiện bộ nhớ/I/O.

Replay Tkinter đọc trace thật đã PASS, kiểm tra hash, hiện tile khi tới mốc hoàn thành trên cùng trục elapsed cycles. Mặc định phát khoảng 15 giây, ghi rõ cycles/giây màn hình. Đây là phát lại, không phải CPU đang chạy trực tiếp. Sobel tạo ảnh biên 2D, không render cảnh 3D như Cinebench R23.

## Cổng sang ASIC

Baseline RUN10 đã có báo cáo vật lý, còn fanout27. Tile DMA đổi RTL nên cần simulation mới và một RUN vật lý đầy đủ mới sau khi đánh giá chức năng/tốc độ. Không kế thừa PPA/checker PASS từ RUN10. Chưa chạy ASIC bản Tile DMA.

Báo actual timing theo corner, cell/core/die area và utilization, power cùng nguồn hoạt động/giả định, IR drop cùng nguồn/tải, DRC/LVS/antenna và kiểm tra điện. Mục tiêu antenna 0 nets/0 pins và DRC/LVS PASS; thiếu báo cáo hoặc checker chưa chạy ghi NOT_RUN/MISSING. Không tắt checker để có PASS.
