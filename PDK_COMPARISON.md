# SKY130 và GF180MCU cho PicoRV32–Sobel

Ngày đối chiếu: 2026-09-11. Đây là phân tích lựa chọn nền tảng, không phải kết quả PPA của dự án.

## Điều không đổi

PicoRV32, thuật toán Sobel, kết quả pixel và giao thức cấp dữ liệu có thể dùng cùng RTL độc lập PDK. Vivado behavioral simulation cũng không phụ thuộc PDK ASIC. Đổi PDK không biến hệ thống thành bộ dựng ảnh 3D, không tự làm ảnh đẹp hơn và không tự làm giảm số chu kỳ của cùng vi kiến trúc.

## Điều thay đổi

| Nội dung | SKY130 | GF180MCU |
|---|---|---|
| Công nghệ | SkyWater 130 nm | GlobalFoundries 180 nm |
| Cell | Ví dụ sky130_fd_sc_hd, high density, VDD danh định 1,8 V | Có thư viện 7-track và 9-track; tài liệu liệt kê các nhóm corner 1,8/3,3/5,0 V, nhưng phải chọn library/corner mà bản PDK/flow thực tế cung cấp |
| Diện tích | Phụ thuộc cell mapping, buffer, clock tree và bộ nhớ | Cell geometry/mapping khác; chưa thể cho tỷ lệ diện tích so với SKY130 khi chưa chạy |
| Timing | Delay cell và RC routing theo SKY130 | Delay cell và RC routing khác; cần kiểm tra lại clock target và mọi corner |
| Power | Theo điện áp, tải, hoạt động và library đã chọn | Cùng nguyên tắc; không suy ra mức tiêu thụ chỉ từ nhãn 180 nm |
| Layout | Theo grid/layer, PDN, antenna và DRC của SKY130 | Cần cấu hình grid/layer, PDN và checker tương ứng; không dùng nguyên GDS hoặc tham số layout của SKY130 |
| Bộ nhớ | Macro nếu dùng phải đúng công nghệ và đầy đủ views | Không tái sử dụng macro SKY130. Nếu dùng register-based memory thì cùng RTL nhưng diện tích và power thay đổi |
| Tình trạng máy vừa kiểm tra | Có đường dẫn ~/.volare/sky130A trong Ubuntu-24.04 | Chưa thấy đường dẫn ~/.volare/gf180mcuD ở vị trí đã kiểm tra; chưa kết luận không có ở nơi khác |

OpenLane hỗ trợ cả hai họ PDK. Tuy nhiên hỗ trợ ở cấp tài liệu không có nghĩa cấu hình dự án này đã tương thích hoặc đạt sign-off. Hiện Docker chưa khả dụng trong distro WSL được kiểm tra, nên chưa nạp cấu hình OpenLane trong môi trường đó.

## Cách so sánh nếu thực hiện cả hai

- Cùng revision RTL, cấu hình CPU, cách triển khai bộ nhớ, firmware, ảnh và quy tắc biên.
- Cùng định nghĩa physical top và phạm vi công suất; không so một bên toàn SoC với bên kia chỉ Sobel.
- Trước tiên chọn một tần số chung mà cả hai đạt timing; ghi corner, điện áp, nhiệt độ, tải I/O và điều kiện switching của từng bên.
- Cùng phương pháp thu thập hoạt động và cùng workload. Vectorless chỉ so với vectorless có giả định được ghi rõ; không trình bày như năng lượng đo thực tế.
- Báo riêng cell area, core/die area, slack/WNS/TNS, công suất, chu kỳ/ảnh và checker đã chạy. So sánh Fmax là thí nghiệm riêng, không suy ra bằng phép tỷ lệ 130/180.
- Nếu chạy ở tần số khác nhau, tính thời gian theo cycles/frequency của mỗi bên, không chỉ so số chu kỳ.
- Không bắt buộc diện tích die hoặc tham số PDN giống nhau; mọi khác biệt và tiêu chí lựa chọn phải được ghi nhận để giải thích kết quả.

## Quyết định sau khi so sánh

Ngày 2026-09-11, người dùng xác nhận chọn **SKY130** vì các bài thực hành trước đều sử dụng công nghệ này. Dự án triển khai với **sky130A / sky130_fd_sc_hd / OpenLane Classic**. GF180MCU chỉ còn là nội dung so sánh tham khảo, không phải một phiên bản phải triển khai trong phạm vi hiện tại. RTL vẫn được giữ độc lập PDK khi phù hợp.

## Nguồn chính thức

- Thư viện SKY130, điện áp và kích thước cell: https://skywater-pdk.readthedocs.io/en/main/contents/libraries/foundry-provided.html
- Thư viện số GF180MCU: https://gf180mcu-pdk.readthedocs.io/en/latest/digital/Digital.html
- Corner GF180MCU 9-track: https://gf180mcu-pdk.readthedocs.io/en/latest/digital/standard_cells/gf180mcu_fd_sc_mcu9t5v0/spec/corners.html
- Thông số hình học GF180MCU 7-track: https://gf180mcu-pdk.readthedocs.io/en/latest/digital/standard_cells/gf180mcu_fd_sc_mcu7t5v0/spec/physical.html
- Cấu hình PDK trong OpenLane: https://openlane2.readthedocs.io/en/stable/usage/about_pdks.html
