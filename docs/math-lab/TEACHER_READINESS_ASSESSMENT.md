# Đánh giá mức sẵn sàng cho giáo viên

> Chốt đánh giá lại: 28/08/2026. Phạm vi là giáo viên tải một ảnh đề Toán bất kỳ từ lớp 1 đến lớp 9, không chỉ các preset đẹp đã chuẩn bị sẵn.

## Kết luận ngắn

**Điểm hiện tại: 7,5/10 cho sản phẩm Math Lab tổng quát lớp 1–9.**

- Nếu chỉ dùng trong danh sách dạng bài đã xác nhận hỗ trợ: **8,6/10**, phù hợp để pilot; hệ thống tự kiểm tra schema/renderer, giáo viên chỉ đánh giá tính hữu ích sư phạm sau kết quả.
- Nếu quảng bá là “đưa ảnh đề Toán lớp 1–9 bất kỳ vào đều có mô phỏng đúng”: **chưa đạt**, chưa nên bàn giao đại trà.
- Khuyến nghị triển khai hiện tại: pilot nội bộ với nhãn **Dạng bài được hỗ trợ**; ứng dụng tự kiểm tra semantic bằng schema/grammar/VisualPlan và tự mô phỏng, không bắt giáo viên duyệt dữ kiện kỹ thuật. Góp ý sau kết quả đã được lưu ở trạng thái `pending_review`.

## Cách chấm

| Hạng mục | Trọng số | Điểm đạt | Căn cứ |
|---|---:|---:|---|
| Đọc ảnh và semantic trên case được hỗ trợ | 20 | 17 | Ảnh thật `(-2/5)^3` được Qwen3-VL 8B đọc đủ stem, 4 choices, dấu âm, tử, mẫu, số mũ; unknown không rò vào dữ kiện. Chưa có benchmark ảnh thật lớn. |
| Bao phủ dạng đề lớp 1–9 | 25 | 17 | Catalog hiện có 66 họ quan sát và 66/66 đạt semantic case + renderer exact. Điểm chưa tăng vì đây vẫn là baseline đề đại diện, chưa đạt saturation hoặc holdout toàn quốc. |
| Trực quan đúng bản chất sư phạm | 20 | 16 | Có 28 renderer, relationship graph và VisualPlan; đã bổ sung tập nghiệm, ba mô hình lượng giác lớp 9 và mặt cong Oxyz. Oracle tổng quát và visual regression theo mọi difficulty band còn partial. |
| Trải nghiệm giáo viên | 10 | 9 | Một lần bấm là tự đọc và mô phỏng; có nhiều câu, lịch sử 5 bài, feedback sau kết quả và safe abstention. Không còn màn bắt giáo viên kiểm tra semantic. |
| Ổn định runtime và vận hành | 15 | 11 | Stack demo 8443 đã cô lập, health 200 và volume external fail-closed. Chưa có backup/restore tự động và từng phát hiện volume cũ không còn trên host. |
| Fine-tune và đánh giá production | 10 | 5 | Dataset 71 họ/14.768 records text+ảnh đã audit, version hóa và có cycle tự động fail-closed. Checkpoint 4B vẫn chỉ là smoke; 8B bị VRAM gate chặn và chưa có teacher-labeled holdout/model league đầy đủ. |
| **Tổng** | **100** | **75** | **7,5/10** |

Điểm 7,5 không có nghĩa là các scene exact chỉ đúng 75%. Nó phản ánh sản phẩm tổng quát vẫn thiếu holdout ảnh thật quy mô lớn, saturation toàn quốc, oracle và vận hành production đã diễn tập đầy đủ.

## Coverage kiểm chứng từ đề lớp 1–9

Audit máy đọc được nằm ở [`training/math_lab/catalogs/grade_1_9_exam_families.json`](../../training/math_lab/catalogs/grade_1_9_exam_families.json). Đây là baseline từ một số đề/ma trận đại diện, không phải khẳng định đã liệt kê hết mọi biến thể trên toàn quốc.

| Lớp | Họ bài quan sát | Đúng trọn vẹn | Partial | Chưa có renderer | Coverage chính xác |
|---:|---:|---:|---:|---:|---:|
| 1 | 8 | 8 | 0 | 0 | 100% |
| 2 | 10 | 10 | 0 | 0 | 100% |
| 3 | 9 | 9 | 0 | 0 | 100% |
| 4 | 11 | 11 | 0 | 0 | 100% |
| 5 | 13 | 13 | 0 | 0 | 100% |
| 6 | 13 | 13 | 0 | 0 | 100% |
| 7 | 9 | 9 | 0 | 0 | 100% |
| 8 | 6 | 6 | 0 | 0 | 100% |
| 9 | 14 | 14 | 0 | 0 | 100% |
| **Toàn bộ catalog** | **66** | **66** | **0** | **0** | **100%** |

Con số 100% chỉ áp dụng cho 66 họ đã được quan sát và ghi vào catalog, không
được dùng để quảng cáo “mọi đề Toán lớp 1–9 đều chạy”. Ma trận sinh tự động đầy
đủ nằm ở [GRADE_1_9_COVERAGE.md](GRADE_1_9_COVERAGE.md).

### Biên chưa được chứng minh

- Chưa có bộ holdout ảnh thật đủ lớn cho từng lớp, từng nguồn ảnh và từng mức
  khó; OCR mờ, chữ viết tay và đề nhiều cột vẫn cần benchmark độc lập.
- Discovery chưa chứng minh catalog đã bão hòa toàn quốc; dạng biến đổi hình,
  đối xứng hoặc biến thể chứng minh mới phải được thêm thành family khi gặp.
- 66/66 catalog exact là coverage của baseline hiện tại, không phải xác suất
  một đề ngẫu nhiên ngoài phân phối sẽ thành công.

## Những gì giáo viên có thể dùng ngay

Cho phép pilot với các family đã có gate và scene đúng cấu trúc:

- thêm/bớt vật thể; nhân/chia theo nhóm;
- phân số bằng nhau, cộng, trừ, nhân; lũy thừa phân số;
- tỉ số từ đại lượng đã biết;
- phương trình bậc nhất dạng `ax+b=c`;
- hàm bậc nhất và điểm tọa độ;
- diện tích/chu vi hình chữ nhật;
- thể tích hình hộp chữ nhật;
- mô hình diện tích `(a+b)^2`;
- chuyển động một chặng theo quãng đường-vận tốc-thời gian.

Trong pilot, giáo viên vẫn phải xem lại OCR và dữ kiện trước khi chiếu cho học sinh. Không dùng fallback để tự động trình chiếu một family chưa có trong allowlist.

## Điều kiện để nâng lên 8/10 tổng quát

1. Mở rộng discovery có provenance và chứng minh saturation trên nhiều bộ đề độc lập; family mới phải có renderer exact, không tăng điểm bằng fallback gần nghĩa.
2. Thi hành oracle tổng quát cho từng VisualPlan stage và visual regression theo family × difficulty band.
3. Tạo bộ holdout ảnh đề thật có quyền sử dụng, tối thiểu 100 câu/lớp và có hai giáo viên gán nhãn độc lập.
4. Đo riêng OCR exact match, semantic role F1, family accuracy, renderer accuracy, teacher accept-without-edit và thời gian phản hồi p50/p95.
5. Chỉ train adapter 8B sau khi nhãn teacher-reviewed đủ lớn; smoke adapter 4B hiện tại không được thay model production.
6. Thêm backup/restore định kỳ cho các external volume và diễn tập rollback production-current/previous.

## Lệnh tái kiểm chứng

```bash
python training/math_lab/scripts/prepare_sft.py
python training/math_lab/scripts/audit_sft.py
python training/math_lab/scripts/audit_exam_coverage.py

cd master_be
pytest -q test/test_math_lab_foundation.py test/test_math_lab_analyzer.py

cd ../frontend
npm test -- --run
npm run build
```

Điểm phải được chấm lại sau mỗi đợt renderer và bộ đề holdout; không nâng điểm chỉ vì tăng số record synthetic hoặc train loss giảm.
