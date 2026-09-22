# M2 — biên bản chuẩn bị 2026-09-17

## Mã mới và phạm vi

S1 horizontal-window reuse được triển khai ở firmware/s1/main.c và sobel_s1.h. S0/H1 firmware và RTL RUN16 giữ nguyên. Testbench M2 tách identity firmware0/2/1 khỏi tham số hardware: mọi biến thể đều dùng ENABLE_SOBEL=1. Runner và audit riêng lưu ba thư mục s0/s1/h1, raw traces/profiles, ratios và frozen sources.

M2 không triển khai DMA v2, RGB480 hoặc thay physical config. Không chạy RTL/firmware/OpenLane trong phiên chuẩn bị.

## Kiểm tra đã thực hiện

- Cross-compile GCC13.2.0 RV32I/ILP32 -O2. S1 binary1500byte. Rebuild S0/H1 trong build mới với cùng compiler/options và đối chiếu từng byte: trùng HEX nền.
- Artifact build thật gồm ELF, disassembly, map, binaries và nguồn được lưu trong firmware/s1/generated/build_evidence.zip; manifest liên kết nguồn/HEX/artifact hashes. Không dùng host test làm bằng chứng target execution.
- Icarus12.0 compile-only M2 S0/S1/H1: đạt. Original core/MMIO/tile/arbiter/M1 variants cũng compile được.
-225 ca host kiểm tra đúng hàm C S1 với golden độc lập, tile-local writes và canaries: đạt. Chỉ native kernel function được gọi, không chạy main firmware hoặc CPU RV32.
-3 host contract tests M2: stale-source/HEX rejection; mode2 phải được coi là software; từ chối khác cấu hình hardware hoặc SW dùng MMIO: đạt.
-10 checker tests kế thừa M1: đạt. Python/shell syntax, source/input/baseline/S1 manifest: đạt.
- Warning cpuregs sensitivity upstream được giữ nguyên.

Evidence compile S1: build/s1_compile_onspGnoa. Evidence static cuối: build/m2_static_166pU67H và build/static_uiCGMt3W.

## Bảo toàn

Kiểm tra70hash nguồn/input/tài liệu stage1 đã nhập: không thay đổi. Ba ZIP M1 vẫn trùng hash ghi ở M1_ACCEPTANCE_REVIEW.md. Không sửa RUN hoặc archive cũ, không commit/push.

## Chờ người dùng

Chạy smoke s2_m2_rgb32_w1_01 theo M2_RUN_GUIDE.md, export cả khi FAIL. Kết quả S1 cycles/speedup và functional RV32 vẫn USER_RUN_REQUIRED. S0 cycles M2 không bắt buộc bằng M1 vì M2 SW nay cũng đi qua arbiter của cấu hình accelerator-present. Không áp đặt trước speedup dương.
