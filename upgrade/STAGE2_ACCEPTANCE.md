# Stage 2 — các mốc nghiệm thu

Ngày 2026-09-17. Các mục bên dưới là tiêu chí, không phải kết quả đã đạt.

| Mốc | Sản phẩm | Cổng nghiệm thu | Trạng thái ban đầu |
|---|---|---|---|
| M0 | Workspace độc lập và baseline archive/hash | Hash nguồn stage1 không đổi; không copy/rerun evidence cũ | Đã tạo, kiểm tra tĩnh trước bàn giao |
| M1 | Regression + profiling baseline | Ba RUN nhỏ đúng pixel/tile; profile nhất quán; RGB32 giữ cycles lịch sử | ACCEPTED — M1_ACCEPTANCE_REVIEW.md |
| M2 | Software S1 công bằng + thiết kế DMA v2 | S1 đúng thuật toán; profile xác định bottleneck; ABI/buffer budget được ghi | ACCEPTED — M2_M3_UNIT_ACCEPTANCE.md |
| M3 | DMA v2 và kiểm chứng | Bit-exact, biên/partial/reset/stall đúng; đối chiếu S1/H1/H2 | ACCEPTED — M2_M3_UNIT_ACCEPTANCE.md, H2_FREEZE_REVIEW.md |
| M4 | Workload480 và ảnh thật | Memory/dataflow hỗ trợ thật; golden/latency/traffic kiểm chứng | Gray480×320 characterization ACCEPTED; ảnh tự nhiên/RGB480 chưa đạt |
| M5 | Physical/PPA chọn lọc | Actual reports gắn đúng snapshot, scope và corner; công khai vi phạm | H1 và H2 ECO đã audit, đạt kiểm tra flow với giới hạn công khai — H1_H2_PPA_ACCEPTANCE.md |
| M6 | Artifact và bản thảo | Claims liên kết bằng chứng; novelty/related work được đánh giá | NOT_STARTED |

## M1: ba RUN do người dùng thực thi

| RUN mới | Input | Tile / wait | Samples / vùng | HW writes / starts |
|---|---|---|---|---|
| s2_m1_rgb32_w1_01 | RGB32 nền | 16 / 1 | 3072 / 4 | 3072 / 12 |
| s2_m1_rgb17x19_w3_01 | RGB17x19, plane lệch byte lane | 16 / 3 | 969 / 4 | 969 / 12 |
| s2_m1_gray37x35_w1_01 | Gray37x35 nền | 16 / 1 | 1295 / 9 | 1295 / 9 |

Mỗi RUN cần unit tests core/MMIO/tile/arbiter, CPU SW/HW thật, golden từng pixel và sự kiện vùng. Counter schema2 phải hợp lệ; DMA đọc đúng số hàng xóm trong ảnh: channels*[4(W-1)(H-1)+2H(W-1)+2W(H-1)]. Đây là giá trị kỳ vọng từ kiến trúc v1, không được dùng để thay thế counter đo.

RGB32 phải giữ cycles lịch sử SW1352946/HW206960 vì firmware/RTL/input/tile/wait giữ nguyên. Khác biệt là lý do điều tra observer/môi trường, không sửa expected để tạo PASS. Không áp con số này cho ảnh khác.

Audit `scripts/audit_m1.py` chỉ đọc bằng chứng đã tồn tại, kiểm tra hash, tái đối chiếu pixel bằng bản sao tạm, tính lại metrics và kiểm tra snapshot/input của cả ba RUN. Chỉ in `STAGE2_M1_ACCEPTANCE_PASS` khi thực sự đủ dữ liệu. Sau audit vẫn chưa có PPA hay tăng tốc DMA v2.

## Quy tắc phép đo

- Cửa sổ từ sau start-marker đến hết end-marker; gồm channel loops, instruction fetch, điều khiển, DMA, output và tile events. Boot và host decode/replay nằm ngoài.
- CPU partition và external bus partition mỗi nhóm bằng total cycles. CPU/DMA wait/busy là các nhóm chồng lấn, không cộng chung.
- DMA arbitration wait gồm tranh chấp và bubble chọn/chuyển owner. Service wait gồm latency bộ nhớ và handshake khi đã được cấp bus.
- External reads đếm đủ32bit mỗi response; RAM writes đếm strobe. Host marker writes báo riêng. Không suy useful-byte count của CPU từ word response.
- Instrumentation chỉ ở TB, không nằm trong physical top.
- `simulation_wall_seconds` là thời gian host; không thay thế target cycles, không tự quy ra FPS ASIC.

## Cổng sau M1

Đọc actual profile trước khi chốt DMA v2; giữ S0 và H1 làm đối chứng. Ưu tiên software S1 tái sử dụng dữ liệu hợp lý và DMA v2 line/window buffer, tách packing thành ablation nếu triển khai. Nếu M1 FAIL thì sửa đúng bằng chứng rồi dùng RUN tên mới; không chuyển sang OpenLane để tìm lỗi chức năng.
