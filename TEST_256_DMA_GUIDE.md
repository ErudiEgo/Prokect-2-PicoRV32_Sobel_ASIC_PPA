# Test thử 256×256 với Tile DMA v1

Theo yêu cầu người dùng, thử một ảnh256 trước khi chuẩn bị bộ ảnh32/64/128/256 chính thức.
Chỉ chuẩn bị INPUT; chưa chạy simulation hoặc OpenLane. RTL/firmware giữ nguyên.

Input: images/5.1.13.tiff, grayscale L 256×256. Đã kiểm tra65536 byte đầu vào giống
TIFF giải mã, không resize/crop. Metadata và hash trong inputs/sipi_chart256_dma_01/image.json.
TIFF SHA256: 92ef9dd86f3c0edbbcdad50d63229d6633df560308b60b96cb045e570be02e18
HEX SHA256: 5209a8b3e63ad46bbd88259df1144699a579a6f5e5158e984835f3b95fa78322
Ảnh và input này vẫn nằm ngoài Git theo allowlist hiện hành; giữ riêng để tái lập.

RUN mới: soc_sipi_chart256_dma_01. tile16, memory_wait1, 65536pixels/256tiles mỗi phương án.
Dữ liệu input dùng0x10000..0x1ffff, output0x50000..0x5ffff, nằm trong vùng hiện có.
Wall timeout3600s mỗi subprocess; watchdog100 triệu cycles giữ nguyên.
Ngoại suy16 lần từ RUN64 SW1822739/HW281750cycles, host44.415/7.782s:
khoảng29.2/4.5 triệu cycles và12/2 phút host. Đây chỉ là dự trù, không phải kết quả256.
Nếu timeout/watchdog thì thu bằng chứng để chẩn đoán, không coi là PASS.

Ubuntu, từng lệnh:

```bash
bash "/mnt/e/aa. PPA_Project_List/aaa.PicoRV32_Sobel_ASIC_PPA/scripts/00_copy_to_ubuntu.sh"
```
```bash
cd "$HOME/openlane_projects/picorv32_sobel_asic_ppa"
```
```bash
bash scripts/03_run_soc_tests.sh soc_sipi_chart256_dma_01 --image inputs/sipi_chart256_dma_01 --tile 16 --memory-wait 1 --timeout-seconds 3600
```
```bash
bash scripts/04_export_sim.sh soc_sipi_chart256_dma_01
```

Cần4 unit TEST PASS, PIXEL CHECK PASS65536pixels/256tiles mỗi SW/HW, FUNCTIONAL TEST PASS.
Kể cả lỗi vẫn export nếu script đã tạo ZIP. Không ghi đè tên RUN.
Sau PASS có thể mở replay:
```bash
python3 scripts/replay.py reports/soc_sipi_chart256_dma_01
```

Đây là kiểm thử tăng kích thước, vẫn so với SW baseline hiện tại. Không thay thế công việc
đối chứng SW tối ưu hoặc PPA/physical checks cho RTL DMA mới.
