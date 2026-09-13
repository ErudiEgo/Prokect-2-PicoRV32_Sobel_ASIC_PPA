# Tối ưu PicoRV32 + Sobel: giữ baseline, giảm chi phí giao tiếp

Ngày 2026-09-13. Người dùng xác nhận GUI replay hoạt động, hiển thị vùng 16x16
đúng mong muốn. Chưa chạy simulation hoặc physical flow mới trong lần phân tích này.

## Baseline đã đo

soc_shapes32_00_01: 32x32, tile16, memory_wait1, 1024 pixel, 4 tile.
SW453421 cycles; CPU+Sobel613171 cycles. Chênh159750 cycles (+35.2322%).
Cả hai output đã kiểm chứng từng pixel. GUI khớp số đo, không có bằng chứng cho
rằng số liệu hiển thị sai. Không đổi thang thời gian riêng cho HW để tạo tăng tốc giả.
Giữ snapshot/ZIP và RUN10 vật lý. RUN10 đạt các check antenna/LVS/DRC/slew/cap,
fanout27 còn tồn tại; không gán kết quả đó cho phần cứng tối ưu chưa chạy PNR.

## Chi phí xác định từ source, chưa phải profile đo động

firmware/main.c/filter thực hiện trên mỗi output pixel:
1. CPU đọc tối đa 8 byte hàng xóm (ngoài biên trả zero), tính địa chỉ/kiểm tra biên.
2. HW path đóng gói và ghi 2 word dữ liệu vào Sobel.
3. Ghi 1 word start.
4. Đọc status ít nhất một lần trong vòng polling, kiểm tra lỗi và timeout.
5. Đọc 1 word result; CPU ghi pixel vào RAM như SW path.

Như vậy HW có tối thiểu 5 giao dịch MMIO/pixel, hay 5120 giao dịch cho 1024 pixel,
chưa gồm đọc ID, host tile events, RAM/instruction fetch và status poll bổ sung.
Đây là cận dưới suy ra từ mã, không phải bộ đếm transaction đã đo trong RUN.

rtl/sobel_core.v nhận start ở cạnh N, tính Gx/Gy, xuất magnitude ở cạnh N+1.
Core ngắn nhưng CPU+MMIO phải điều khiển lại cho từng pixel. Đây là cơ sở để ưu tiên
giảm granularity giao tiếp hơn việc chỉ rút ngắn phép cộng/trừ. Chưa gán toàn bộ
159750 chu kỳ chênh cho polling hoặc bus nếu chưa có counter phân loại.

## Trình tự thực hiện đề xuất

1. Giữ ảnh 32x32 hiện tại làm baseline chung. Thêm bộ đếm chỉ ở testbench để đo
   instruction fetch, RAM read/write, MMIO data/start/status/result transactions,
   wait cycles và core busy cycles trong cùng cửa sổ start/end. Các nhóm cycle
   phải không trùng nếu cộng thành tổng; busy của core có thể chồng CPU nên báo riêng.
   Đếm đúng handshake valid&&ready, không đếm mỗi chu kỳ valid là một giao dịch.
   Không dùng host wall time thay cycle count. Compile và static-check trước,
   người dùng chạy RUN tên mới. Instrumentation không nằm trong ASIC/PPA.
2. Thử giảm overhead giao thức ở phạm vi nhỏ sau khi có profile: auto-start khi
   nạp đủ dữ liệu, hoặc read-result có handshake chờ kết quả để giảm polling.
   Giữ giao thức cũ hoặc version hóa rõ, kiểm tra reset/busy/backpressure/duplicate
   transaction và lỗi truy cập. Chưa khẳng định riêng bước này sẽ vượt SW.
3. Nếu nạp 8 hàng xóm vẫn chiếm lớn, hướng kiến trúc chính là streaming/batch:
   tái sử dụng hàng/cột pixel trong line buffer, CPU cấp một chuỗi dữ liệu thay vì
   gửi lại cả cửa sổ cho từng pixel. Cần định nghĩa biên ảnh/tile, buffer hữu hạn,
   backpressure, output ordering và chi phí truyền trước khi viết RTL. Line buffer
   là phần cứng mới, ảnh hưởng area/power, phải được tính vào physical top.
   DMA/arbiter truy cập RAM là mở rộng riêng, không mặc định có sẵn trong thiết kế.
4. Mỗi thay đổi chạy lại ảnh32 cùng tile16/memory_wait1 và checker golden hiện có;
   sau đó ảnh32 thứ hai, ảnh64, test37x35 tile không đầy, rồi mới mở rộng SIPI.
5. Chỉ sau chức năng và tốc độ đã có bằng chứng mới chạy OpenLane cho RTL mới,
   đo PPA/checkers lại. Mục tiêu SW_cycles/HW_cycles>1 là tiêu chí, chưa phải kết quả.

## So sánh công bằng

Nếu tối ưu SW (con trỏ hàng, tái sử dụng pixel, bỏ phép nhân địa chỉ lặp), lưu một
baseline SW mới cùng baseline cũ; không làm SW chậm đi để HW thắng. Giữ cùng image,
border zero padding, min(255,abs(Gx)+abs(Gy)), tile, memory model và phạm vi đo gồm
transfer/control/output. Giữ tách biệt cycles và clock period thực tế khi so latency.
Power hiện vectorless; cycle giảm không tự chứng minh năng lượng giảm. Không gộp
area/power CPU+Sobel thành area/power CPU-only.

Không sửa RTL, firmware hoặc giao diện replay trong lần phân tích này. Đây là lộ
trình dựa trên source và baseline; các thay đổi cần được triển khai/kiểm chứng tiếp.
