# Tile DMA v1 — kết quả RUN đầu tiên

RUN: `soc_shapes32_dma_01`, người dùng thực thi; ngày đánh giá 2026-09-13.
Ảnh `shapes32_00_01`, 32 × 32, tile 16 × 16, memory_wait=1. Không chạy lại simulation khi đánh giá.

| Chỉ số | PicoRV32 SW | PicoRV32 + tile DMA |
|---|---:|---:|
| Chu kỳ trong khoảng đo | 453421 | 69406 |
| Pixel đúng với golden | 1024/1024 | 1024/1024 |
| Tile được xác minh | 4/4 | 4/4 |
| Thời gian simulator trên máy người dùng (s) | 11.942030 | 2.671418 |
| CPU instruction-fetch transactions | 85018 | 8108 |
| DMA input reads | 0 | 7812 |
| DMA output writes | 0 | 1024 |

Speedup theo chu kỳ = 453421/69406 = **6.532879×**.
Giảm thời gian tại cùng clock = (1−69406/453421)×100 = **84.692813%**.
Mục tiêu giảm 15–20% đã đạt trên trường hợp này; chưa suy rộng sang mọi ảnh hoặc chip sau layout.
Firmware SW và số chu kỳ SW giữ nguyên so với baseline trước tối ưu. HW cũ cần 613171 chu kỳ;
HW mới cần 69406, nhưng đối chứng chính để báo cáo tăng tốc là SW cùng RUN.

## Kiểm chứng bằng chứng

- Bốn unit test core, MMIO, tile engine và arbiter đều có TEST PASS; tất cả command exit0.
- Đã kiểm tra lại 59 hash nguồn đóng băng, 10 hash trace/output/profile, manifest firmware,
  toàn bộ 1024 pixel mỗi phương án và thứ tự/thời điểm bốn tile bằng checker golden.
- Output PGM SW/HW giống từng byte, hash `4bfd45818ee37f3c709a53e756f82033249edb80405825872aad1f15712c41c9`.
- Snapshot RTL/firmware/TB/scripts/dependency khớp nguồn hiện hành tại lúc đánh giá.
- Profile partition bằng end_cycle−start_cycle: SW299..453720, HW379..69785.
- ZIP giữ nguyên ở reports/soc_shapes32_dma_01.zip.
- SHA256 ZIP: `310e264337e2f5b417ddc5f2c01cdb69e83e0655aef71f55509bad7ef5c226da`.

## Diễn giải và giới hạn

CPU khởi động đúng bốn tile. Engine thực hiện 7812 lần đọc hàng xóm trong ảnh và 1024 lần ghi
output; hàng xóm ngoài ảnh dùng zero padding nên không tạo DMA read. CPU không phải thực hiện
vòng lọc từng pixel, số instruction-fetch transactions giảm từ85018 còn8108. Phép đo vẫn gồm
cấu hình, truy cập RAM, chờ bộ tăng tốc, lưu kết quả và sự kiện tile.

HW có 988 lần đọc status. Profile tile_busy=67864, dma_wait=47764 và cpu_wait=44041 chu kỳ;
đây là các khoảng chồng lấp, không được cộng thành tổng thời gian. Nếu tối ưu tiếp có thể xem
việc đọc lại các hàng xóm và tranh chấp bus, nhưng ưu tiên mở rộng kiểm chứng trước khi đổi RTL.

Wall time11.942s/2.671s là thời gian simulator chạy trên máy; không phải thời gian chip.
Hai warning Icarus về sensitivity của cpuregs xuất hiện ở cả SW/HW, không làm RUN này thất bại.
ASIC PPA và Antenna/LVS/DRC/timing/fanout của RTL DMA mới: **NOT_RUN**. RUN10 thuộc kiến trúc
cũ, không được gán PPA hoặc các PASS đó cho bản mới. RAM ngoài vẫn là mô hình testbench.

## Bước tiếp theo — người dùng chạy trong Ubuntu

Có thể xem ngay replay đã xác minh, không chạy lại CPU:

```bash
cd "$HOME/openlane_projects/picorv32_sobel_asic_ppa"
python3 scripts/replay.py reports/soc_shapes32_dma_01
```

Giữ nguyên RTL/firmware và điều kiện RAM, kiểm tra ảnh32 thứ hai:

```bash
bash scripts/03_run_soc_tests.sh soc_shapes32_dma_02 --image inputs/shapes32_01_01 --tile 16 --memory-wait 1
```

```bash
bash scripts/04_export_sim.sh soc_shapes32_dma_02
```

Nếu FUNCTIONAL TEST PASS, tiếp tục ảnh64 (4096 pixel, 16 tile mỗi phương án):

```bash
bash scripts/03_run_soc_tests.sh soc_shapes64_dma_01 --image inputs/shapes64_00_01 --tile 16 --memory-wait 1
```

```bash
bash scripts/04_export_sim.sh soc_shapes64_dma_01
```

Giữ nguyên RUN cũ. Nếu lỗi thì thu ZIP và dừng để chẩn đoán; chưa sửa hoặc chạy lại cùng tag.
Sau đó kiểm tra kích thước lẻ/partial tile và memory_wait khác, rồi chuẩn bị full OpenLane RUN
cho RTL mới. Chưa chạy mô phỏng hoặc physical flow nào trong phiên đánh giá này.

## Đối chiếu tính công bằng theo câu hỏi người dùng

Đã so trực tiếp hai ZIP soc_shapes32_00_01 và soc_shapes32_dma_01: firmware SW và image.hex giống từng byte. SW HEX SHA256=df573f5febf0a4072dbcd4c853bdce07fb97ef6427cc9042225b5209c0c22f3e. Số chu kỳ SW vẫn453421. Cờ GCC chung -O2/-march=rv32i/-mabi=ilp32, CPU parameters giống nhau, TB clock và memory_wait chung. Không có delay/NOP cố ý trong đường lọc SW; NOP sau completion nằm ngoài khoảng đo. Nhánh SW đi thẳng RAM; nhánh DMA mới chịu arbitration và contention thật.

Giới hạn đối chứng: SW là C cơ bản, không phải bản nhanh nhất đã được chứng minh. IMAGE là volatile, nên các lần đọc lân cận không tự được loại bỏ như dữ liệu thường; có kiểm tra biên và tính địa chỉ. Disassembly có __mulsi3, nhưng không được suy luận mỗi hàng xóm đều gọi phép nhân: compiler đã thực hiện một số tối ưu. Cả hai CPU đều không có M extension. Không đổi lựa chọn ISA giữa hai bên để tạo lợi thế.

Cách ghi kết quả chính xác: 6.532879× theo chu kỳ so với firmware C baseline -O2 trên PicoRV32 RV32I, cho ảnh32/tile16/memory_wait1; chưa phải mọi phần mềm Sobel hay số đo chip sau layout. Muốn đối chứng mạnh hơn, giữ baseline nguyên và bổ sung SW optimized (con trỏ hàng, xử lý biên riêng, tái sử dụng pixel khi hợp lệ), cùng golden và khoảng đo. Có thể thêm SW chạy trên chính SoC có DMA nhưng DMA idle để phân biệt chi phí arbiter; chưa thực hiện các RUN đó. Chấp nhận số tăng tốc giảm nếu baseline tối ưu nhanh hơn, không sửa số để giữ mục tiêu.

Kiểm tra lưu trữ: RUN01 có thư mục và ZIP Ubuntu, ZIP Windows. RUN02 chưa có thư mục/ZIP ở cả hai nơi tại lúc kiểm tra. Log dừng ở replay GUI; đóng replay hoặc mở terminal mới rồi chạy RUN02.
