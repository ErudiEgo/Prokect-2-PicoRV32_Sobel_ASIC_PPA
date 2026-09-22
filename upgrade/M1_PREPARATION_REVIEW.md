# Stage2 M1 — biên bản chuẩn bị 2026-09-17

## Phạm vi đã thực hiện

- Tạo project độc lập trong upgrade. Không chỉnh nguồn/RUN/report stage1 ở thư mục cha.
- Lưu70 tệp nguồn/input/tài liệu được nhập vào baseline/stage1_import.zip,161151byte. SHA256: `37ce558145ee3ba68b7ca243cff591e7e1d279b9e0e5daf8f33cadea3944830c`.
- import_manifest.json lưu hash từng tệp, Git HEAD/status tại thời điểm nhập và giới hạn RUN16. Đây là working-tree import gồm firmware RGB; không phải toàn bộ clean checkout RUN16. Config/SDC trong archive cũng là bản working tree tại lúc nhập, không được mặc định coi là frozen config RUN16.
- Đối chiếu lại70hash tại nguồn stage1 sau triển khai: không thay đổi. Không sao chép hay chạy lại các archive kết quả nặng.
- Giữ nguyên toàn bộ RTL/firmware/vendor bytes trong M1; thêm observer schema2 trong TB và checker phân tích profile.
- Runner yêu cầu s2_ RUN mới, precheck trước simulation, freeze nguồn/checker/baseline và xuất ZIP về upgrade/reports. Có công cụ audit ba RUN để nghiệm thu M1.
- Thêm .gitignore/.gitattributes cục bộ để nguồn stage2 không bị allowlist ở thư mục cha che mất và giữ hash qua checkout; chưa commit/push.

## Kiểm tra đã thực hiện

Ubuntu-24.04, Icarus Verilog12.0. Chạy `scripts/01_precheck.sh` bằng đường dẫn upgrade trên ổ E, không copy/chạy trong workspace Ubuntu stage1.

Evidence cuối: `build/static_cnuuj1Gs/`.

- Compile-only core, MMIO, tile DMA, arbiter và hai cấu hình CPU: đạt.
-5 kiểm tra host của checker RGB: đạt.
-5 kiểm tra host của hợp đồng profile: đạt, bao gồm số hàng xóm ở ảnh suy biến, SW không dùng DMA và từ chối counter hỏng.
- Cú pháp shell/Python, hash firmware/input, RTL RUN16 identity và baseline archive: đạt.
- Hai warning sensitivity mảng cpuregs upstream trên mỗi cấu hình SoC được giữ nguyên.

Các test host dùng dữ liệu tổng hợp để kiểm tra checker, lưu tạm và không được coi là ảnh/cycle từ RTL. Các file .vvp ở build chỉ là sản phẩm compile, chưa được thực thi.

## Chưa thực hiện

Không chạy vvp/firmware/RTL simulation hoặc OpenLane/PNR. Không có functional PASS stage2, benchmark mới, DMA v2, software S1 hay RGB480. Power/energy/ASIC stage2 NOT_RUN. M1 chưa nghiệm thu.

## Điểm bàn giao

Người dùng chạy theo STAGE2_RUN_GUIDE.md: RGB32 wait1 -> RGB17x19 wait3 -> gray37x35 wait1 -> audit_m1.py. Export ZIP kể cả khi thất bại. Nếu RUN đầu khác cycles lịch sử, chẩn đoán trước khi chuyển tiếp. Sau khi đọc profile thật mới chốt triển khai S1/DMA v2 và các RUN mở rộng.
