# H2 M3 — baseline đã freeze

Trạng thái: **H2_LINEBUFFER_BASELINE_FREEZE_PASS**. Nhóm A: bảo toàn baseline nghiên cứu, không thay đổi kiến trúc.

- Annotated Git tag cục bộ: `H2_LINEBUFFER_BASELINE`.
- Commit: `a5b8f2317589a90a599ea37d5bc2a782d71e99f0`.
- Parent: `e9ff741064810c1ce893745581a2d89917b0b238`.
- Gói: `baseline/H2_LINEBUFFER_BASELINE/`.
- Manifest SHA256: `d41639057c7ee48e10f86284a558ad43682fe8c741f1ff3d4e34c2a974299eb6`.

Đã audit lại17 ZIP gốc:3 M1,6 M2,7 M3 integration và1 M3 unit. Package chứa141 tệp nguồn trong sources.zip,17 archive bằng chứng trong evidence.zip, audit.json, provenance.json, README.md và manifest.json. Unit181ca và bảy integration workload đã đạt theo evidence có sẵn, bao gồm kết quả âm; không có simulation mới.

Đã kiểm tra147 Git blob khớp từng byte với141 source files và6 package files. Commit chỉ thay đường dẫn upgrade so với parent. Tag trỏ đúng commit trên; chưa push. Branch đang làm việc vẫn codex/rgb-from-run16, HEAD không chuyển; staged entries và index bytes giữ nguyên trong lần publication thành công. Các thay đổi stage1 chưa commit không được gom vào commit freeze và không bị sửa.

Nguồn là snapshot working tree, không phải toàn checkout sạch của parent RUN16. Trong provenance.json, helper đã trim một dấu cách đầu dòng status đầu tiên: `M .gitignore` tương ứng thay đổi unstaged ` M .gitignore` ở lần kiểm tra ban đầu, không phải staged modification. Package đã freeze được giữ nguyên; ghi rõ chi tiết định dạng ở đây. Checksum index có thay đổi trước publication trong khi staged contents vẫn trống; không dùng cache-byte khác biệt làm bằng chứng nội dung staged thay đổi.

RUN16 archive lịch sử được kiểm tra SHA256 và liên kết ở external_evidence của manifest, không sao chép138MB vào package. Archive gốc vẫn tại thư mục reports của stage1. Không dùng RUN16 làm PPA H2.

Thêm công cụ đọc-only scripts/verify_h2_freeze.py để kiểm tra inventory/hash package. Không sửa RTL/firmware/checker chức năng hoặc RUN cũ. Không chạy simulation, synthesis, OpenLane hay Vivado. Không tạo H3 branch. Các source metadata trạng thái lịch sử được giữ byte-exact; audit.json là trạng thái evidence tại freeze.

Muốn kiểm tra lại package, từ repository root:

```bash
python3 upgrade/scripts/verify_h2_freeze.py upgrade/baseline/H2_LINEBUFFER_BASELINE
```

Kiểm tra tag:

```bash
git rev-parse 'H2_LINEBUFFER_BASELINE^{commit}'
```

Lệnh chỉ kiểm tra lại, không cần chạy để tiếp tục. Không sửa package hoặc di chuyển tag; thay đổi mới dùng revision/RUN mới.

Giới hạn giữ nguyên: characterization gray480 chưa chạy; H2 PPA chưa chạy; H3/FPGA chưa triển khai. Bước kế tiếp là characterization H2 đã freeze: gray scaling, same-input tile16/32/64 và wait0/1/3 theo ma trận nhỏ có kiểm soát, giữ irregular/degenerate cases. Không generic hóa H2 trước khi đủ characterization/PPA.
