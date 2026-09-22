# DMA v2 — ứng viên độc lập, chưa tích hợp SoC

Nguồn: `candidate/sobel_tile_v2.v`; testbench: `candidate/tb_sobel_tile_v2.sv`. RTL nền trong `rtl/` và firmware S0/S1/H1 không đổi. ABI ID TIL2 = 0x54494c32 để không bị nhận nhầm là TIL1.

Ứng viên quét vùng tile cộng halo một pixel mỗi phía, dùng hai bộ đệm dòng 66 byte và các thanh ghi cửa sổ 3×3. Tổng dung lượng hai dòng là 132 byte, chưa bao gồm taps và điều khiển. Mỗi mẫu trong vùng quét nằm trong frame được đọc một lần; padding ngoài frame bằng 0, halo giữa các tile vẫn đọc lại. Hiện mỗi mẫu byte vẫn dùng một giao dịch bus32; chưa đóng gói/tận dụng bốn byte của một lần đọc. Core Sobel đa chu kỳ được giữ nguyên; không tuyên bố một pixel mỗi chu kỳ.

Địa chỉ source/destination vẫn trỏ pixel trên-trái của tile trong một mặt phẳng ảnh. Dimensions/origin/extent giữ như v1. Trước start, kiểm tra cả phạm vi mặt phẳng suy từ origin và stride; địa chỉ không được tràn vùng input 0x10000–0x50000 hoặc output 0x50000–0x90000. Tối đa frame512×512 và tile64×64, chưa thay memory map để hỗ trợ RGB480. Bộ đệm không reset toàn mảng; hai hàng khởi động chặn dữ liệu cũ. Các mô hình RAM trong testbench là testbench-only.

Test được chuẩn bị: 181 ca có đối chiếu từng pixel, số giao dịch đọc bằng diện tích halo được cắt theo frame, số ghi bằng diện tích tile, không ghi trùng/ngoài tile. Gồm sáu mẫu ảnh (cả gradient nhỏ tránh che lỗi do saturation), bốn byte lane, ảnh hẹp, tile thiếu, tile64 và halo nội bộ; RAM chờ thay đổi, descriptor viết lúc busy, descriptor ngoài vùng/tràn, partial MMIO, reset khi đọc/ghi và chạy lại sau reset.

Trạng thái tại lúc chuẩn bị: **chưa chạy RTL**. Compile thành công không chứng minh 181 ca đã đạt. Runner đóng băng candidate, core, scripts, tài liệu; ghi phiên bản tool, log, mã thoát, thời gian mô phỏng thực và hash. `DMA_V2_UNIT_FUNCTIONAL_PASS` chỉ có nghĩa unit đã đạt sau khi chạy thật; không phải RV32 SoC PASS, tốc độ đo hoặc ASIC PASS.

Người dùng chạy riêng sau batch M2:

```bash
bash scripts/21_run_dma_v2_unit.sh s2_m3_unit_01
```

Xuất cả khi thất bại:

```bash
bash scripts/04_export_sim.sh s2_m3_unit_01
```

Rủi ro cần kiểm chứng tiếp: multipliers trong kiểm tra descriptor có thể tốn diện tích; mảng bộ đệm chưa gắn SRAM macro nên có thể thành flop/mux; overhead FSM và warm-up có thể làm tile nhỏ chậm; giảm đọc không tự bảo đảm speedup khi chung bus với CPU. Chỉ sau unit PASS mới tích hợp ứng viên vào SoC riêng, firmware H2, đo S1/H1/H2 cùng cấu hình bộ nhớ và CPU. Không chạy OpenLane trước functional gate.
