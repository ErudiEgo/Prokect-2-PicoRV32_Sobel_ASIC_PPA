> Cập nhật2026-09-14: RUN16 đã chạy, exit0 và Antenna/LVS/DRC/setup/hold/slew/cap PASS, còn1fanout. Xem [đánh giá kết quả](RUN16_REVIEW.md). Nội dung dưới là kế hoạch trước khi chạy; không chạy lại tag baseline_06.

# RUN16: clock branch buffering và sửa điện sau fanout

Ngày chuẩn bị: 2026-09-14. Tag: `picorv32_sobel_dma_clk50_baseline_06`.
**Chưa chạy vật lý. Người dùng chạy OpenLane.** RUN12 vẫn là mốc ổn định được backup;
RUN15 là bằng chứng thử nghiệm giảm fanout62→4 nhưng còn slew20/cap8, exit2.

## Thay đổi có căn cứ

1. CTS: `CTS_DISTANCE_BETWEEN_BUFFERS=80` µm và tùy chọn native
   `-branching_point_buffers_distance 1` µm qua `SOBEL_CTS_BRANCH_BUFFER_DISTANCE`.
   Mục đích đặt buffer ở các điểm rẽ, tránh nối trực tiếp tầng2 tới16buffer tầng6
   như ODB RUN15. Khoảng cách80µm là mục tiêu triển khai mới, không phải kết quả đã đo.
   Vẫn fanout optimization6, không bỏ dummy loads và không nới final limit10.
2. Sửa tín hiệu: extra SS RepairDesignSlowCorner thực hiện2lượt native repair_design.
   Lượt1 giữ fanout5 và slew/cap margins55% như RUN15. Lượt2 xét lại mạch sau buffer
   mới với margins70%, để tăng dư địa cho diode và điện dung routing. Sau hai lượt,
   fanout được trả về10; nếu một lượt lỗi cũng trả về10 rồi giữ nguyên lỗi để flow dừng.
   Legalization/GRT của script OpenLane gốc vẫn thực hiện sau đó, tiếp theo là timing
   repair đa corner và antenna như cũ. Không sửa sau signoff rồi giữ kết quả cũ.

Nguồn thuật toán đã đối chiếu đúng OpenROAD edf00dff:
[HTreeBuilder.cpp](https://github.com/The-OpenROAD-Project/OpenROAD/blob/edf00dff99f6c40d67a30c0e22a8191c5d2ed9d6/src/cts/src/HTreeBuilder.cpp),
[RepairDesign.cc](https://github.com/The-OpenROAD-Project/OpenROAD/blob/edf00dff99f6c40d67a30c0e22a8191c5d2ed9d6/src/rsz/src/RepairDesign.cc).
[Tài liệu CTS](https://openroad.readthedocs.io/en/latest/main/src/cts/README.html) mô tả
branching-point buffering yêu cầu distance_between_buffers. Cú pháp còn được kiểm tra
trực tiếp bằng Tcl parser của binary đã pin, thay hàm C++ chạy CTS bằng stub.

Hai thay đổi này có thể đổi skew, hold, routing, area và power. Không hứa PASS từ
precheck. Mục tiêu là xử lý lỗi đã xác định, đánh giá lại mọi checker trên RUN mới.
Giữ RTL/firmware/SDC/pinorder, clock50ns, SKY130 HD, ngưỡng slew1,5ns/cap0,2pF cùng
các giới hạn Liberty, checker và native antenna repair. Không xóa diode để giảm tải.

## Kiểm tra đã thực hiện

`build/asic_precheck_CvJfVKaZ` tại Ubuntu:
- Bốn bằng chứng simulation32/64/128/256 khớp hash/golden; không simulation lại.
- Config Classic81steps, lint, SDC load và API PASS.
- Hai lỗi wrapper cũ về env/master tiếp tục có regression.
- Tcl parser CTS cài đặt chấp nhận tham số spacing/branch; C++ CTS engine là stub.
- Mock kiểm tra đối số hai lượt sửa55/70 và phục hồi fanout10 khi lỗi ở lượt1 hoặc2.
- Không có Step.start, synthesis, CTS engine, resizer engine, placement/routing hoặc
  checker vật lý nào được trợ lý chạy. 81 bước chính giữ nguyên; extra SS có2lượt nội bộ.

## Lệnh Ubuntu

```bash
bash "/mnt/e/aa. PPA_Project_List/aaa.PicoRV32_Sobel_ASIC_PPA/scripts/00_copy_to_ubuntu.sh"
```
```bash
cd "$HOME/openlane_projects/picorv32_sobel_asic_ppa"
```
```bash
bash scripts/08_run_report_baseline.sh
```

Đây là RUN hoàn toàn mới từ đầu, không parent/checkpoint, không ghi đè RUN12–15.
Kết thúc dù thành công hay lỗi:

```bash
bash scripts/07_collect_asic.sh picorv32_sobel_dma_clk50_baseline_06
```

Đọc exit0 và Antenna/LVS/DRC PASS, setup/hold/slew/cap/fanout0 ở các corner kiểm tra.
Chỉ sau khi đọc report thật mới chốt baseline và tổng hợp PPA. Nếu cófinalODB:

```bash
bash scripts/09_open_final_openroad.sh picorv32_sobel_dma_clk50_baseline_06
```

## WARNING phải đánh giá, không che log

| Nhóm cảnh báo RUN15 | Ý nghĩa và cách xử lý ở phạm vi hiện tại |
|---|---|
| GRT-0097 ở STA trước routing | Chưa có global routing tại stage đó; phân biệt với lỗi sau extraction. |
| DRT-0349 LEF58_ENCLOSURE/CUTCLASS | Giới hạn parser của bộ tool/PDK đã pin; không sửa PDK hoặc bỏ DRC chỉ để hết chữ WARNING. |
| Checker.WireLength chưa đặt threshold | Kiểm tra này chưa có ngưỡng yêu cầu nên bị skip. Chưa tự đặt ngưỡng theo kết quả để tạo PASS; phải ghi rõ trong báo cáo. |
| VSRC_LOC_FILES=None | IR drop thiếu mô hình nguồn thực tế; vẫn ghi indicative/vectorless, không giả tạo vị trí pad để hết warning. |
| Hai output thiếu antenna diffusion info | Cần đối chiếu với các output địa chỉ hằng; không suy ra LVS fail hay full signoff từ thông báo này. |

RUN16 tập trung làm sạch lỗi vật lý và điện. Không cam kết số WARNING giảm nếu các
điều kiện mô hình/công cụ trên vẫn giữ nguyên. WARN không được ẩn hoặc giảm mức log.
