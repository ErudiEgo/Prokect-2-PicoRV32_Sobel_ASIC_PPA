# DMA v2 — dự thảo trước cổng M1

Trạng thái: DESIGN_DRAFT, chưa RTL/compile/simulation/PPA. Dựa trên RTL v1 và profile thực RGB32; cần xem thêm RGB17x19/gray37x35 trước khi chốt. Không thay nguồn đang dùng cho ba RUN M1.

## Câu hỏi và thay đổi có kiểm soát

DMA v1 đã đo23436lần đọc cho3072mẫu kênh RGB32. Mỗi giao dịch trả word32bit nhưng chỉ dùng một byte hàng xóm. Thí nghiệm tiếp theo phải phân biệt tái sử dụng pixel và tận dụng nhiều byte trong word. CPU/arbiter/memory_wait được giữ làm điều kiện đối chứng ban đầu.

S1 là software tối ưu công bằng: row pointers và tái sử dụng cửa sổ theo chiều ngang, cùng zero-padding, saturation, tile/channel order và output requirements. Phải lưu S0 riêng; không so HW mới chỉ với S0. Compiler/options và sự thay đổi instruction/data traffic được ghi rõ. Chưa kết luận speedup so với S1.

## Ứng viên chính: streaming cửa sổ trong từng tile

Giữ lịch xử lý tile và thứ tự R/G/B để dùng chung yêu cầu hoàn thành vùng. Một tile output Wt x Ht cần quét vùng input (Wt+2) x (Ht+2), bao gồm halo. Chỉ tọa độ nằm ngoài toàn ảnh mới lấy0. Halo qua tile phải đọc pixel thật.

Ứng viên lưu hai dòng trước với stride Wt+2 và cửa sổ3x3. Tile tối đa64 cần132byte cho hai dòng, cộng9byte cửa sổ và FIFO/trạng thái nếu có. Đây là dung lượng dự kiến cho phương án hai dòng vòng; đọc/ghi đồng thời và lịch cập nhật phải được đặc tả/kiểm chứng. Không phải SRAM macro đã tồn tại hoặc area đo được.

Một input sample được nhận sẽ cập nhật line/window state đúng một lần. Chỉ phát output khi cửa sổ đủ3hàng/3cột; pause toàn bộ trạng thái cửa sổ khi kết quả chưa được core/đầu ghi tiếp nhận. Cho phép serialize core/store ở phiên bản đầu; không mặc định1pixel/cycle.

Với tile nội ảnh, số sample input lý tưởng cần đọc là (Wt+2)(Ht+2), thay vì8WtHt. Ở biên ảnh, mẫu zero không cần giao dịch. Đây là mô hình dự kiến để kiểm tra counter, không phải kết quả v2. Thiết kế phải đếm word transactions thực nếu bổ sung packing.

## Hợp đồng giao tiếp phải hoàn tất trước RTL

- Descriptor gồm dimensions/origin/extent/source/destination; nguồn hiện tại trỏ pixel góc tile, không phải góc toàn ảnh. Halo address tính từ tọa độ toàn ảnh, tránh unsigned underflow.
- Validate toàn bộ phạm vi input/output, kích thước, phép cộng/nhân địa chỉ và vùng chồng lấn trước start. Không chỉ kiểm tra base.
- Version hóa ID/capability nếu ABI thay đổi; firmware phải kiểm tra đúng thiết bị. Không tái sử dụng ID để che khác biệt không tương thích.
- Start khi busy/descriptor sai giữ error có thể kiểm tra; done sau handshake ghi output cuối, không phải sau phép tính cuối.
- Request giữ addr/data/strobe ổn định khi chờ ready. Reset hủy job và invalidates trạng thái cửa sổ, không cần xóa toàn bộ mảng nếu valid tracking đúng.
- Input/output không overlap. CPU không sửa buffer input hoặc descriptor đang được engine sử dụng.
- Giữ memory map v1 ở thí nghiệm đầu. RGB480 là thay đổi riêng sau khi engine đúng, không gộp vào cùng lần sửa.

## Các biến thể để tìm nguyên nhân cải thiện

H1: DMA v1 hiện có. H2a: tái sử dụng line/window nhưng vẫn fetch byte qua word interface. H2b tùy bằng chứng: giữ word đọc và sử dụng các byte còn lại; tính alignment, đầu/cuối hàng và ranh giới plane RGB lẻ. Không đổi arbiter cùng lúc, trừ khi có bằng chứng deadlock/starvation; mọi đổi arbitration là thí nghiệm riêng.

Đánh giá cycles, reads/writes, bus bytes, waits và first-region latency với S0/S1/H1/H2. Line buffers phải được tính vào physical top; nếu tổng hợp thành flop, báo đúng area và công suất theo cách đó. Không gọi tiết kiệm năng lượng từ riêng cycles/traffic.

## Kiểm chứng cần chuẩn bị

- Golden bit-exact; không thay đổi arithmetic/border để tăng tốc.
- 1x1,1xN,Nx1; tile1/16/32/64; kích thước lẻ/partial và halo qua tile.
- RGB plane không word-aligned, cực trị/saturation, impulse, reset giữa fill/compute/store.
- Stalls ở fetch và output; không cập nhật buffer hai lần khi valid kéo dài; không mất output.
- So expected transactions từ tập tọa độ input với handshake đo thật.
- Compile/lint trước; người dùng chạy unit/SoC simulation; chỉ sau functional evidence mới chọn cấu hình đưa sang OpenLane.

Bản này không phải cam kết tối ưu cuối. Nếu profile sau M1 hoặc S1 cho thấy chi phí CPU/arbiter chi phối, điều chỉnh giả thuyết và kế hoạch thí nghiệm có giải thích, giữ kết quả âm.
