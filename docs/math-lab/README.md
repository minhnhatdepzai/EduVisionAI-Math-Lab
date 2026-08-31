# Math Vision Lab

> Trạng thái được kiểm chứng ngày 28/08/2026. Tài liệu này phân biệt rõ chức năng đang chạy, checkpoint smoke và kế hoạch fine-tune production. Mức sẵn sàng tổng quát cho giáo viên hiện được chấm **7,5/10**; xem [đánh giá và coverage lớp 1–9](TEACHER_READINESS_ASSESSMENT.md).

Math Vision Lab biến ảnh hoặc văn bản đề Toán lớp 1–9 thành mô phỏng có thể nhìn và chạy từng bước. Người dùng không cần biết tên renderer, trục, scene hay semantic model: thao tác chính là **Tải ảnh → Đọc đề và trực quan hóa**.

## Luồng đang chạy

```text
Ảnh/văn bản
  → Qwen3-VL đọc đề và xuất ProviderDocument JSON
  → Pydantic kiểm tra schema, evidence, đại lượng và unknown
  → relationship graph + policy chọn VisualConcept và biểu diễn
  → VisualPlan ghi primitive, stage, binding, state delta và oracle bắt buộc
  → pedagogy planner tạo các bước giảng dạy
  → React renderer dựng cảnh từ cùng một MathWorldState
  → tự chạy mô phỏng; giáo viên không phải kiểm tra semantic hay chọn renderer
```

- Ảnh được gửi qua HTTPS cùng origin, giới hạn chờ phía trình duyệt 600 giây; Nginx chờ upstream 300 giây và backend chờ Ollama tối đa 240 giây.
- Câu trắc nghiệm được đọc kèm choices. Nếu model nhận ra `multiple_choice` nhưng bỏ sót A/B/C/D, analyzer tự đọc bù từ chính ảnh; code không tự bịa phương án.
- Policy và renderer là deterministic. Model AI chỉ nhận diện cấu trúc toán, không sinh HTML/SVG/JavaScript và không được ghi đáp số cần tìm thành dữ kiện đã biết.
- Màn hình tự dựng và tự chạy ngay sau một lần bấm. Luồng `Kiểm tra dữ kiện` đã bị gỡ khỏi Math Lab vì đây không phải việc của giáo viên; các grammar hẹp và renderer deterministic chịu trách nhiệm chặn những fallback sai nghĩa.
- Ảnh có nhiều câu tạo thanh `Câu 1`, `Câu 2`, …; nhấn một câu sẽ tự lập scene tương ứng.

## Model và công nghệ

| Tầng | Đang dùng | Trách nhiệm |
|---|---|---|
| Vision runtime | Ollama + `qwen3-vl:8b-instruct` | OCR, tách câu, choices, domain, problem type và semantic quantities |
| Hợp đồng dữ liệu | FastAPI, Pydantic v2, `ProviderDocument`, `MathSemanticModel`, `MathScene` | Cấm field lạ, kiểm tra evidence/role/unit/reference và không để unknown rò vào quantities |
| Chọn trực quan | Rule-based `VisualDecisionEngine` + registry | Ánh xạ dạng toán sang renderer đã đăng ký; không để model tự chọn code giao diện |
| Kịch bản dạy | `PedagogyPlanner` | Tạo các mốc quan sát, biến đổi và kết luận |
| Giao diện | React 19, Vite 6, CSS/SVG, Three.js cho cảnh 3D | Playback, bước trước/sau, cùng một world state và error boundary chống màn hình trắng |
| Hạ tầng | Nginx HTTPS, Docker Compose, NATS JetStream | Same-origin API, health/readiness và đồng bộ hệ thống |

Registry production hiện có 29 ID: 28 renderer trực quan và một trạng thái `unsupported`. Ngoài các mô hình nền tảng còn có `place_value`, `column_algorithm`, `unit_scale`, `data_chart`, `number_compare`, `probability_simulator`, `percent_grid`, `algebra_tiles`, `part_whole`, `shape_pattern`, `calendar`, `factor_lattice`, `expression_tree`, `circle_model` và `solution_set`; `unsupported` là trạng thái từ chối an toàn chứ không được tính là renderer đúng cho một họ bài.

Runtime giữ `qwen3-vl:8b-instruct` làm model chính vì đây là biến thể tuân thủ structured JSON ổn định nhất trên GPU 16 GB hiện tại. `qwen3-vl:8b-thinking` đã được cài và benchmark nhưng một yêu cầu với toàn bộ schema không hoàn thành trong giới hạn 180 giây, nên không được thay làm model chính để tránh tái phát 504. Cấu hình `num_gpu` đã tăng từ 28 lên 999: Ollama hiện nạp model Instruct 100% GPU, context 12.288 token; smoke văn bản thực tế mất khoảng 7–10 giây thay vì CPU-offload.

## Case chuẩn `4 + 3`

Regression ngày 27/08/2026: provider nhận đúng `addition_basic` nhưng bỏ trống
`quantities`, còn tia số phía trình duyệt tự thay dữ liệu thiếu bằng `0`, dẫn
đến cảnh sai `0 + 0 = 0`. Pipeline hiện:

1. Grammar hẹp chỉ nhận biểu thức số học ngắn và chép đúng hai toán hạng `4`,
   `3` đã in; không ghi đáp số `7` vào known quantities.
2. Semantic model tạo quan hệ `part_whole` giữa hai phần và unknown toàn bộ.
3. Decision engine chỉ cho `object_group` và `number_line` chạy khi đủ hai
   binding; renderer không còn mặc định dữ liệu thiếu thành số 0.
4. Trình duyệt thật trên HTTPS đã hiện bảy chấm, phép tính `4 + 3 = 7`, tia số
   bắt đầu ở 4 và nhảy ba bước tới 7; không có `unsupported` hay HTTP 5xx.

Ảnh E2E: [addition-basic-e2e.png](evidence/addition-basic-e2e.png).

## Case chuẩn `58 xe tải − 38 xe rời bãi`

Với đề `Trong bãi có 58 chiếc xe tải. Có 38 chiếc xe rời bãi. Hỏi xe tải còn
lại trong bãi là bao nhiêu?`, pipeline hiện:

1. Hiểu được cả trật tự “bớt 38” lẫn “38 chiếc xe rời bãi”; chỉ phục hồi số
   khi đồng thời có vật đếm, hành động rời đi và câu hỏi phần còn lại.
2. Giữ `58` ở role `count_initial`, `38` ở `count_change`, đáp số tiếp tục là
   unknown; relation xác định `whole − removed_part = remaining_part`.
3. Dựng 58 biểu tượng xe tải: ở bước cuối 20 xe còn lại giữ màu, 38 xe rời bãi
   chuyển xám; hiện trực tiếp `58 − 38 = 20`.
4. Tia số hai chữ số lùi theo chục `58 → 48 → 38 → 28 → 20`, chỉ ghi các mốc
   `0, 10, 20, 30, 40, 50, 58` để không chồng nhãn.

API HTTPS và trình duyệt thật qua cổng 8443 đều đã kiểm chứng trạng thái
`ready`, hai renderer `object_group + number_line`, không còn `unsupported`.

## Case chuẩn `(1 + 1) × 2`

Regression ngày 27/08/2026: API vẫn trả HTTP 200 nhưng provider gắn family
`multiplication_basic` và để `quantities=[]`, nên renderer không có toán hạng để
dựng cảnh. Pipeline hiện:

1. Grammar hẹp nhận biểu thức `(a + b) × c` hoặc `(a − b) × c`, gồm các ký
   hiệu `×`, `x`, `*`, khoảng trắng tùy ý và câu hỏi có dấu/không dấu như
   `bằng mấy`, `bầng mấy`, `bang may`; chỉ chép ba số đã in vào quantities,
   không ghi kết quả vào dữ kiện đã biết.
2. Giữ đúng thứ tự phép tính: tính trong ngoặc trước, sau đó mới nhân; semantic
   model ghi relation `operation_tree` thay vì làm phẳng thành phép nhân cơ bản.
3. Dựng trực quan hai phần trong ngoặc, rồi tạo `c` nhóm bằng nhau với
   `a + b` đồ vật trong mỗi nhóm và chỉ hiện kết quả ở bước kết luận.
4. Nếu người dùng không chọn lớp, case này mặc định lớp 3 và inspector hiện tên
   tiếng Việt **Tính trong ngoặc rồi nhân**.

Trình duyệt thật qua HTTPS đã xác nhận chính input `(1+1) x 2 bầng mấy` dựng
hai nhóm, mỗi nhóm hai đồ vật, kết luận `(1 + 1) × 2 = 2 × 2 = 4`; không có
HTTP 4xx/5xx, lỗi JavaScript hay thông báo thiếu dữ kiện. Ảnh E2E:
[parenthesized-multiplication-e2e.png](evidence/parenthesized-multiplication-e2e.png).

Regression tiếp theo `( 1 + 1 ) x 2 bang may?` cũng đã được chạy lại trên
trình duyệt thật và qua migration lịch sử: family được sửa thành
`parenthesized_addition_multiplication`, đủ ba quantity, renderer `grouping`
ở trạng thái `ready` với bốn bước. Ảnh E2E:
[parenthesized-multiplication-unaccented-e2e.png](evidence/parenthesized-multiplication-unaccented-e2e.png).

## Case chuẩn biểu thức và phương trình `x, y, z`

Ba mẫu regex riêng cho `ax+b=c`, `ax+by=c` và `ax+by+cz=d` đã được thay bằng
**một bộ chuẩn hóa tuyến tính tổng quát**: nó đọc cả hai vế thành
`Σ hệ số × biến + hằng số` rồi trừ hai vế cho nhau. Nhờ vậy mọi đề tuyến tính
in ra đều đi cùng một đường, không phụ thuộc vào việc biến nằm ở vế nào.

    3x + y = z    →  3x + y − z = 0
    y = 2x + 1    →  −2x + y = 1
    5x = 2x + 9   →  3x = 9
    3(x + 2) − 5 = 2x + 7  →  3x + 1 = 2x + 7  →  x = 6

Việc phân loại chỉ dựa vào cấu trúc đã chuẩn hóa: số biến có hệ số khác 0 và
việc có dấu bằng.

1. `2x+1` là biểu thức một biến → `algebra_tiles`: hai thanh `x` và một ô đơn vị.
2. `2x+3=9`, `5x = 2x + 9` là phương trình một ẩn → `balance`, cùng một phép
   toán ở cả hai đĩa cân.
3. `3(x+2)−5=2x+7` có ngoặc → family riêng `compound_linear_equation`; cân hiển
   thị thêm bước phá ngoặc và bước thu gọn, không nhảy thẳng tới `ax = d`.
4. `2x+y=1` và `y=2x+1` là phương trình hai biến → đường thẳng trên Oxy.
5. `x+y=3; x−y=1` là hệ hai phương trình → hai đường trên cùng hệ trục, kèm
   trạng thái *cắt nhau / song song / trùng nhau* đúng theo định thức.
6. `3x+y+z=6` và `-2x+4y-z=8` là phương trình ba biến → mặt phẳng trên Oxyz.

### `3x+y=z` — mặt phẳng đi qua gốc O

Đây là ca P0 của đợt sửa này. `3x+y=z` **không phải** phương trình một ẩn và
cũng **không phải** dạng không hỗ trợ. Sau chuẩn hóa nó là `3x + y − z = 0`,
tức mặt phẳng qua gốc tọa độ với vectơ pháp tuyến `(3; 1; −1)`.

Vì vế phải bằng 0 nên cả ba giao điểm với Ox, Oy, Oz **trùng nhau tại O**.
Renderer không được bịa ba giao điểm khác nhau; thay vào đó cảnh hiện:

1. dạng chuẩn `3x + y − z = 0` sau khi chuyển mọi hạng tử về một vế;
2. ba trục Oxyz cùng tỉ lệ và gốc O;
3. câu giải thích O(0; 0; 0) đã là một nghiệm nên mặt phẳng đi qua gốc;
4. mặt phẳng mờ vuông góc với vectơ pháp tuyến `n(3; 1; −1)`, có mũi tên `n`;
5. các điểm nghiệm mẫu, mỗi điểm được **thay ngược vào phương trình** trước khi
   được vẽ, kèm phép thay số hiển thị bên dưới.

Kết luận ghi rõ có **vô số** bộ `(x; y; z)` thỏa mãn; không đưa ra một giá trị
duy nhất cho x, y hay z.

Đề không xác định hoặc mâu thuẫn (`x=x`, `x+1=x+2`) không tạo HTTP 5xx và cũng
không dựng hình sai: Math Lab đưa ra một lời nhắc tiếng Việt bình thường, không
chứa từ nội bộ như renderer, schema hay payload.

Bộ kiểm thử cố định cho họ bài này nằm ở
[`master_be/test/test_math_lab_linear.py`](../../master_be/test/test_math_lab_linear.py)
và trong ma trận nghiệm thu `training/math_lab/benchmarks/`.

### Tập nghiệm và mặt cong Oxyz

Ba họ đại số từ đề lớp 9 dùng renderer `solution_set` riêng thay vì một thẻ
“chưa hỗ trợ”: bất phương trình tô đúng nửa trục với đầu mút đóng/mở, phương
trình tích đánh dấu từng nghiệm, còn điều kiện xác định dùng điểm rỗng cho các
giá trị làm mẫu bằng không. Parser phân thức chỉ được kích hoạt khi đề thật sự
nói đến mẫu, phân thức hoặc điều kiện xác định; chuỗi đơn vị `km/h` và công thức
Viète `-b/a`, `c/a` không còn bị nhận nhầm.

Với `x² + 5y − z = 0`, pipeline nhận family
`quadratic_surface_three_variables`, lấy đúng hệ số đã in và dựng một lưới mặt
cong trên Oxyz. Các lát theo một phương là parabol, các đường sinh theo phương
còn lại là đường thẳng; điểm mẫu chỉ được vẽ khi thay ngược thỏa phương trình.
Nó không còn bị ép thành mặt phẳng tuyến tính hoặc yêu cầu một giá trị duy nhất
cho `x`, `y`, `z`.

## Case chuẩn `giải tam giác vuông`

Báo lỗi thực tế từ trang chạy: đề `Hãy giải tam giác ABC vuông tại A. Biết
AB = 5 cm, BC = 13 cm. (Góc làm tròn đến phút).` hiện thẻ nhắc “chưa đủ dữ
kiện” với bảng **DỮ KIỆN ĐÃ BIẾT rỗng**, dù cả hai cạnh đều đã in trong đề.

Nguyên nhân không nằm ở thẻ nhắc mà ở khâu đọc dữ kiện: grammar cũ chỉ hiểu một
dạng duy nhất — *hai cạnh góc vuông, tìm cạnh huyền* — và bắt buộc phải có
`Tính <đoạn>`. Câu “giải tam giác” không nêu một đoạn cụ thể nào và cho sẵn một
cạnh góc vuông cùng **cạnh huyền**, nên không khớp mẫu nào, không phục hồi được
toán hạng, và readiness từ chối dựng hình vì thật sự không có số để dựng.

Nay grammar đọc **mọi cạnh và góc nhọn đã in** của tam giác vuông, còn relation
ghi rõ cạnh nào là cạnh huyền — dữ kiện quyết định cạnh còn lại được tính bằng
tổng hay hiệu bình phương:

1. Dựng tam giác đúng tỉ lệ, đánh dấu góc vuông tại đỉnh đã nêu và ghi nhãn hai
   cạnh đã cho.
2. `AC² = BC² − AB² = 13² − 5²` → `AC = 12 cm` (Pythagoras).
3. `sin B = AC / BC = 12/13` → `B ≈ 67°23'`.
4. `C = 90° − B ≈ 22°37'` vì hai góc nhọn phụ nhau.
5. Kiểm tra `AB² + AC² = BC²` và `B + C = 90°`.

Hai cạnh góc vuông kèm câu hỏi chỉ tìm cạnh huyền vẫn giữ family hẹp
`right_triangle_hypotenuse`. Nếu cạnh góc vuông dài hơn cạnh huyền đã nêu thì
cảnh **không** được dựng — không có tam giác nào như vậy — thay vì hiện một độ
dài ảo.

### Ba mô hình lượng giác hình học lớp 9

- `angle_of_depression_distance`: dựng hải đăng, đường ngang song song mặt
  biển, tia nhìn và cung góc hạ; tính khoảng cách ngang bằng `h / tan(α)`.
- `oblique_triangle_altitude_solution`: đường cao chia tam giác xiên thành hai
  tam giác vuông, rồi hiện riêng `h/sin(B)`, `h/sin(C)` và hai đoạn
  `h/tan(B)`, `h/tan(C)` trước khi ghép cạnh đáy.
- `parallelogram_perpendicular_diagonal_area`: dựng đúng `AC ⟂ AD`, dùng
  `AC = AD × tan(D)` làm chiều cao và kết luận `S = AD × AC`.

Các phép tính và hình vẽ dùng cùng một relationship graph; renderer không tự
đoán số từ bố cục ảnh.

## Case chuẩn `angle_bisector`

Với đề `Cho ∠xOy = 80°, Ot là tia phân giác của ∠xOy. Số đo ∠xOt bằng?`, pipeline hiện:

1. Giữ `80` trong quantity `role=angle`, `unit=degree`; nếu VLM bỏ sót, grammar hẹp chỉ phục hồi số được in cạnh ký hiệu góc và không tự chép đáp án.
2. Chọn `geometry_2d`, không còn rơi vào thẻ `unsupported`.
3. Dựng hai tia Ox, Oy và cung toàn góc `80°`.
4. Dựng tia Ot ở chính giữa, hiển thị hai cung bằng nhau.
5. Kết luận trực quan `∠xOt = ∠tOy = 80° ÷ 2 = 40°` ở bước cuối.

## Case chuẩn `sequential_fraction_remainder_ratio`

Với đề bán `160 kg` gạo trong ba ngày, ngày 1 bán `3/8` toàn bộ, ngày 2 bán `1/4` phần còn lại và hỏi tỉ số ngày 3/ngày 1, pipeline hiện tự động:

1. Phục hồi đúng `mass=160 kg`, `numerator/denominator=3/8` và `addend_numerator/addend_denominator=1/4` từ chữ in; không ghi đáp số vào quantities.
2. Chọn `bar_model` riêng cho phép lấy phân số liên tiếp trên phần còn lại, không rơi sang thông báo bài trung bình.
3. Chia thanh `160 kg` thành 8 phần, tô 3 phần của ngày 1: `160 × 3/8 = 60 kg`; còn `100 kg`.
4. Coi `100 kg` là toàn bộ mới, chia thành 4 phần; ngày 2 lấy `25 kg`, ngày 3 còn `75 kg`.
5. Đặt hai thanh ngày 3 và ngày 1 cạnh nhau, hiện `75 : 60`, cùng chia cho 15 và kết luận `5 : 4`.

## Case chuẩn `work_rate_with_variable_people`

Với đề tổ có `8 người`, dự định làm trong `6 ngày`, sau đó bổ sung `4 người` và năng suất mỗi người như nhau, pipeline hiện:

1. Phục hồi ba dữ kiện in trong đề kể cả khi VLM nhận đúng family nhưng bỏ trống quantities; sửa domain sai từ `probability` về `ratio`. Số ngày dùng `unit=one` vì đây là số cột ngày rời rạc trong mô hình công-ngày, tránh làm frontend cũ hiểu nó như thời gian vật lý. Bản ghi lịch sử cũ có `unit=day` hoặc `quantities=[]` cũng được migration từ chính `source_text` khi đọc lại.
2. Chọn `bar_model`, không rơi vào `unsupported`.
3. Dựng ma trận `8 × 6 = 48` ô, mỗi ô là một công-ngày.
4. Cập nhật tổ mới: `8 + 4 = 12 người`, rồi xếp lại đúng 48 ô thành 12 cột người.
5. Đọc số hàng ngày mới: `48 ÷ 12 = 4 ngày`; kiểm tra `12 × 4 = 48 công-ngày`.

Smoke trình duyệt thật qua `https://localhost:8443` đã xác nhận cả bài mới và bốn bản ghi lịch sử cũ đều trả `bar_model`; không còn `quantity unit is not supported`, thẻ `unsupported` hay HTTP 5xx.

## Case chuẩn `distance_time_direct_proportion`

Với đề `Một ô tô đi trong 5 giờ được 225 km. Ô tô đó đi trong 8 giờ được quãng đường là bao nhiêu`, pipeline hiện:

1. Chuẩn hóa `start_time/end_time=""` từ VLM thành `null`, nên trường giờ đồng hồ tùy chọn không còn làm cả ProviderDocument lỗi schema và trả HTTP 502.
2. Với văn bản khớp grammar hẹp, lấy đúng ba dữ kiện in trong đề `5 giờ`, `225 km`, `8 giờ` bằng đường xử lý xác định; không gọi VLM và không ghi `360 km` vào dữ kiện đã biết.
3. Gắn family `distance_time_direct_proportion`, relation `direct_proportion` và chọn `bar_model` với trạng thái `ready`.
4. Dựng 5 ô giờ bằng nhau ứng với 225 km; quy về một ô: `225 ÷ 5 = 45 km/giờ`.
5. Dựng tiếp 8 ô cùng kích thước, mỗi ô 45 km; kết luận `45 × 8 = 360 km` và kiểm tra `360 ÷ 8 = 45 km/giờ`.

Kiểm thử còn có biến thể `4 giờ → 180 km, hỏi 7 giờ` để khóa theo họ bài thay vì theo đáp số. API HTTPS thật trả 200 cho cả analyze và plan; trình duyệt headless thật xác nhận không còn thông báo lỗi schema, hiện đầy đủ sơ đồ, phép quy về đơn vị và kết quả. Ảnh E2E: [distance-time-direct-proportion-e2e.png](evidence/distance-time-direct-proportion-e2e.png).

## Case chuẩn `two_item_discount_system`

Với đề hai quyển sách có tổng giá niêm yết `270.000 đồng`, sách Toán giảm
`10%`, sách Ngữ Văn giảm `20%`, tổng thực trả `228.000 đồng`, pipeline hiện:

1. Gom phần dẫn và bốn dòng a–d của ảnh về một câu toán; không còn để Vision tách thành năm câu thiếu dữ kiện.
2. Giữ đúng bốn dữ kiện in trong đề và hai ẩn `x`, `y`. Hai giá ở khẳng định d) chỉ là claim cần kiểm tra, không được chép thành dữ kiện hay đáp số.
3. Chọn `percent_grid`, dựng hai thẻ sách và hai thanh 100%; tô rõ phần giữ lại `90%` và `80%` sau giảm giá.
4. Lập song song `x + y = 270.000` và `0,9x + 0,8y = 228.000`; lấy phương trình thứ hai trừ `0,8(x+y)=216.000` để thấy `0,1x=12.000`.
5. Kết luận `x=120.000`, `y=150.000`; kiểm tra hóa đơn `108.000 + 120.000 = 228.000`.
6. Đánh dấu khẳng định d) **sai** vì ảnh đã đảo hai giá: sách Toán không phải `150.000 đồng` và sách Ngữ Văn không phải `120.000 đồng`.

Regression gate bao gồm văn bản, ảnh nhiều dòng a–d, provider trả generic/thiếu
quantities và biến thể số liệu sinh tự động. Family này có riêng 160 records
train, 24 validation và 24 test ở hai modality text+ảnh.

## Case chuẩn `sequential_fraction_remainder_quantity`

Với đề khu đất `10 dam² 80 m²`, dùng `2/5` toàn bộ làm nhà, tiếp tục dùng `1/3` phần còn lại trồng hoa rồi hỏi diện tích cuối cùng, pipeline hiện:

1. Không còn đọc nhầm `dam²`, `m²` thành `kg`; đổi `10 dam² = 1.000 m²`, cộng `80 m²` thành `1.080 m²`.
2. Phục hồi đủ hai cặp phân số `2/5` và `1/3`, kể cả dạng ảnh/OCR xếp tử và mẫu trên hai dòng.
3. Dùng strategy tổng quát “phân số của phần còn lại” với `bar_model`, không phụ thuộc ngữ cảnh khu đất, gạo, tiền hay số đồ vật.
4. Dựng lần 1: `1.080 × 2/5 = 432 m²`, còn `648 m²`; coi `648 m²` là toàn bộ mới.
5. Dựng lần 2: `648 × 1/3 = 216 m²`; phần cuối `648 − 216 = 432 m²`; kiểm tra `432 + 216 + 432 = 1.080 m²`.

Bản ghi lịch sử sai cũ được migration từ chính `source_text`, gồm cả semantic payload lẫn nhãn tóm tắt bên ngoài. Smoke trình duyệt headless thật trên HTTPS đã mở mục **Gần đây**, chọn lại bản ghi cũ và xác nhận không còn `10 kg`, `80 kg` hay thẻ `unsupported`. Bộ kiểm thử Math Lab liên quan hiện đạt 198 backend tests và toàn bộ frontend suite đạt 520 tests; discovery/autolearning foundation nằm trong gate backend này.

## Ma trận nghiệm thu lớp 1–9 và 19 họ bài mới đóng

Coverage không còn là một con số chép tay. Có hai bộ chạy được:

```bash
# Ma trận nghiệm thu có phiên bản: analyzer + plan cho từng ca
python training/math_lab/benchmarks/build_acceptance_matrix.py
python training/math_lab/benchmarks/run_acceptance_matrix.py

# Mọi họ bài trong bộ sinh dữ liệu có thực sự tới được renderer đúng không
python training/math_lab/benchmarks/run_family_plans.py
```

`run_acceptance_matrix.py` báo cáo theo **lớp, họ bài, phương thức nhập và tầng
lỗi**; một ca chỉ đạt khi vai trò ngữ nghĩa, unknown, renderer, trạng thái plan
và số bước cùng đúng. `run_family_plans.py` nạp từng `ProviderDocument` do bộ
sinh dữ liệu tạo ra, chạy qua analyzer thật, decision engine thật và pedagogy
planner thật, rồi báo họ bài nào rơi vào `unsupported`.

Đợt này đóng toàn bộ 19 họ bài trước đây ở trạng thái `partial` hoặc `missing`:

| Họ bài | Trạng thái cũ | Mô hình trực quan mới |
|---|---|---|
| `column_arithmetic_regrouping` | partial | nhân nhiều chữ số theo tích riêng, chia dài hạ từng chữ số |
| `decimal_arithmetic` | partial | nhân/chia thập phân qua bước dịch dấu phẩy |
| `time_calendar_duration` | missing | `calendar` — đếm trên lưới tháng, thấy ranh giới sang tháng |
| `multi_step_arithmetic_word` | missing | một đại lượng chạy qua hai phép tính, giữ giá trị trung gian |
| `ratio_total_parts` | partial | tách tổng thành hai thanh phần bằng nhau |
| `map_scale` | missing | hai thước bản đồ – thực tế đọc cùng một quãng đường |
| `arithmetic_mean` | missing | san bằng số cột bất kỳ về mức trung bình |
| `divisibility_common_multiple` | missing | `factor_lattice` — hai tập bội và phần giao |
| `circle_area` | missing | `circle_model` — cắt hình quạt, xếp lại thành hình chữ nhật |
| `mixed_rational_arithmetic_percent` | partial | `expression_tree` — rút gọn theo thứ tự ưu tiên |
| `discount_tax_percentage` | partial | chuỗi giá: thuế tính trên giá đã giảm |
| `proportional_system_two_variables` | missing | hai thanh tỉ lệ, hiệu là số phần dôi ra |
| `multi_segment_equal_distance_motion` | partial | từng chặng có thời gian riêng, vận tốc trung bình không phải trung bình hai vận tốc |
| `algebraic_expression_modeling` | missing | mỗi cụm từ thành đúng một hạng tử tile |
| `triangle_congruence_centroid_proof` | missing | trung tuyến chia tại trọng tâm, đo được tỉ số 2 : 1 |
| `compound_linear_equation` | partial | cân kèm bước phá ngoặc và thu gọn |
| `word_equation_rectangle` | partial | hình chữ nhật và phương trình đổi cùng nhau |
| `triangle_similarity_metric_relation` | partial | hai tam giác, cạnh tương ứng và một tỉ số |
| `circle_tangent_cyclic_proof` | missing | tiếp tuyến vuông góc bán kính, góc nội tiếp bằng nửa góc ở tâm |

Số liệu coverage phải lấy lại bằng `build_coverage_docs.py` sau mỗi lần đổi
catalog; đừng chép con số trong tài liệu này vào một tuyên bố hoàn thành.

## Góp ý giáo viên và học tăng cường

Phiên bản hiện tại đã có nút **Góp ý cải thiện AI** sau mô phỏng. Góp ý, đánh giá, correction kỳ vọng, semantic model và scene được lưu ở PostgreSQL với trạng thái `pending_review`; lịch sử 5 bài gần nhất nằm trong Redis, bài mới thứ sáu tự loại bài cũ nhất. Math Lab không yêu cầu giáo viên duyệt semantic trước khi mô phỏng. Smoke adapter 4B vẫn chưa được runtime production nạp.

Đây chưa phải online reinforcement learning/RLHF: phản hồi chưa duyệt không tự cập nhật trọng số model đang chạy.

Luồng an toàn cần triển khai là: `Góp ý sau mô phỏng → lưu input/model/scene/correction/rating có phiên bản → ẩn dữ liệu cá nhân → giáo viên hoặc quản trị viên duyệt → tạo dataset version bất biến → QLoRA SFT/DPO offline → chạy holdout và quality gate → canary adapter → rollback nếu giảm chất lượng`. Không cập nhật trọng số ngay sau mỗi lần bấm vì một góp ý sai có thể làm hỏng model cho mọi giáo viên.

## Case chuẩn `(-2/5)^3`

Ảnh kiểm thử: `Câu 9: Kết quả (−2/5)³ là`, với bốn phương án A–D.

Pipeline đã kiểm chứng qua HTTPS:

1. Đọc đúng `problem_type=fraction_power`, `numerator=-2`, `denominator=5`, `exponent=3`.
2. Chọn duy nhất `power_model`, không còn chọn `balance` theo domain đại số chung chung.
3. Viết phép nhân lặp `(−2/5) × (−2/5) × (−2/5)`.
4. Tách dấu: ba thừa số âm là số lẻ nên tích âm.
5. Tính riêng `2³ = 8` và `5³ = 125`.
6. Dựng năm lớp 5×5; tám ô tô tạo đúng khối con 2×2×2 trong khối 5×5×5.
7. Ghép dấu với độ lớn, kết luận `−8/125` và đối chiếu **Chọn C**.

Ảnh chụp E2E thật: [fraction-power-e2e.png](evidence/fraction-power-e2e.png).

## Claude Code mission và skill

Skill cấp dự án nằm tại
[`../../.claude/skills/math-lab-grade-1-9/SKILL.md`](../../.claude/skills/math-lab-grade-1-9/SKILL.md).
Nó khóa phạm vi chỉ Math Lab, buộc chạy coverage lớp 1–9, kiểm chứng browser
8443 và phân biệt checkpoint smoke với fine-tune production thật. Master prompt
để dán trực tiếp vào Claude Code nằm tại
[`CLAUDE_CODE_MASTER_PROMPT.md`](CLAUDE_CODE_MASTER_PROMPT.md).

## Fine-tune đang nhắm vào gì?

Fine-tune chỉ nhắm vào **semantic analyzer**, không train renderer. Target model production là `Qwen/Qwen3-VL-8B-Instruct` với QLoRA:

- 4-bit NF4, double quantization, compute `bfloat16`;
- LoRA `r=8`, `alpha=16`, target `q_proj/k_proj/v_proj/o_proj` theo framework Qwen3-VL chính thức;
- vision tower đóng băng ở adapter semantic đầu tiên;
- dữ liệu VLM dạng `prompt + completion`, chỉ tính loss trên completion JSON;
- `max_length=null` để không cắt mất image tokens;
- checkpoint có thể resume, kèm processor và metrics.

Nguồn cấu hình được khóa trong [`training/math_lab/sources.lock.json`](../../training/math_lab/sources.lock.json): Qwen3-VL commit `9658872`, TRL `8bbf121`, PEFT `02d57bf`. Hướng dẫn chính thức của TRL yêu cầu không truncate image tokens; TRL hiện tại không hỗ trợ `assistant_only_loss` cho vision nên pipeline dùng `completion_only_loss` trên prompt-completion.

### Dataset semantic đã tạo và audit

- Generator source hiện có 71 họ bài, gồm text và ảnh cho từng semantic case; họ mới nhất là hệ hai giá niêm yết với hai mức giảm giá khác nhau.
- Với cấu hình mặc định: train 5.680 semantic cases = 11.360 records text+image.
- Validation: 852 cases = 1.704 records.
- Test: 852 cases = 1.704 records.
- Audit hiện tại: schema validity 100%, unknown leakage 0, renderer decision accuracy 100%, không trùng stem giữa ba split.

Catalog coverage hiện đối chiếu 66 họ bài quan sát trong bộ đề/ma trận đại diện và các failure thực tế lớp 1–9; 66/66 có semantic case và renderer chính xác trong baseline hiện hành. Catalog nằm tại [`training/math_lab/catalogs/grade_1_9_exam_families.json`](../../training/math_lab/catalogs/grade_1_9_exam_families.json). Con số coverage phải được lấy lại bằng `audit_exam_coverage.py` sau mỗi lần sinh manifest; đây không phải danh mục toàn bộ đề trên toàn quốc.

### Discovery mở và coverage trung thực

Pipeline discovery hiện có `discover_sources.py`, `extract_questions.py`,
`normalize_questions.py`, `classify_families.py`, `cluster_questions.py`,
`discover_new_families.py` và `audit_family_saturation.py`. Fingerprint dựa trên
domain, toán tử, vai trò đại lượng, relationships, unknown, constraints và cấu
trúc chuỗi; tên người, bối cảnh và con số cụ thể không tham gia fingerprint.
Không có exact family thì giữ `UNKNOWN_CLUSTER`, không ép vào family gần nhất.

Source manifest hiện có 10 provenance records phủ lớp 1–9: 6
`TAXONOMY_ONLY`, 4 `METADATA_ONLY`, 0 `TRAIN_ALLOWED`. Do đó không có nội dung
web nào được đưa vào SFT hiện hành. Baseline catalog ngày 28/08/2026 có 66 họ
quan sát và đạt 66 exact sau khi đóng các gap đã ghi nhận. Đây vẫn chưa phải
saturation hay lời khẳng định đã bao phủ mọi đề trên toàn quốc. Xem
[coverage lớp 1–9](GRADE_1_9_COVERAGE.md),
[visual matrix](VISUAL_COVERAGE_MATRIX.md), [data governance](DATA_GOVERNANCE.md)
và [controlled autolearning](AUTOLEARNING.md).

Dữ liệu mạng không được trộn tùy tiện:

- Kaggle `AIMO3 Math Corpus` (Apache-2.0): chỉ làm nguồn gợi ý cấu trúc sau khi con người duyệt, không chép solution vào SFT.
- Kaggle `25K Math Equation` (MIT): chỉ là ứng viên OCR công thức riêng.
- Kaggle `Handwritten Math Symbols`, cập nhật 23/08/2026 (CC0): đã tải bằng `kaggle.json`, checksum khóa trong source lock; chỉ là ứng viên OCR vì nhãn glyph không phải semantic scene.
- LessonBench: chỉ tham khảo chủ đề/sư phạm, không train lại lesson/media.
- We-Math, MathVista, MathNet và VLM curriculum: giữ ngoài train để làm holdout và tránh contamination.
- `kaggle.json`, raw data, generated data, cache và checkpoints đều bị Git ignore; file credential được kiểm tra quyền `0600`.

### Checkpoint đã chạy thật

Máy có RTX 5060 Ti 16 GB nhưng tại thời điểm chạy chỉ còn 10.879 MiB VRAM do tiến trình của tài khoản khác. Gate 8B yêu cầu 12.000 MiB nên đã từ chối an toàn; không tiến trình nào của người khác bị dừng.

Một smoke QLoRA thực tế đã chạy trên `Qwen/Qwen3-VL-4B-Instruct`, đúng một train image và một validation image thuộc `fraction_power`:

- `train_loss=0.247867`, `eval_loss=0.241940`;
- `eval_mean_token_accuracy=0.959119`;
- runtime train 5,33 giây;
- adapter `adapter_model.safetensors` 11.839.096 byte, SHA-256 `427afed14d9033d1e878d5105d6bd1bd074ba5e9dc536c1fd62d2087f225236f`;
- checkpoint, optimizer, processor và `all_results.json` đã được xuất tại `training/math_lab/checkpoints/qwen3vl-4b-fraction-power-smoke/` (local, Git ignored).

Đây là **smoke checkpoint xác nhận pipeline**, không phải model đã hội tụ và chưa được đưa vào production. Chỉ thay runtime 8B sau khi train đủ dữ liệu và đạt quality gate dưới đây.

## Lệnh tái tạo

```bash
python training/math_lab/scripts/prepare_sft.py
python training/math_lab/scripts/audit_sft.py
python training/math_lab/scripts/audit_exam_coverage.py
python training/math_lab/discovery/discover_sources.py
python training/math_lab/scripts/build_dataset_version.py
python training/math_lab/scripts/build_coverage_docs.py

python -m venv --system-site-packages training/math_lab/.venv
training/math_lab/.venv/bin/pip install -r training/math_lab/requirements-qlora.txt

# Kiểm tra dữ liệu và VRAM cho target 8B, chưa nạp model
training/math_lab/.venv/bin/python training/math_lab/scripts/train_qlora.py --dry-run

# Smoke có giới hạn; không dùng kết quả này làm production
training/math_lab/.venv/bin/python training/math_lab/scripts/train_qlora.py \
  --model Qwen/Qwen3-VL-4B-Instruct \
  --output-dir training/math_lab/checkpoints/qwen3vl-4b-fraction-power-smoke \
  --family fraction_power --min-free-vram-mib 8000 \
  --max-steps 1 --train-samples 1 --eval-samples 1 \
  --gradient-accumulation-steps 1 --save-steps 1 --eval-steps 1
```

## Quality gate trước production

Adapter 8B chỉ được chấp nhận khi:

- 100% JSON parse và Pydantic schema validity;
- unknown-answer leakage bằng 0;
- semantic role accuracy ≥ 99%;
- renderer selection accuracy ≥ 98%;
- eval riêng cho OCR mờ, số mũ, dấu âm, phân số xếp chồng và choices A–D;
- toàn bộ backend/frontend tests, build, Docker health và ảnh E2E qua HTTPS đều đạt;
- so sánh base 8B với adapter trên holdout, không chỉ nhìn train loss.

## Chẩn đoán 502/504 đã gặp

Ảnh toán không phải nguyên nhân của 502/503. Lỗi được tái hiện khi các tiến trình Compose của checkout `/home/khiem/Documents/EduVisionAI` hoàn tất build trễ rồi dừng/thay thế ingress, Master, NATS và Data Storage có tên dùng chung. Vì vậy trình duyệt nhận lần lượt `503 Service Unavailable`, `ERR_CONNECTION_CLOSED` và `ERR_CONNECTION_REFUSED` dù đề đầu vào hợp lệ.

Phiên demo Math Lab dùng [`docker-compose.demo.yml`](docker-compose.demo.yml) với project, image, container, network và volume riêng. Nó chiếm cả `127.0.0.1:8443` lẫn `[::1]:8443`, nên `https://localhost:8443` không còn phụ thuộc checkout khác. Các volume được đánh dấu external để `docker compose down -v` không xóa tài khoản, lịch sử hay feedback. Các service lâu dài dùng `restart: always`: sau sự cố Docker daemon ngày 28/08/2026, chính sách này được áp dụng cả trong Compose lẫn container đang chạy để cổng 8443 tự trở lại khi Docker khởi động. Lệnh khởi động duy nhất từ thư mục gốc dự án:

```bash
./docs/math-lab/start-demo.sh
```

Lệnh này fail closed nếu volume bảo vệ bị mất thay vì âm thầm tạo database rỗng. Chỉ với máy cài mới hoàn toàn mới chạy `./docs/math-lab/start-demo.sh --bootstrap` một lần.

JetStream còn một snapshot `user_state` có field `client_devices` do checkout khác ghi nhưng schema backend hiện tại chưa nhận. Để không sửa ngoài phạm vi Math Lab và không xóa state, phiên demo hiện chạy Master với `NATS_ENABLED=false`; Data Storage và lịch sử/góp ý Math Lab vẫn hoạt động. Compose mặc định vẫn bật NATS cho lần chạy bình thường sau khi hai schema user-state được hợp nhất.

Sau sửa, `https://127.0.0.1:8443`, `https://localhost:8443` và `/health/ready` đều trả HTTP 200. Bundle hiện hành là `index-Ckj6nzMy.js`; shell HTML đặt `no-cache`, còn bundle có hash được cache bất biến. API văn bản đọc `2 nhân 4 bằng mấy?` thành hai quantity `2`, `4` và renderer `grouping`. API ảnh thật đọc đúng `(-2/5)^3`, đủ bốn đáp án, chọn `power_model` và lập sáu bước. Nếu một tab đã mở từ trước vẫn chạy bundle cũ, tải lại mạnh một lần để tab nhận shell mới.
