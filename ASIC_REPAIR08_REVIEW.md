# RUN 8 chưa hội tụ; RUN 9 chuyển sang native post-DRT repair

Archive gốc: `reports/picorv32_sobel_clk50_repair_08_collect_20260912T092407863171Z.tar.gz`. SHA256: `cf76f43b85ae15fdfb66048307b53c2bc57f30f5bb427d9c6ba731c4464db178`.

## Bằng chứng RUN 8

| Kiểm tra | Net lỗi | Pin lỗi |
| --- | ---: | ---: |
| Đầu RUN, kế thừa RUN 7 | 2 | 2 |
| Sau vòng 1 | 5 | 5 |
| Sau vòng 2 | 4 | 4 |
| Sau vòng 3 | 4 | 5 |

Hai pin ban đầu fanout901/A và fanout932/A không còn vi phạm sau vòng đầu. Các lỗi mới phát sinh ở pin khác. net286/_12550_/S vi phạm liên tiếp hai vòng rồi hết; cuối RUN là:

| Net | Pin | Lớp | Partial side-area ratio / limit |
| --- | --- | --- | --- |
| _02766_ | fanout165/A | met3 | 470.23 / 400 |
| _02766_ | fanout166/A | met3 | 470.23 / 400 |
| cpu.alu_out[7] | _13141_/D | met1 | 575.67 / 400 |
| cpu.reg_pc[25] | _07534_/A | met1 | 508.39 / 400 |
| net586 | _09751_/A1 | met1 | 406.37 / 400 |

Nguồn: RUN 8 `01-sobel-antennaclosure/closure_history.json`, `round_*/targets.json` và report antenna độc lập. LVS/DRC PASS; vẫn exit 2. Final state còn slew max_ss 12, nom_ss 6; cap max_ss/nom_ss 2; fanout 25. Không gọi đây là cải thiện tổng thể so với RUN 7.

## Vì sao đổi phương pháp

Script targeted_diodes.py trước đây xóa toàn bộ dbWire tín hiệu để tránh dây cũ sai vị trí sau legalization. Sau đó GlobalRouting/DRT chạy lại toàn thiết kế. Guard giữ topology logic nhưng không giữ hình học dây. Đây là thay đổi phạm vi lớn có thể tạo lỗi antenna mới trên net khác, phù hợp với các report quan sát được; không phải bằng chứng duy nhất giải thích mọi violation.

Đã đọc mã nguồn đúng commit OpenROAD đang cài `edf00dff99f6c40d67a30c0e22a8191c5d2ed9d6`:

- [GlobalRouter.cpp](https://github.com/The-OpenROAD-Project/OpenROAD/blob/edf00dff99f6c40d67a30c0e22a8191c5d2ed9d6/src/grt/src/GlobalRouter.cpp): repairAntennas dùng IncrementalGRoute, cập nhật các net thay đổi.
- [RepairAntennas.cpp](https://github.com/The-OpenROAD-Project/OpenROAD/blob/edf00dff99f6c40d67a30c0e22a8191c5d2ed9d6/src/grt/src/RepairAntennas.cpp): nhận biết DetailedRouting và không hủy toàn bộ wire như trường hợp dựng wire từ global route; có xử lý vị trí diode và legalization nội bộ.

## Bản RUN 9

Bắt đầu từ checkpoint pre-filler RUN 7 (2/2, fanout 21), giữ RUN 8 để đối chiếu. Không lấy RUN 8 kém hơn làm mặc định mới.

Trong continuation antenna-only:
1. Check antenna độc lập trên ODB đã route và ghi targets/report.
2. Capture topology nguyên bản.
3. Gọi native repair_antennas trên dây đang có, 1 iteration mỗi lần, giữ margin 30 của cấu hình.
4. DetailedRouting và guard: cell/master/kết nối cũ phải giữ, chỉ cho phép thêm đúng PDK diode đã nối tín hiệu.
5. Kiểm tra antenna độc lập lại, tối đa ba vòng; dừng sớm khi 0/0.

Không gọi targeted_diodes.py để chèn/xóa dây trong nhánh continuation này; không gọi full GlobalRouting hoặc resizer. Native router vẫn có thể sửa vị trí/hình học cần thiết và DRT vẫn có thể cập nhật dây; chưa khẳng định mọi segment khác đều bất biến. Không thay RTL/firmware/SDC hoặc nới checker. LVS/DRC/timing/slew/cap/fanout cuối vẫn là tiêu chuẩn đánh giá.

## Precheck và giới hạn

`build/resume09_frozen_check_MeTMV7ju/`: config Classic 81 bước, API regression, lint, SDC-load và frozen view/hash đạt. ODB thật 14989 instance/88930 terminal, đúng 2 target của RUN 7. Native Tcl nạp ODB/lib/SDC và xác nhận có detailed wires/API repair_antennas; nhánh PREFLIGHT không gọi repair hay route. Guard thử bằng dữ liệu kỳ vọng trên ODB thật: chấp nhận diode PDK có kết nối, từ chối thêm logic.

Trợ lý chưa thực thi flow, sửa diode, placement hoặc routing; RUN 9 chưa có kết quả. Kết quả precheck không chứng minh antenna sẽ PASS. Slew/cap/fanout của RUN 7 vẫn chưa được sửa trong thử nghiệm này và có thể làm flow exit 2 dù antenna đạt.

Lệnh: `bash scripts/06_run_openlane.sh picorv32_sobel_clk50_repair_09 picorv32_sobel_clk50_repair_07`. Thu thập: `bash scripts/07_collect_asic.sh picorv32_sobel_clk50_repair_09`. Xem ASIC_RUN_GUIDE.md để copy/cd.
