# Math Vision Lab

Math Vision Lab là mô-đun giải và trực quan hóa toán phổ thông Việt Nam từ lớp 1 đến lớp 9. Mục tiêu không chỉ là đưa ra đáp án, mà còn giúp học sinh nhìn thấy dữ kiện, phép biến đổi và quan hệ toán học qua từng bước.

README này chỉ mô tả Math Lab. Các mô-đun khác của EduVisionAI không thuộc phạm vi tài liệu này.

> **Phạm vi repository GitHub này:** đây là bản bàn giao chỉ chứa mã nguồn,
> kiểm thử, benchmark/training và tài liệu thuộc Math Lab. Các thành phần dùng
> chung của ứng dụng EduVisionAI (đăng nhập, lớp học, dashboard, gateway và hạ
> tầng chạy đầy đủ) không được sao chép vào repository. Vì vậy
> `docs/math-lab/start-demo.sh` là đặc tả tích hợp và chỉ chạy khi Math Lab được
> đặt lại vào checkout EduVisionAI có đủ các dịch vụ phụ thuộc.

## Trạng thái hiện tại

Số liệu được kiểm tra ngày **31/08/2026**:

| Hạng mục | Kết quả |
|---|---:|
| Họ bài toán đã có trong danh mục kiểm thử | 71 |
| Họ bài có luồng giải chính xác và dữ liệu sinh bài riêng | 66 |
| Họ bài dùng chung parser, solver và renderer hiện có | 5 |
| Họ bài không có renderer phù hợp | 0 |
| Ma trận chấp nhận | 270/270 |
| Kiểm thử backend Math Lab | 253/253 |
| Kiểm thử frontend | 542/542 |
| Kiểu trực quan hóa | 29 |

Các con số trên là bằng chứng cho danh mục bài đã quan sát, không phải lời cam kết rằng mọi cách diễn đạt tùy ý đều đã được bao phủ. Năm họ bài chưa có dữ liệu SFT chuyên biệt gồm phương trình phân thức bậc nhất, trị tuyệt đối, trùng phương, chứa căn và hữu tỉ; chúng đang sử dụng năng lực parser/solver/renderer dùng chung.

> Trạng thái SFT trong báo cáo là trạng thái dữ liệu và luồng sinh bài. Chỉ được gọi là “mô hình đã fine-tune” khi có checkpoint huấn luyện và kết quả đánh giá độc lập.

Tài liệu kiểm chứng chi tiết:

- [Ma trận bao phủ lớp 1–9](docs/math-lab/GRADE_1_9_COVERAGE.md)
- [Kiến trúc trực quan hóa](docs/math-lab/VISUAL_ARCHITECTURE.md)
- [Mức độ sẵn sàng cho giáo viên](docs/math-lab/TEACHER_READINESS_ASSESSMENT.md)

## Bàn giao nhanh

- Nhánh bàn giao: `FE-update-and-remove-`. Không phát triển hoặc push trực tiếp lên `main`.
- Điểm vào giao diện: `frontend/src/features/math-lab/`.
- API và bộ phân tích: `master_be/app/api/math_lab.py` và `master_be/app/services/math_lab/`.
- Parser/solver xác định: `master_be/app/schemas/math_lab_*.py`.
- Lịch sử và feedback: `data_storage/app/api/routes/math_lab.py`.
- Dữ liệu, benchmark và fine-tune: `training/math_lab/`.
- Tài liệu thiết kế, giới hạn và bằng chứng: `docs/math-lab/`.
- Lệnh chạy toàn bộ demo: `./docs/math-lab/start-demo.sh`.

Thứ tự nên đọc khi nhận dự án:

1. README này để biết trạng thái và các giới hạn thật.
2. [README kỹ thuật Math Lab](docs/math-lab/README.md) để xem các regression/case đã xử lý.
3. [Kiến trúc trực quan](docs/math-lab/VISUAL_ARCHITECTURE.md) và [ngữ pháp trực quan](docs/math-lab/VISUAL_GRAMMAR.md).
4. [Quản trị dữ liệu](docs/math-lab/DATA_GOVERNANCE.md), [autolearning](docs/math-lab/AUTOLEARNING.md) và `training/math_lab/README.md` trước khi train.
5. [Failure taxonomy](docs/math-lab/FAILURE_TAXONOMY.md) và [roadmap](docs/math-lab/ROADMAP.md) trước khi mở rộng dạng bài.

## Math Lab làm gì?

Một lượt xử lý điển hình:

1. Nhận đề từ văn bản gõ tay, ảnh, bài mẫu hoặc lịch sử.
2. Giữ nguyên đề người dùng đã nhập.
3. Phân tích ký hiệu, dữ kiện, yêu cầu và loại bài.
4. Lập kế hoạch giải theo từng bước sư phạm.
5. Chọn mô hình trực quan phù hợp.
6. Dựng cảnh bằng renderer React xác định, không để mô hình AI tự vẽ tùy ý.
7. Kiểm tra tính nhất quán giữa đề gốc, lời giải, đáp án và hình minh họa.
8. Lưu lịch sử và phản hồi; phản hồi không tự động trở thành dữ liệu huấn luyện.

## Nguyên tắc bắt buộc

### Không tự ý sửa đề

- Văn bản người dùng gõ được giữ nguyên để hiển thị và đối chiếu.
- Chuẩn hóa chỉ diễn ra ở biểu diễn nội bộ phục vụ tính toán.
- “Đề gốc” và “cách hệ thống hiểu” là hai trường riêng.
- Nếu đề sau phân tích không còn khớp đề gốc, frontend chặn mô phỏng thay vì âm thầm vẽ một bài khác.
- Với ảnh, văn bản OCR được ghi rõ là nội dung nhận dạng từ ảnh.

Ví dụ, với đề:

```text
6x^3 + 4x^2 - 5x - 1 = 0
```

hệ thống không được tự biến nó thành `y = 6x - 1`, bỏ các hạng tử, hoặc vẽ đường thẳng thay cho đồ thị bậc ba.

### Không đoán khi đề mơ hồ

Nếu thiếu dữ kiện, ký hiệu không rõ hoặc có nhiều cách hiểu hợp lý, hệ thống phải:

- chỉ ra phần chưa rõ;
- đưa ra cách hiểu đang được đề xuất;
- yêu cầu xác nhận khi việc lựa chọn làm thay đổi bài toán;
- không bịa hệ số, đơn vị, hình học hoặc đáp án.

Parser phải tiêu thụ toàn bộ biểu thức. Phần không hiểu không được phép bị bỏ qua âm thầm.

## Cách nhập đề bằng bàn phím

Người dùng không cần bàn phím toán học chuyên dụng. Math Lab hỗ trợ ký hiệu phổ biến và cách viết bằng tiếng Việt:

| Ý định | Ví dụ được chấp nhận |
|---|---|
| Lũy thừa | `x^2`, `x mũ 2`, `x lũy thừa 2` |
| Căn bậc hai | `sqrt(9)`, `√9`, `căn 9`, `căn bậc hai của (x + 1)` |
| Phân số | `3/5`, `3 phần 5`, `ba phần năm` |
| Hỗn số | `3 và 2 phần 5` |
| Nhân | `4*98`, `4x98`, `4X98`, `4 × 98`, `4·98`, `4⋅98`, `4 nhân 98` |
| Chia | `10/2`, `10 : 2`, `10 chia 2` |
| Giai thừa | `92!`, `92 giai thừa`, `giai thừa của 92` |
| Cộng, trừ | `a + b`, `a cộng b`, `a - b`, `a trừ b` |
| So sánh | `>`, `<`, `>=`, `<=`, `lớn hơn`, `bé hơn` |
| Ngoặc | `2(x + 3)`, `2 nhân (x cộng 3)` |

`3 2 phần 5` là cách viết có thể mơ hồ. Nên nhập `3 và 2 phần 5` nếu muốn biểu diễn hỗn số, hoặc dùng ngoặc để làm rõ ý.

## Phạm vi bài toán

Danh mục hiện tại bao phủ các nhóm chính:

- số học, bốn phép tính, thứ tự thực hiện phép tính;
- phân số, số thập phân, phần trăm và tỉ số;
- đại lượng, đổi đơn vị, thời gian, tiền và chuyển động;
- toán có lời văn một bước và nhiều bước;
- dãy số, quy luật và suy luận;
- biểu thức, đa thức và phân tích nhân tử;
- phương trình, bất phương trình và hệ phương trình;
- hàm số và đồ thị;
- hình học phẳng, hình khối, đo độ dài, diện tích và thể tích;
- thống kê, bảng, biểu đồ và xác suất cơ bản.

Danh sách đầy đủ từng họ bài và trạng thái triển khai nằm trong [GRADE_1_9_COVERAGE.md](docs/math-lab/GRADE_1_9_COVERAGE.md).

## Phương trình được xử lý

| Dạng | Ví dụ | Cách trực quan chính |
|---|---|---|
| Bậc nhất một ẩn | `3x - 5 = 10` | cân bằng hai vế, trục số |
| Bậc nhất có ngoặc | `2(x + 3) = 14` | phân phối và cân bằng |
| Bậc nhất dạng phân thức | `(x + 1)/3 = 2` | thanh phân số, biến đổi tương đương |
| Trị tuyệt đối | `|x - 2| = 3` | khoảng cách trên trục số |
| Bậc hai | `6x^2 - 5x - 1 = 0` | parabol, giao điểm với trục hoành |
| Trùng phương | `x^4 - 5x^2 + 4 = 0` | đặt ẩn phụ và kiểm tra nghiệm |
| Chứa căn | `sqrt(x + 1) = 3` | điều kiện xác định và đối chiếu nghiệm |
| Hữu tỉ | `1/(x - 1) = 2` | điều kiện mẫu và kiểm tra nghiệm |
| Bậc ba | `6x^3 + 4x^2 - 5x - 1 = 0` | đồ thị bậc ba và nghiệm thực |
| Hệ hai ẩn | `x + y = 5; x - y = 1` | giao điểm hai đường thẳng |
| Hệ ba ẩn tuyến tính | `x + y + z = 6; ...` | mặt phẳng và nghiệm hệ |

Phương trình bậc ba là năng lực mở rộng, không phải nội dung cốt lõi của toàn bộ chương trình lớp 1–9. Với biểu thức hữu tỉ phức tạp, hệ thống vẫn phải kiểm tra điều kiện xác định và có thể trả về “chưa hỗ trợ an toàn” thay vì rút gọn sai.

## Trực quan hóa

Math Lab có 29 loại cảnh trực quan xác định, được chia theo cấu trúc toán học:

- vật đếm, nhóm và bó chục;
- thanh phần, tỉ lệ và phân số;
- cân bằng phương trình và trục số;
- bảng, biểu đồ, dãy số và cây xác suất;
- đường thẳng, parabol, đồ thị bậc ba và hệ tọa độ;
- hình học phẳng, góc, tam giác, đường tròn;
- khối hộp, hình trụ và các mô hình đo lường;
- dòng thời gian, tiền, vận tốc và sơ đồ lời văn.

Một hình minh họa đạt yêu cầu phải cho thấy được ít nhất một quan hệ toán học cần dùng để giải, không chỉ trang trí hoặc hiển thị đáp án cuối.

## Kiến trúc xử lý

```text
Văn bản / ảnh
      │
      ▼
ProviderDocument
      │  giữ đề gốc và nguồn dữ liệu
      ▼
MathSemanticModel
      │  dữ kiện, yêu cầu, biểu thức, ràng buộc
      ├──────────────► VisualDecision ─► VisualPlan
      │
      ▼
PedagogyPlan
      │  các bước giải và kiểm chứng
      ▼
MathScene / MathWorldState
      │
      ▼
React renderer xác định
```

Các thư mục chính:

```text
master_be/                              API điều phối và pipeline Math Lab
document_renderer/                     parser, solver và renderer service
frontend/src/features/math-lab/        giao diện Math Lab
training/math_lab/                     catalog, benchmark và dữ liệu đánh giá
docs/math-lab/                          tài liệu thiết kế và bằng chứng
```

## Thuật toán và vị trí mã nguồn

Math Lab là hệ lai. AI/VLM chỉ đọc ảnh hoặc bổ sung semantic JSON khi grammar xác định chưa nhận được đề; phép giải, chọn renderer, dựng hình và kiểm tra tính đúng đắn nằm trong code xác định.

### 1. Chuẩn hóa đề gõ tay

File chính: `master_be/app/schemas/math_lab_input.py`.

`canonicalize_typed_math` chuẩn hóa Unicode và các cách gõ tương đương nhưng không thay `source_text`. Nó xử lý các nhóm ký hiệu như:

- `^`, `mũ`, `lũy thừa`, các ký tự `²`, `³`;
- `sqrt`, `√`, `căn`, `căn bậc hai của`;
- `nhân`, `chia`, `cộng`, `trừ`, `bằng`;
- phân số dạng `3/5`, `3 phần 5`, hỗn số có từ nối;
- dấu nhân/chia Unicode, ngoặc toàn chiều rộng và nhãn problem type từ provider.

Nguyên tắc là giữ hai lớp dữ liệu: đề gốc để đối chiếu và biểu diễn chuẩn hóa để parser tính toán. Parser phải tiêu thụ toàn bộ chuỗi; không được bỏ phần không hiểu rồi giải một bài khác.

### 2. Grammar số học và toán lời văn

File chính: `master_be/app/schemas/math_lab_text.py`.

Các extractor hẹp đọc đúng toán hạng đã in và chỉ kích hoạt khi đủ dấu hiệu cấu trúc. Chúng bao gồm bốn phép tính, giai thừa từ `0!` đến `500!`, phân số, hình chữ nhật, chuyển động tỉ lệ thuận, bài công-ngày, phần còn lại liên tiếp, tam giác vuông, góc hạ, tam giác xiên có đường cao, hình bình hành, hệ giảm giá hai mặt hàng và hệ phương trình tuyến tính.

Các thuật toán quan trọng:

- cộng/trừ: mô hình `whole`, `part`, `remaining`, không ghi đáp số vào dữ kiện;
- nhân nhỏ: nhóm bằng nhau hoặc khối giá trị hàng; nhân nhiều chữ số: tích riêng theo từng chữ số rồi dịch đúng hàng;
- chia nhỏ: chia nhóm; số bị chia lớn: chia dài, hạ từng chữ số và kiểm tra `số chia × thương + số dư`;
- giai thừa: tích giảm dần đến 1, tính chính xác bằng `BigInt`, hiện các mốc `10!`, `20!`, ... cùng số chữ số và số 0 tận cùng;
- tỉ số: tổng số phần → giá trị một phần → đại lượng cần tìm;
- phân số phần còn lại: sau mỗi lần lấy phân số, phần còn lại trở thành “toàn bộ mới”;
- công-ngày: bảo toàn `số người × số ngày` khi năng suất mỗi người không đổi;
- chuyển động: chuẩn hóa đơn vị rồi dùng `s = v × t`, `v = s/t`, `t = s/v`;
- tam giác vuông: Pythagoras và các tỉ số lượng giác, có kiểm tra cạnh huyền/góc;
- hệ giảm giá: lập hai phương trình từ tổng giá gốc và tổng tiền sau giảm, không dùng giá trong lựa chọn làm dữ kiện.

### 3. Biểu thức tuyến tính, phương trình và hệ

File chính: `master_be/app/schemas/math_lab_linear.py`.

Mỗi vế được phân tích thành `Σ hệ_số × biến + hằng_số`; lấy vế trái trừ vế phải để có dạng chuẩn. Bộ parser hỗ trợ hệ số nguyên, thập phân, phân số, biến ở cả hai vế và phân phối một số qua ngoặc tuyến tính. Nó từ chối `xy`, `x(x+1)`, `2/x` và các dấu hiệu phi tuyến thay vì ép thành bậc nhất.

Hệ tuyến tính dùng số hữu tỉ `Fraction` và khử Gauss-Jordan:

1. lập ma trận mở rộng từ mọi hệ số, kể cả hệ số 0 của biến bị khuyết;
2. chọn pivot, đổi hàng, chuẩn hóa pivot và khử các hàng còn lại;
3. so sánh `rank(A)` với `rank([A|b])`;
4. phân loại nghiệm duy nhất, vô số nghiệm hoặc vô nghiệm;
5. giữ cả nghiệm số và chuỗi phân số chính xác;
6. lưu từng phép biến đổi hàng để frontend trình bày lại.

Hệ hai ẩn được dựng bằng giao của hai đường thẳng trên Oxy. Hệ ba ẩn được giải bằng cùng bộ khử và dựng các mặt phẳng trên Oxyz. Mọi nghiệm duy nhất phải được thay lại vào toàn bộ phương trình.

### 4. Phương trình phi tuyến

Các file chính:

- `master_be/app/schemas/math_lab_nonlinear.py`: bậc hai, bậc ba và mặt cong ba biến;
- `master_be/app/schemas/math_lab_equations.py`: phân thức bậc nhất, trị tuyệt đối, trùng phương, chứa căn và hữu tỉ.

Thuật toán đang có:

- bậc hai: chuẩn hóa `ax²+bx+c=0`, tính biệt thức, nghiệm thực và đỉnh parabol;
- bậc ba: chuẩn hóa hệ số, tìm nghiệm thực có kiểm chứng và dựng đường cong lấy mẫu;
- trị tuyệt đối: tách hai nhánh theo định nghĩa khoảng cách;
- trùng phương: đặt `t=x²`, giải bậc hai theo `t`, chỉ nhận `t≥0`, rồi trả `x=±√t`;
- chứa căn: đặt điều kiện xác định, bình phương, sinh ứng viên và thay lại phương trình gốc để loại nghiệm ngoại lai;
- hữu tỉ: ghi điều kiện mẫu khác 0, quy đồng tối đa hai mẫu tuyến tính, giải tử bậc không quá hai rồi loại nghiệm cấm;
- mặt `x² + by + cz = d`: lấy mẫu lưới, chỉ giữ điểm thỏa phương trình và dựng các lát parabol/đường sinh.

### 5. Semantic model và provider

File chính: `master_be/app/services/math_lab/analyzer.py`.

`MathProblemAnalyzer` ưu tiên grammar xác định. Với ảnh hoặc đề ngoài grammar, `OllamaMathVisionProvider` yêu cầu model trả `ProviderDocument` JSON. Pydantic đặt `extra=forbid`, kiểm tra evidence, role, unit, reference, unknown và constraint trước khi chuyển sang `MathSemanticModel`.

Các bước repair chỉ được phục hồi số hoặc cấu trúc đã xuất hiện trong đề gốc. Provider không được đưa đáp số cần tìm vào `quantities`, không được sinh HTML/SVG/JavaScript và không quyết định code giao diện.

### 6. Chọn hình, lập bài giảng và dựng scene

Các file chính:

- `master_be/app/services/math_lab/decision_engine.py`: ánh xạ family/domain/grade sang renderer và kiểm tra readiness;
- `master_be/app/services/math_lab/registry.py`: danh sách renderer, miền và lớp được phép;
- `master_be/app/services/math_lab/pedagogy.py`: các bước quan sát → biến đổi → kết luận → kiểm tra;
- `master_be/app/services/math_lab/visual_plan.py`: primitive, binding, stage và oracle;
- `master_be/app/services/math_lab/foundation.py`: ghép decision, pedagogy và visual plan.

Decision engine fail closed: thiếu binding bắt buộc hoặc renderer không phù hợp thì trả trạng thái có giải thích, không dựng một hình thay thế sai nghĩa.

### 7. Trạng thái và thuật toán trực quan ở frontend

Các file chính:

- `frontend/src/features/math-lab/state/mathWorldState.js`: một world state dùng chung;
- `frontend/src/features/math-lab/derive/deriveScene.js`;
- `frontend/src/features/math-lab/derive/deriveCoverage.js`;
- `frontend/src/features/math-lab/derive/deriveCurriculum.js`;
- `frontend/src/features/math-lab/visualizations/registry.js`;
- `frontend/src/features/math-lab/renderers/`.

Các hàm `derive*` chỉ tính từ semantic values/bindings đã kiểm tra. `progress` chung điều khiển mọi biểu diễn đồng bộ. Đồ thị đường thẳng giữ dạng tổng quát `ax+by=c` để vẽ được cả đường đứng; parabol/bậc ba lấy mẫu trong miền quan sát; hình học kiểm tra độ dài/góc hợp lệ; phân số dùng GCD/LCM; biểu đồ, xác suất và mô hình phần-trăm đều dựng từ cùng world state.

Renderer phải có DOM text cho kết luận quan trọng, không để thông tin chỉ nằm trong canvas/SVG. `UnsupportedRenderer` là từ chối an toàn, không được tính là trực quan hóa thành công.

### 8. Đơn vị, kiểm chứng và lưu dữ liệu

- `master_be/app/services/math_lab/units.py` chuẩn hóa các đơn vị tương thích trước khi tính.
- Visual oracle kiểm tra quantity/binding, source preservation và invariant của scene.
- Redis giữ tối đa 5 lượt gần nhất cho mỗi người dùng bằng transaction `LPUSH + LTRIM + EXPIRE`.
- PostgreSQL lưu feedback, semantic model và scene ở trạng thái `pending_review`; `training_eligible` mặc định là `false`.
- Luồng autolearning không tự cập nhật model. Quy trình dự kiến là ẩn danh → người duyệt → dataset bất biến → model league/holdout → canary → rollback.

## Model đang dùng và fine-tune đã thực hiện

### Model production hiện tại

| Hạng mục | Giá trị |
|---|---|
| Runtime | Ollama |
| Model | `qwen3-vl:8b-instruct` |
| Vai trò | OCR ảnh, tách câu/choices và sinh semantic JSON khi grammar xác định không đủ |
| Context | 12.288 token |
| Output tối đa | 6.144 token |
| GPU layers | 999, mục tiêu nạp toàn bộ model lên GPU |
| Trạng thái | Base model đang chạy; chưa phải checkpoint do dự án fine-tune |

`qwen3-vl:8b-thinking` đã được benchmark nhưng không hoàn thành schema đầy đủ trong cửa sổ 180 giây, nên không dùng cho demo thời gian thực. Xem `docs/math-lab/MODEL_BENCHMARK.md`.

### Fine-tune đã chạy thật

Có một smoke QLoRA trên `Qwen/Qwen3-VL-4B-Instruct`, family `fraction_power`, với đúng 1 ảnh train và 1 ảnh validation, 1 step:

| Thuộc tính | Giá trị |
|---|---|
| Phương pháp | LoRA/SFT, `r=8`, `alpha=16`, target `q_proj/k_proj/v_proj/o_proj` |
| Train loss | 0,247867 |
| Eval loss | 0,241940 |
| Eval mean token accuracy | 0,959119 |
| Adapter | `training/math_lab/checkpoints/qwen3vl-4b-fraction-power-smoke/adapter_model.safetensors` |
| SHA-256 | `427afed14d9033d1e878d5105d6bd1bd074ba5e9dc536c1fd62d2087f225236f` |
| Dung lượng adapter | 11.839.096 byte |
| Toàn thư mục checkpoint | khoảng 76 MB trên máy bàn giao |

Đây chỉ là checkpoint kiểm tra pipeline; `training/math_lab/benchmarks/model_ledger.json` đánh dấu `eligible=false`. Nó chưa được nạp vào production và không chứng minh chất lượng lớp 1–9.

### Fine-tune chưa thực hiện

Target production trong `training/math_lab/configs/qwen3vl_qlora.json` là `Qwen/Qwen3-VL-8B-Instruct` với QLoRA NF4, vision tower đóng băng, completion-only loss và 3 epoch. Chưa có checkpoint 8B đầy đủ. Lần chạy đã dừng ở VRAM gate vì còn dưới 12.000 MiB trống; không dừng tiến trình của người khác để giành GPU.

Không có DPO/RL production. Feedback của giáo viên không tự trở thành dữ liệu train.

## Dữ liệu ở đâu?

### Thành phần được Git theo dõi

| Đường dẫn | Nội dung |
|---|---|
| `training/math_lab/scripts/prepare_sft.py` | generator dữ liệu semantic text + ảnh |
| `training/math_lab/prompts/math_scene_analyzer_system.txt` | system prompt/contract đầu ra |
| `training/math_lab/catalogs/grade_1_9_exam_families.json` | 71 họ bài quan sát và trạng thái |
| `training/math_lab/sources.lock.json` | nguồn, revision, checksum, license và quyền sử dụng |
| `training/math_lab/sources/source_manifest.jsonl` | provenance theo policy |
| `training/math_lab/dataset_version.json` | content digest, seed và số lượng split |
| `training/math_lab/benchmarks/` | acceptance matrix, model ledger và scripts đánh giá |
| `training/math_lab/discovery/` | fingerprint, clustering và phát hiện family mới |

### Dữ liệu chỉ có cục bộ, bị Git ignore

| Đường dẫn | Trạng thái hiện tại |
|---|---|
| `training/math_lab/data/generated/math_scene_train.jsonl` | 11.360 records |
| `training/math_lab/data/generated/math_scene_validation.jsonl` | 1.704 records |
| `training/math_lab/data/generated/math_scene_test.jsonl` | 1.704 records |
| `training/math_lab/data/generated/observed_questions.jsonl` | 6.587 dòng quan sát |
| `training/math_lab/data/generated/` | khoảng 345 MB cả JSONL và media sinh |
| `training/math_lab/data/raw/` | nguồn thô cục bộ theo `sources.lock.json`; không commit |
| `training/math_lab/checkpoints/` | checkpoint/optimizer/tokenizer cục bộ; không commit |
| `training/math_lab/.venv/` | môi trường train cục bộ; không commit |

Clone Git chỉ nhận code, catalog, manifest và checksum; không nhận 345 MB dữ liệu sinh hoặc 76 MB checkpoint smoke. Người bàn giao phải sao chép các thư mục ignored qua kênh nội bộ được phép, hoặc tái tạo dataset bằng script. Không đưa `kaggle.json`, `.env`, token, raw data không rõ bản quyền hay thông tin học sinh lên Git.

Dataset hiện được sinh xác định với seed `260826`, 5.680/852/852 semantic cases và hai modality text+image, tương ứng 11.360/1.704/1.704 records. Audit gần nhất đạt schema validity 100%, unknown leakage 0, renderer decision accuracy 100% và không trùng stem giữa các split. Đây là kiểm tra dữ liệu sinh, không phải accuracy của model production trên đề thật.

Nguồn web hiện có 6 bản ghi `TAXONOMY_ONLY`, 4 `METADATA_ONLY`, 0 `TRAIN_ALLOWED`; vì vậy không có nội dung web nào được đưa trực tiếp vào SFT. We-Math, MathVista, MathNet và VLM curriculum được giữ ngoài train làm ứng viên holdout.

## Chạy Math Lab

### Yêu cầu

- Docker và Docker Compose
- Ollama có model mặc định `qwen3-vl:8b-instruct`
- chứng chỉ HTTPS cục bộ theo cấu hình của dự án

Các file mẫu cấu hình:

- `master_be/.env.example`
- `document_renderer/.env.example`
- `data_storage/.env.example`

Chỉ sao chép file mẫu khi file `.env` tương ứng chưa tồn tại. Không ghi đè cấu hình hoặc khóa đang dùng.

```bash
cp master_be/.env.example master_be/.env
cp document_renderer/.env.example document_renderer/.env
cp data_storage/.env.example data_storage/.env
```

Lần chạy đầu:

```bash
./docs/math-lab/start-demo.sh --bootstrap
```

Các lần sau:

```bash
./docs/math-lab/start-demo.sh
```

Mở:

```text
https://localhost:8443/#/math-lab
```

Stack demo dùng compose riêng tại `docs/math-lab/docker-compose.demo.yml` để hạn chế ảnh hưởng đến dữ liệu và dịch vụ ngoài Math Lab.

Kiểm tra container:

```bash
docker compose -f docs/math-lab/docker-compose.demo.yml ps
```

## Kiểm thử

Backend Math Lab:

```bash
cd master_be
PYTHONPATH=. pytest -q test/test_math_lab_analyzer.py test/test_math_lab_foundation.py test/test_math_lab_linear.py
```

Frontend:

```bash
cd frontend
npm test -- --run
```

Kiểm tra ma trận lớp 1–9:

```bash
python training/math_lab/scripts/audit_exam_coverage.py
python training/math_lab/scripts/audit_sft.py
```

Khi thay đổi parser, solver hoặc renderer, cần kiểm tra tối thiểu:

- đề gốc không bị thay đổi;
- toàn bộ biểu thức được parser xử lý;
- nghiệm thỏa lại phương trình hoặc ràng buộc ban đầu;
- nghiệm ngoại lai và điều kiện xác định được loại đúng;
- hình minh họa đúng loại bài và đúng các giá trị trong lời giải;
- trường hợp không hỗ trợ trả về thông báo có cấu trúc, không làm vỡ giao diện.

## API Math Lab

Các route được cung cấp dưới tiền tố `/api/v1/math-lab`:

| Phương thức | Route | Chức năng |
|---|---|---|
| GET | `/capabilities` | năng lực parser, solver và renderer |
| POST | `/analyze/text` | phân tích đề nhập bằng văn bản |
| POST | `/analyze/image` | nhận dạng và phân tích đề từ ảnh |
| POST | `/plan` | tạo kế hoạch giải và trực quan hóa |
| GET | `/history` | đọc lịch sử Math Lab |
| POST | `/history` | lưu một lượt xử lý |
| POST | `/feedback` | lưu phản hồi của người dùng |

## Những việc còn thiếu và giới hạn đã biết

Các mục này phải được xử lý trước khi tuyên bố “mọi bài lớp 1–9 đều giải được”:

1. Chưa có checkpoint Qwen3-VL 8B fine-tune đầy đủ, chưa có model-league/holdout đủ điều kiện production.
2. Năm family `fractional_linear_equation`, `absolute_value_equation`, `biquadratic_equation`, `radical_equation`, `rational_equation` có parser/solver/renderer nhưng chưa có family SFT chuyên biệt.
3. Catalog 71 family là baseline quan sát, không phải chứng minh đã bão hòa mọi đề Việt Nam. Saturation audit nhiều batch theo lớp chưa hoàn tất.
4. Cách gõ thiếu quan hệ vẫn còn mơ hồ. Ví dụ `4x+y-9 và 5y=10` hiện bị từ chối vì dòng đầu là biểu thức không có dấu `=`. Nếu hỗ trợ quy ước “biểu thức bằng 0”, giao diện phải hiện cách hiểu và yêu cầu xác nhận, không âm thầm sửa đề.
5. Renderer Oxy hiện chỉ trình bày đúng hai đường; hệ ba phương trình nhưng chỉ có hai ẩn đang bị từ chối để tránh bỏ mất phương trình thứ ba.
6. Parser hữu tỉ chỉ hỗ trợ tối đa hai mẫu tuyến tính khác nhau và tử sau quy đồng bậc không quá hai.
7. OCR chữ viết tay, phân số xếp chồng, ảnh mờ/nghiêng và đề nhiều cột cần benchmark thật lớn hơn. Dataset ký hiệu viết tay hiện chỉ là ứng viên adapter OCR riêng.
8. Autolearning mới dừng ở lưu feedback, discovery và promotion gate; chưa tự động hóa ẩn danh, human review, canary và rollback end-to-end.
9. `UnsupportedRenderer` vẫn cần tồn tại cho đề thiếu dữ kiện hoặc ngoài phạm vi. Không được thay nó bằng hình đoán hoặc lời hứa “không bao giờ lỗi”.
10. Cần chạy lại browser E2E bằng tài khoản thật sau mỗi thay đổi deploy; unit test, build hoặc HTTP 200 riêng lẻ không chứng minh màn hình người dùng đúng.
11. Toàn bộ suite `data_storage/test/unit` hiện dừng ở bước collect vì bảng SQLAlchemy `class_invitations` bị khai báo hai lần. Các module Math Lab vẫn compile và chạy trong stack demo, nhưng lỗi tương thích phần lớp học này cần được sửa trước khi coi toàn repository là xanh.

Backlog chi tiết nằm trong `docs/math-lab/ROADMAP.md` và `docs/math-lab/TEACHER_READINESS_ASSESSMENT.md`.

## Quy tắc bàn giao và phát hành

- Chỉ commit/push vào `FE-update-and-remove-`; không sửa lịch sử hay push `main`.
- Trước commit: chạy `git diff --check`, test backend/frontend, build, audit dataset và coverage.
- Rà staged diff để không có `.env`, private key, token, mật khẩu, raw dataset, generated dataset, checkpoint, cache hoặc virtualenv.
- Không gọi model production là “đã fine-tune” cho tới khi có checkpoint 8B và báo cáo holdout đạt quality gate.
- Khi đẩy xong, so sánh `git rev-parse HEAD` với `git ls-remote origin refs/heads/FE-update-and-remove-`.
- Người nhận checkpoint/dataset ignored phải kiểm tra SHA-256 trước khi dùng.

## Khi nào được xem là hoàn thành?

Một dạng toán chỉ được xem là hỗ trợ an toàn khi đồng thời đạt các điều kiện:

1. nhận diện đúng đề và không sửa nội dung;
2. giải đúng với kiểm tra ngược;
3. có lời giải từng bước phù hợp cấp lớp;
4. có renderer đúng cấu trúc toán học hoặc giải thích rõ vì sao không cần hình;
5. xử lý được dữ kiện thiếu, mơ hồ và trường hợp vô nghiệm;
6. có kiểm thử hồi quy cho ví dụ chuẩn và ví dụ biên;
7. chạy được trong luồng giao diện thật, không chỉ trong kiểm thử đơn vị.

Mục tiêu của Math Lab là mở rộng dần phạm vi có kiểm chứng. Khi gặp bài ngoài phạm vi an toàn, hệ thống phải nói rõ giới hạn và giữ nguyên đề, thay vì tự sửa đề để tạo ra một hình có vẻ hợp lý.
