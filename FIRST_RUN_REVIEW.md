# Đánh giá soc_image_smoke_01

Người dùng chạy Icarus simulation và export ZIP; trợ lý kiểm tra lại dữ liệu hiện có, không chạy lại CPU hoặc OpenLane. Không sửa RTL/firmware hoặc archive trong lần đánh giá này.

Nguồn: `reports/soc_image_smoke_01.zip`.

SHA256 archive: `73c07a6b6e5fefeb5750527b6184ecd2abbe000c9962c25b4df833c3f24d5e3f`.

| Hạng mục | Kết quả |
|---|---|
| Input | 37 × 35, 1.295 pixel, tile 32, 4 tile, memory_wait=1 |
| Core unit test | Log PASS 1.283 vector và kiểm tra giao thức/reset |
| MMIO unit test | Log PASS thanh ghi, bắt tay, số học, lỗi và reset |
| CPU software | 573.713 chu kỳ; mọi pixel/tile hợp lệ |
| CPU + Sobel MMIO | 774.758 chu kỳ; mọi pixel/tile hợp lệ |
| HW − SW | +201.045 chu kỳ, tăng 35,0428% |
| SW/HW | 0,740506; chưa có tăng tốc về chu kỳ |
| Thời gian chạy vvp trên host | SW 14,755 s; HW 19,508 s, không phải thời gian ASIC |
| ASIC timing/area/power, DRC/LVS/antenna | NOT_RUN |

Audit xác nhận 35 hash đầu vào đóng băng, hash các file đầu ra đã kiểm chứng, 16 file RTL/TB/firmware/vendor hiện hành khớp snapshot, mọi exit code đã ghi bằng 0. Đối chiếu lại từng pixel với phép tích chập 3 × 3 từ input, kiểm tra mọi timestamp, thứ tự/vị trí/kích thước tile và PGM khớp dữ liệu. Không lấy chữ PASS trên terminal làm bằng chứng duy nhất.

`01_precheck.sh` là compilation/kiểm tra hash. `03_run_soc_tests.sh` thực thi mô phỏng: unit tests rồi PicoRV32 chạy hai firmware. Vì vậy RUN đã vượt qua precheck và thực sự tạo ảnh trong RTL simulation; chưa chuyển RTL sang layout ASIC.

Warning `@* is sensitive to all 32 words in array 'cpuregs'` mô tả sensitivity của logic đọc register file ở mã CPU. Trong RUN này warning không làm compile thất bại hoặc gây sai pixel; không sửa/tắt warning chỉ để terminal sạch. Lint của OpenLane sẽ được đánh giá riêng.

Vấn đề hiện tại là hiệu năng. Theo mã firmware, mỗi pixel ở bản HW vẫn cần CPU đọc hàng xóm, đóng gói, ghi hai thanh ghi pixel, ghi start, polling và đọc result; các bước này thay phần tính số học tương đối ngắn. Đây là giả thuyết nguyên nhân phù hợp với kiến trúc và kết quả. RUN chưa có bộ đếm phân loại instruction/MMIO/stall nên chưa lượng hóa được chi phí của từng phần.

Bước cải thiện nên bắt đầu bằng đo các chi phí đó và giảm số lần CPU điều khiển trên mỗi pixel; hướng tiếp theo có thể là cấp pixel liên tục hoặc xử lý nhiều pixel trong một lệnh. Mọi thay đổi phải giữ quy tắc Sobel/border và điều kiện bộ nhớ so sánh, ghi RUN mới. Không thay số liệu hoặc đổi nhãn baseline thành thành công tăng tốc.

Chưa cần người dùng chạy lại cùng bài test để phân tích số liệu hoặc mở replay. Một ảnh nhỏ đạt kiểm tra chức năng không chứng minh mọi ảnh, kích thước, độ trễ bộ nhớ hoặc sign-off ASIC đều đạt.
