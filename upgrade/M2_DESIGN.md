# M2 — software S1 và so sánh cùng phần cứng

Ngày2026-09-17. S1 đã có mã và được compile; functional/cycle results trên RV32 vẫn USER_RUN_REQUIRED. DMA v2 chưa triển khai; ASIC stage2 NOT_RUN.

## Thay đổi đã thực hiện

- Thêm firmware S1 ở firmware/s1; giữ nguyên main.c, start.S, linker và HEX S0/H1 nền. S1 định danh mode2, S0mode0, H1mode1.
- S1 tính row pointers một lần mỗi hàng trong tile, trượt cửa sổ theo chiều ngang và giữ cột đã đọc trong biến. Phép Sobel signed, zero-padding ở biên toàn ảnh và saturation255 giữ nguyên. Tile/channel/output order giống baseline.
- Pixel center được đọc để trở thành hàng xóm bên trái ở bước kế tiếp; không dùng center trong phép Sobel hiện tại. Mỗi đầu hàng/tile khởi tạo lại cửa sổ. Chưa tái sử dụng giữa các tile hoặc giữa các hàng; đây là S1 có phạm vi rõ ràng, không phải lời khẳng định software tối ưu tuyệt đối.
- Hàm dùng volatile read/write cùng hợp đồng truy cập bộ nhớ như S0; không thêm delay hay làm yếu baseline. Không gọi MMIO của Sobel trong S1.
- TB M2 dùng cùng ENABLE_SOBEL=1, CPU/config/arbiter/native RAM model cho cả S0/S1/H1. Hai SW để DMA nghỉ; FIRMWARE_MODE chỉ điều khiển identity/checker, không thay đổi DUT.

## Vì sao M2 không lấy trực tiếp cycles SW của M1

M1 SW dùng ENABLE_SOBEL=0 với bus trực tiếp; H1 dùng ENABLE_SOBEL=1 qua arbiter. So sánh đó vẫn là bằng chứng lịch sử về hai cấu hình đã công khai. M2 dùng cùng cấu hình phần cứng để đo chi phí software/accelerator công bằng hơn. S0 binary giữ nguyên nhưng cycles có thể đổi do owner-selection/release bubbles. Không quy đổi hoặc sửa số liệu M1.

Ba tỷ số báo riêng: S0/S1 (lợi ích tối ưu software), S0/H1 (so với software cũ trên cùng hardware), S1/H1 (accelerator so với software mạnh hơn). Tỷ số<=1 được công khai; functional PASS không yêu cầu đạt speedup định trước.

## Compiler và bằng chứng compile

RV32I/ILP32 GCC13.2.0, -O2 cùng tùy chọn freestanding/no-relax của nền. Build S1 đồng thời rebuild S0/H1 trong thư mục mới, so từng byte binary với HEX nền trước khi publish S1. S0/H1 rebuild khớp, S1 binary1500byte. Manifest ghi hash source/header/HEX, compiler/options và build artifact hashes. Linker và stack limit không đổi. S1 không được tự gọi là functional PASS từ compilation.

Host algorithm test biên dịch riêng hàm Sobel S1 thành thư viện native và đối chiếu golden trên225ca:9kích thước gồm1x1/1xN/Nx1,5tile sizes và5mẫu ảnh. Kiểm tra chỉ ghi trong tile, input/canaries không đổi. Không chạy main firmware/RV32, không đo target cycles và không tạo RTL output evidence từ host test.

## Cổng nghiệm thu

1. Smoke RGB32 trên cả S0/S1/H1: bit-exact, event/profile hợp lệ, cùng hardware, không dùng DMA ở SW.
2. RGB17x19 wait3 và gray37x35 wait1: partial/unaligned/regression.
3.1x1 RGB,1x7 RGB,9x1 gray với tile1/2/16 theo hướng dẫn: cửa sổ suy biến trên CPU thật.
4. Audit từng RUN từ frozen sources, traces và binary bindings. Giữ raw cycles/profile, không ép số liệu theo ước lượng.

Sau cổng trên mới kết luận hiệu quả S1 và chốt DMA v2 theo dữ liệu. Memory map/RGB256 hiện tại giữ nguyên; RGB480 mở riêng sau. CPU/DMA wait counters có thể chồng lấn. Read bus bytes đếm word32bit, không phải dữ liệu ảnh duy nhất.

## Bảo toàn và giao diện

M1 ZIP/snapshot và stage1 không thay đổi. RUN M2 phải có prefix s2_m2_, lưu riêng thư mục s0/s1/h1. Output PGM/PPM và tile CSV từ CPU thật được giữ cho từng biến thể. Replay cũ chỉ hiểu cặp sw/hw của M1; không đưa RUN M2 vào replay cũ. Chưa có GUI replay ba biến thể.
