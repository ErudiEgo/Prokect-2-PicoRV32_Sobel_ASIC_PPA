> Cập nhật 2026-09-14: RUN16 baseline_06 đã được chuẩn bị; xem RUN16_REPAIR_PLAN.md. RUN15 exit2 do slew/cap, fanout4; RUN12 vẫn là mốc bảo toàn. Chưa có kết quả RUN16.

<!-- Current launch target: baseline_06; retain baseline_01 as failed-run evidence. -->
# Mốc báo cáo DMA — RUN đầy đủ từ đầu

RUN duy nhất đang chuẩn bị: **picorv32_sobel_dma_clk50_baseline_06**.
RUN12 baseline_02 đã đạt Antenna/LVS/DRC, exit0 nhưng còn62 fanout; đã backup. RUN13 baseline_03 dừng ở bootstrap Tcl trước CTS. RUN14 baseline_04 dừng khi chọn clock buffer trùng tên giữa các thư viện. RUN15 baseline_05 đã sửa lựa chọn theo ODB master, đang chờ chạy. Xem RUN12_PRESERVATION_AND_FANOUT.md. Người dùng thực thi, trợ lý chỉ precheck.

## Phạm vi chốt

PicoRV32 RV32I + Sobel legacy MMIO/core + Sobel tile DMA/core + bộ phân xử bus.
Ảnh xám8bit, Sobel3×3, CPU firmware baseline và DMA đã test32/64/128/256.
RAM chương trình/input/output ngoài physical top; host đổi RGB sangL, testbench và replay
không phải hardware ASIC. Chưa nâng cấp RGB hoặc SW optimized cho mốc này.
Clock50ns (20MHz), SKY130 sky130A/sky130_fd_sc_hd, OpenLane2.3.10 Classic.
Giữ các constraint, checker và 33 annotation style upstream đã ghi nhận; không sửa ngưỡng để PASS.

## Thực thi hoàn toàn mới

Launcher08 không nhận parent. Launcher06 nhận đúng một tag từ launcher08.
Không --from, --with-initial-state, --skip, --last-run hoặc --overwrite.
run_inputs/TAG/execution_plan.json ghi full_from_start, parent_run=null, initial_state=null.
Classic81 bước gồm78bước gốc (CTS được bọc để đặt fanout mục tiêu) và3bước sửa bổ sung. Synthesis, floorplan, placement, CTS,
routing, extraction và các kiểm tra cuối đều thuộc RUN này.

Sửa antenna native sau DRT dùng routing vừa sinh trong chính RUN mới:
SOBEL_NATIVE_ANTENNA_REPAIR=true. SOBEL_ANTENNA_ONLY=false và
SOBEL_OUTPUT_BUFFER_REPAIR=false: không áp dụng hai pin ECO của RUN10 lên netlist mới.
Dùng thuật toán sửa đã học không có nghĩa kế thừa dữ liệu/checkpoint.
Nếu còn lỗi, collect và chẩn đoán. Mốc chỉ được chốt sau khi đọc report; không hứa PASS trước.
Nếu phải sửa và tạo baseline02 thì vẫn chạy đầy đủ từ đầu theo yêu cầu người dùng.

## Bằng chứng chức năng đóng băng

| RUN | SWcycles | HWcycles |
|---|---:|---:|
|soc_std32_shape10_01|452073|69406|
|soc_std64_00022_01|1845427|281750|
|soc_std128_00000002_01|7420738|1136398|
|soc_std256_4105_01|29781741|4565534|

Precheck xác minh hash snapshot, nguồn hiện hành, output golden, command exit status.
Snapshot mới gồm4ZIP benchmark_evidence và benchmark_link.json, cùng functional_evidence.zip
cho RUN32 làm liên kết chính. Firmware/SW đối chứng giữ nguyên, không claim SW tối ưu nhất.
Snapshot chứaRTL/TB/firmware/scripts/config/SDC/pinorder, nguồn physical dẫn xuất và hash;
environment.txt ghi Docker image digest, PDK resolved path. Không ghi đè RUN cũ.

## Người dùng chạy Ubuntu

Mở Docker Desktop và Engine/WSL integration trước. Đồng bộ:
```bash
bash "/mnt/e/aa. PPA_Project_List/aaa.PicoRV32_Sobel_ASIC_PPA/scripts/00_copy_to_ubuntu.sh"
```
```bash
cd "$HOME/openlane_projects/picorv32_sobel_asic_ppa"
```
Chạy FULL từ đầu (launcher tự precheck và đóng băng):
```bash
bash scripts/08_run_report_baseline.sh
```
Không cần chạy simulation lại để mở bằng chứng. Dòng FULL RUN FROM START xác nhận nhánh thực thi.
Kết thúc dù PASS/lỗi:
```bash
bash scripts/07_collect_asic.sh picorv32_sobel_dma_clk50_baseline_06
```
Gửi terminal summary và archive Windows. Đọc exit status, Antenna/LVS/DRC, setup/hold,
slew/cap/fanout, final views. Collector tiếp tục báo FAIL_OR_INCOMPLETE nếu còn vi phạm.
Power vectorless; IR drop có giả định nguồn vì VSRC_LOC_FILES chưa có. Không gọi full tapeout signoff.

## Mở OpenROAD sau khi có final ODB

```bash
bash scripts/09_open_final_openroad.sh picorv32_sobel_dma_clk50_baseline_06
```
Viewer tìm đúngfinal/*.odb, đọc bằng OpenROAD của image đã pin, project mountread-only.
Không chạy flow/synthesis/placement/routing, không sửa RUN; Tcl chỉ read_db và fit.
Có thể xem cell, clock tree, routing và chọn net. Đây là xemlayout, không phải tính lạiSTA/PPA.
GUI cần WSLg DISPLAY; nếu thiếu báo lỗi thay vì chạy lại flow.

Giữ runs/TAG, run_inputs/TAG, Dockerimage và PDKrevision. Collector đã bổ sung toàn bộ
final views (ODB/netlists/SPEF/SDC/GDS/LEF nếuflow xuất) vào archiveWindows, cùng snapshot.
Không xóa stage cũ. Archive không chứa cả PDK hay Dockerimage; chúng vẫn cần để tái mở đầy đủ.

## Kiểm tra chuẩn bị đã hoàn tất

- ASIC precheck: build/asic_precheck_T8ZiVbjU, config/lint/SDC/API PASS,81steps.
- Docker sha256:37c3bd4ea0534a276cb2deb88d601044857bad2807b9bc5b36efe9d02c62624e.
- PDK version0fe599b2afb6708d281543108caf8310912f54af; OpenROAD edf00dff99f6c40d67a30c0e22a8191c5d2ed9d6.
- Thử freeze trong build/full_freeze_audit_x5p13___ đạt:4ZIP, hashmanifest, configbound, khôngcheckpoint. Đây là audit tạm, không phải RUN baseline.
- Viewer Tcl đã đọc finalODB của RUN10 bằngOpenROAD -exit với projectread-only; khôngGUI/flow. Log build/openroad_view_read_audit.log. GUI mới sẽ mở sau RUN baseline cófinalODB.
- Các kiểm tra trên thuộc lần chuẩn bị cũ; trạng thái mới nhất xem RUN12_PRESERVATION_AND_FANOUT.md.

## Cập nhật RUN baseline01 đã chạy

Exit2: Antenna/LVS/DRC PASS; hold/slew/cap còn lỗi, fanout65. Chưa đạtbaselinecuối.
Chưa có final/ nhưng ODBstage vẫn xem được. Mở rõ chế độstage (khôngchứngnhậnPASS):
```bash
bash scripts/09_open_final_openroad.sh picorv32_sobel_dma_clk50_baseline_01 --latest-state
```
Viewer chọnODB từstatecuối, không sửaRUN hay chạyflow. Đã mởvà nạpODB thực tế trongOpenROADGUI.

## Lịch sử Baseline02 — sửa hold/slew/cap sau phân tích RUN01

RUN mới picorv32_sobel_dma_clk50_baseline_02, FULL từ đầu, không parent/checkpoint.
Đây là hồ sơ lần sửa trước; launcher08 hiện chạy baseline03, không chạy lại baseline02.

Bằng chứng RUN01, cornermax_ss_100C_1v60:
- Hold ext_rdata[2] → _21155_/D: slack−0.014998ns; ext_rdata[0] → _21153_/D: −0.008628ns.
- Các đường reg-to-reg không có hold violation theo metrics; hai lỗi làinput-to-register.
- 11slew entries cùngnet fanout26/X (buf_1), outputnet1680. Slew1.572214ns so với1.5ns.
- Cap0.085686pF so với giới hạnLiberty0.081492pF (không phải ngưỡngconfig0.2pF).
- Antenna0/0, LVS/DRC PASS, setupPASS; fanout65 vẫn phải theo dõi.
- PostGRTrepair từng báo0slew/cap vàholdWS0.101957ns; signoffRC sauDRT phát hiện các lỗi trên.
  Metric trung gian có thể được kế thừa; không gọi nó là signoff hoặc chứng minh tool sai.

Ba điều chỉnh có kiểm soát:
1. GRT_RESIZER_HOLD_SLACK_MARGIN0.05→0.20ns để tối ưu chừa dư hold trướcDRT.
2. GRT_DESIGN_REPAIR_MAX_SLEW_PCT/MAX_CAP_PCT40→55 để targettối ưu chặt hơn.
3. Bước bổ sung trướcResizerTimingPostGRT chuyển sang Sobel.RepairDesignSlowCorner,
   kế thừa đúngRepairDesignPostGRT và dùng corners_key riêng max_ss. Timingrepair vẫn3corner,
   signoff vẫn9corner; không bỏ checker hoặc nới constraintSDC/Liberty.

Không chèn ECO theo tênfanout26 vì netlist mới có thể đổi tên. Không đổi RTL/firmware/
clock/input-outputdelay/uncertainty. Antenna nativeclosure giữ nguyên. Thêmbuffer hoặc
resize có thể đổi area/power/routing và lỗi khác; phải đọc RUN02 thực tế mới biết PASS.
Đây là sửa cấu hình/flow triển khai vật lý, không có bằng chứng bài test ảnh gây lỗiASIC.

Precheck build/asic_precheck_MXXQeUvA: fourbenchmarkshash/golden PASS, config/lint/SDC/API PASS,
81step(78original+3additions). Chưa synthesis/simulation/PNR RUN02.


RUN12 sau đó đã chạy đạt Antenna/LVS/DRC và exit0, còn62fanout. Trạng thái và backup trong RUN12_PRESERVATION_AND_FANOUT.md.
