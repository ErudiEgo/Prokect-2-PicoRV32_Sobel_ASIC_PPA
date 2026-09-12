# Lỗi tích hợp repair_04–05; tiếp tục bằng repair_06

Ngày 2026-09-12. Nguồn: archive `reports/picorv32_sobel_clk50_repair_04_collect_20260912T045049515654Z.tar.gz` và traceback người dùng gửi. SHA256 archive: `3b9a6e9f09c1cd04284130889f17a609a6cb975e6baabb27bd443e249d1d53f4`. Bản trích đọc ở `build/repair04_review_fbiqab_6`; giữ nguyên RUN/archive gốc.

## Lỗi xác định

Detailed routing ở `47-openroad-detailedrouting` hoàn tất. Bước mới `48-sobel-antennaclosure` đã chạy checker antenna độc lập và ghi `round_00/targets.json`, rồi dừng tại lời gọi ghi log:

```text
AttributeError: 'AntennaClosure' object has no attribute 'info'
```

Đây là lỗi tích hợp script do trợ lý viết: OpenLane 2.3.10 có `openlane.logging.info`, không có `Step.info`. Precheck trước đó chỉ nạp cấu hình, chưa kiểm tra lời gọi API này trong thân vòng lặp. Không phải bằng chứng CPU/Sobel hỏng. Chưa chèn diode có mục tiêu, chưa chạy các vòng sửa, chưa tới LVS/DRC cuối; không lấy PASS của RUN trước gán cho RUN này.

Checker đầu vòng hiện thấy 7 net/7 pin: `net4/_09966_/A0`, `net302/_12347_/S`, `cpu.reg_pc[1]/_06480_/B`, `_00001_/fanout1043/A`, `net230/_12090_/S`, `cpu.reg_pc[22]/_07513_/A`, `net944/_11592_/A1`. Đây là trạng thái trước sửa có mục tiêu. Report cell tại DRT ghi 491 antenna cells; khác với 9932 của repair_03, nhưng chưa có STA sau extraction để kết luận điện đạt.

## Bản sửa

- Thay cả hai `self.info(...)` bằng `info(...)` từ `openlane.logging` (nhánh bắt đầu vòng sửa và nhánh checker sạch). Giữ `self.warn`, đã xác minh tồn tại trong phiên bản cài đặt.
- Thêm `test_repair_api.py`: kiểm tra bắt được lời gọi lỗi cũ, kiểm tra các phương thức self đang dùng có tồn tại, và kiểm tra hai nhánh ghi log dùng logger thực tế. Ba kiểm tra chạy trong precheck của mỗi RUN; không chạy physical Step.start hay RTL simulation.
- Không đổi config vật lý, RTL, firmware, SDC, thuật toán chèn diode, số vòng tối đa hoặc checker. Đây là sửa lỗi API, chưa phải xác nhận thuật toán sửa antenna hội tụ.

## Chạy tiếp từ checkpoint có kiểm chứng

`06_run_openlane.sh` nhận thêm RUN nguồn làm tham số thứ hai. Ví dụ:

```bash
bash scripts/06_run_openlane.sh picorv32_sobel_clk50_repair_05 picorv32_sobel_clk50_repair_04
```

Script đóng băng nguồn sửa trong snapshot mới. `resume_checkpoint.py` chỉ cho dùng checkpoint nếu config vật lý, RTL gốc/bản sinh, constraints, pin order, image ID và PDK revision còn khớp. Hash snapshot và bằng chứng chức năng cũ/mới phải hợp lệ. Nếu khác, script dừng để yêu cầu RUN đầy đủ.

Toàn bộ file view mà state DRT tham chiếu được sao chép vào `run_inputs/<RUN mới>/resume_checkpoint/views`, gắn SHA256 và sửa đường dẫn state sang bản sao. Không sửa ODB hay snapshot RUN 4. CTS state và log congestion kế thừa được lưu kèm provenance. Lệnh OpenLane dùng `--from Sobel.AntennaClosure --with-initial-state .../resume_checkpoint/state.json`; không chạy lại synthesis/placement/DRT ban đầu. Đây là tính năng CLI đã kiểm tra trên bản cài 2.3.10.

Flow vẫn có 81 bước chính; các bước trước checkpoint được bỏ qua khi tiếp tục. Runtime RUN mới chỉ đo phần tiếp tục, không phải tổng thời gian từ RTL. Collector ghi rõ nguồn checkpoint, kiểm tra hash và phân biệt CTS/congestion kế thừa. Nếu vòng sửa đi dây lại, log congestion mới được ưu tiên. Antenna cuối vẫn phải lấy checker thực tế sau bước sửa, không dùng số từ checkpoint để suy ra PASS.

## Kiểm tra đã thực hiện

- `build/asic_precheck_e5deehg3`: 3 kiểm tra API đạt, cấu hình 81 bước và các bước con nạp được; lint/SDC đạt; bằng chứng ảnh/RTL/firmware khớp. Không chạy flow.
- Thử chuẩn bị trong `/tmp/sobel_resume_preflight_0fp3ftka`: dùng checkpoint thật của RUN 4, sao chép và xác minh đủ view/path/hash, từ chối ghi đè checkpoint. Kết quả ở `build/resume05_preflight.json`. Không sửa RUN nguồn; không thực thi physical step.
- `build/resume05_frozen_check_fcNQFSp1`: precheck trên snapshot có checkpoint đạt, `State.loads(..., validate_path=True)` nạp đủ các view đã sao chép trong Docker. Đây chỉ là nạp dữ liệu, không chạy lại DRT.
- Regression collector từ archive base_01 vẫn khớp 7 giá trị thực và nguồn stage.

Lệnh copy, chạy tiếp và collect ở [ASIC_RUN_GUIDE.md](ASIC_RUN_GUIDE.md). RUN 5 chưa được thực thi bởi trợ lý; antenna PASS, DRC/LVS và lỗi điện còn phải xác nhận từ lần chạy của người dùng.

## RUN 5: dbNet.getId và bản sửa repair_06

Archive: `reports/picorv32_sobel_clk50_repair_05_collect_20260912T052311709049Z.tar.gz`, SHA256 `7909199ffd5c451d1a91d4846d14f375ae47b65d18ecdba4e2c7742892499ff1`. Bản trích đọc: `build/repair05_review_q1550jx5`.

RUN 5 qua được logging và resolve đủ 7 pin, nhưng dừng trong targeted_diodes.py khi chụp kết nối trước sửa: `AttributeError: dbNet has no attribute getId`. Chưa gọi insert_diode, chưa ghi ODB output của bước này. Đây là lỗi API do trợ lý viết, không phải kết luận lỗi chức năng RTL.

Bản sửa thay ID bằng tên net ODB chính xác (không bỏ escape), tách capture_original/verify_original và chạy toàn bộ phần đọc/đối chiếu trước điểm thoát --plan-only. Ngay sau chèn diode vẫn kiểm tra từng master và kết nối gốc. Trong phạm vi thao tác này không đổi tên/xóa/tạo lại net, nên tên net là định danh kiểm tra phù hợp; không dùng phương thức không tồn tại.

Frozen precheck nay dùng chính ODB checkpoint và report antenna khớp ODB đó: resolve target, chụp/đối chiếu toàn bộ kết nối, rồi thử guard bằng dữ liệu kỳ vọng sai trong Python. Không thay ODB để thử. Kết quả thực tế: 14941 instance, 88674 terminal, 7 target; hai guard phát hiện master/net không khớp. Nạp config/lint/SDC và State.loads đều đạt. Bằng chứng: `build/resume06_frozen_check_XeOAvULh`.

Collector trước đó chỉ tìm state_out của bước ngoài nên báo METRICS SOURCE MISSING khi composite chưa hoàn tất. Đã thêm đọc state bước con và báo cáo antenna độc lập sau DRT/checkpoint. Regression trên chính archive RUN 5 tìm đúng round_00/01-check-antennas/state_out.json, giữ antenna 7/7 và FAIL_OR_INCOMPLETE; final metrics vẫn MISSING. Không coi đây là số liệu sign-off cuối.

Lệnh tiếp tục: `bash scripts/06_run_openlane.sh picorv32_sobel_clk50_repair_06 picorv32_sobel_clk50_repair_04`. Dùng checkpoint DRT RUN 4; RUN 5 không tạo checkpoint DRT mới. Giữ nguyên RUN 4/5, RTL, firmware, config vật lý và checker. Trợ lý chưa thực thi chèn diode/routing; hiệu quả antenna vẫn phải xác nhận từ RUN người dùng.
