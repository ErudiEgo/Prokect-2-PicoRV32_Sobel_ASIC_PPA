# Nghiệm thu M1 — 2026-09-17

**STAGE2_M1_ACCEPTANCE_PASS**, xác nhận bằng audit ba ZIP do người dùng chạy và export. Trợ lý không chạy lại simulation/firmware hoặc OpenLane.

| RUN | SW cycles | HW cycles | SW/HW | Mẫu kênh / vùng mỗi phương án |
|---|---:|---:|---:|---:|
| s2_m1_rgb32_w1_01 | 1352946 | 206960 | 6.537234x | 3072 / 4 |
| s2_m1_rgb17x19_w3_01 | 604553 | 101421 | 5.960827x | 969 / 4 |
| s2_m1_gray37x35_w1_01 | 580371 | 90106 | 6.440981x | 1295 / 9 |

Audit kiểm tra inventory/hash frozen source, RTL RUN16 và firmware nền, bằng chứng hoàn thành unit tests, pixel so với golden độc lập, timestamp vùng, profile, metric tính lại, cùng bộ nguồn giữa ba RUN và đúng fixture. RGB32 giữ nguyên chu kỳ lịch sử. Audit tạo ảnh kiểm chứng ở thư mục tạm, không sửa ảnh/evidence gốc.

RGB17x19 kiểm tra tile cuối không đầy, plane RGB lệch word alignment và memory_wait3. Gray37x35 kiểm tra hồi quy một kênh với9tile. PASS chỉ bao phủ các trường hợp và kiểm tra đã thực hiện; không chứng minh mọi input hoặc mọi điều kiện bus.

Hash ZIP:

- RGB32: `087da8cb2c934fa091b6dd74606b99e49d02b4fb03107495945577fe2468c843`
- RGB17x19: `1639bc958b69d1e7d4926df04f0548a848f56f0489ed576e123cf8f574445c92`
- Gray37x35: `cfbe8f3345afd8dd4b9063c30d3f88965195f2481b5a31fe528ee5177cdca7a1`

Chi tiết audit lưu tại `build/m1_exported_zip_audit_01.json`. Không cần chạy lại ba RUN này. Các dòng USER_RUN_REQUIRED trong snapshot/log là metadata trạng thái chuẩn bị khi nguồn được đóng băng, không phủ định kết quả audit sau chạy.

## Ý nghĩa đối với bước tiếp theo

Baseline S0/H1 và bộ đo đã vượt cổng M1. Có thể chuyển sang triển khai software S1 và DMA v2 theo bản thiết kế, giữ snapshot M1 làm đối chứng. Tỷ số trên là tốc độ phần cứng v1 so với software S0 cùng điều kiện trong từng RUN, chưa phải thành tích DMA v2. Không so sánh tỷ số giữa ảnh khác nhau để kết luận riêng tác động memory_wait.

ASIC stage2 NOT_RUN; software S1/DMA v2/RGB480 chưa triển khai tại thời điểm nghiệm thu này. RUN16 vật lý lịch sử vẫn có fanout1 và power vectorless, external RAM không thuộc physical top. M1 PASS không phải full ASIC sign-off.
