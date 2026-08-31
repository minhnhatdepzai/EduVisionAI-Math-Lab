from __future__ import annotations

from app.schemas.math_lab import (
    MathQuantityRole,
    MathSemanticModel,
    PedagogyPlan,
    PedagogyRevealStep,
    VisualizationDecision,
)


def _plane_passes_through_origin(model: MathSemanticModel) -> bool:
    """True when ``ax + by + cz = 0``, so every axis intercept is O itself.

    ``3x + y = z`` canonicalizes to ``3x + y - z = 0``. Claiming three separate
    axis intercepts there would be false: they all collapse onto the origin.
    """

    constants = [
        quantity.value
        for quantity in model.quantities
        if quantity.role == MathQuantityRole.CONSTANT and quantity.value is not None
    ]
    return bool(constants) and abs(float(constants[0])) <= 1e-9


class PedagogyPlanner:
    def plan(
        self,
        model: MathSemanticModel,
        decisions: list[VisualizationDecision],
    ) -> PedagogyPlan:
        if not decisions:
            raise ValueError("Pedagogy planning requires at least one visualization")
        primary = decisions[0].visualization
        supporting = [item.visualization for item in decisions[1:]]
        if model.grade <= 2:
            band, level = "1-2", "concrete"
            explanation = "Bắt đầu bằng vật thể và một thay đổi nhìn thấy được, sau đó mới gọi tên phép toán."
            interactions = ["tap", "group", "reset"]
        elif model.grade <= 4:
            band, level = "3-4", "model"
            explanation = "Dùng mô hình trực quan theo từng bước rồi nối mô hình với số và đơn vị."
            interactions = ["next", "previous", "play", "reset"]
        elif model.grade <= 6:
            band, level = "5-6", "model"
            explanation = "Đặt sơ đồ và công thức cạnh nhau để mỗi ký hiệu có một ý nghĩa trực quan."
            interactions = ["next", "previous", "play", "pause", "set_value", "reset"]
        else:
            band, level = "7-9", "dynamic"
            explanation = "Liên kết mô hình, quan hệ đại số và đồ thị; cho phép thay đổi giá trị có giới hạn."
            interactions = ["next", "previous", "play", "pause", "what_if", "why", "reset"]
        reveal_steps = [
            PedagogyRevealStep(
                id="observe",
                title="Quan sát dữ kiện",
                goal="Nhận biết các đại lượng và quan hệ đã cho.",
                visualization_ids=[primary],
            ),
            PedagogyRevealStep(
                id="connect",
                title="Kết nối biểu diễn",
                goal="Theo dõi cùng một trạng thái toán học trên các biểu diễn liên quan.",
                visualization_ids=[primary, *supporting],
            ),
            PedagogyRevealStep(
                id="reason",
                title="Giải thích quan hệ",
                goal="Nêu quy tắc hoặc công thức sau khi mô hình đã rõ.",
                visualization_ids=[primary, *supporting],
            ),
        ]
        problem = model.problem_type.lower()
        if primary.value == "unsupported":
            reveal_steps = [
                PedagogyRevealStep(
                    id="unsupported_review",
                    title="Chưa có mô phỏng phù hợp",
                    goal="Giữ nguyên đề và dữ kiện để giáo viên kiểm tra; không thay bằng một hình minh họa sai nghĩa.",
                    visualization_ids=[primary],
                )
            ]
        elif primary.value == "number_compare":
            reveal_steps = [
                PedagogyRevealStep(id="number_values", title="Đọc các số", goal="Giữ nguyên mọi chữ số và giá trị hàng trước khi so sánh.", visualization_ids=[primary]),
                PedagogyRevealStep(id="number_markers", title="Đặt lên tia số", goal="Mỗi số có một mốc riêng trên cùng một thang đo.", visualization_ids=[primary]),
                PedagogyRevealStep(id="number_distance", title="So sánh khoảng cách", goal="Đọc trái-phải để sắp xếp hoặc so khoảng cách tới hai mốc làm tròn.", visualization_ids=[primary]),
                PedagogyRevealStep(id="number_conclusion", title="Kết luận", goal="Viết thứ tự hoặc số đã làm tròn từ vị trí nhìn thấy được.", visualization_ids=[primary]),
            ]
        elif primary.value == "probability_simulator":
            reveal_steps = [
                PedagogyRevealStep(id="probability_trials", title="Xác định phép thử", goal="Đếm tổng số lần thực hiện phép thử.", visualization_ids=[primary]),
                PedagogyRevealStep(id="probability_outcomes", title="Chạy lại kết quả", goal="Hiện từng lần biến cố xảy ra hoặc không xảy ra.", visualization_ids=[primary]),
                PedagogyRevealStep(id="probability_frequency", title="Đếm tần số", goal="Cập nhật số lần biến cố xảy ra trên cùng dải phép thử.", visualization_ids=[primary]),
                PedagogyRevealStep(id="probability_ratio", title="Tính xác suất thực nghiệm", goal="Chia tần số của biến cố cho tổng số phép thử.", visualization_ids=[primary]),
            ]
        elif "multi_item_reverse_discount" in problem:
            reveal_steps = [
                PedagogyRevealStep(id="discount_item_one", title="Tính tiền món thứ nhất", goal="Tô 70% giá gốc món thứ nhất và đọc số tiền thực trả 87.500 đồng.", visualization_ids=[primary]),
                PedagogyRevealStep(id="discount_item_two", title="Tính tiền món thứ hai", goal="Tô 85% giá gốc món thứ hai và đọc số tiền thực trả 255.000 đồng.", visualization_ids=[primary]),
                PedagogyRevealStep(id="discount_known_total", title="Cộng hai khoản đã biết", goal="Đặt hai khoản 87.500 và 255.000 vào cùng hóa đơn.", visualization_ids=[primary]),
                PedagogyRevealStep(id="discount_third_paid", title="Tìm tiền đã trả cho món thứ ba", goal="Lấy tổng hóa đơn trừ hai khoản đã biết để được 350.000 đồng.", visualization_ids=[primary]),
                PedagogyRevealStep(id="discount_third_rate", title="Nhìn phần còn lại sau giảm", goal="Giảm 12,5% nghĩa là 350.000 đồng đang biểu diễn 87,5% giá gốc.", visualization_ids=[primary]),
                PedagogyRevealStep(id="discount_original", title="Suy ngược giá gốc", goal="Chia 350.000 cho 87,5% để khôi phục toàn bộ 100% là 400.000 đồng.", visualization_ids=[primary]),
            ]
        elif "two_item_discount_system" in problem:
            reveal_steps = [
                PedagogyRevealStep(id="discount_variables", title="Đặt hai giá chưa biết", goal="Gọi giá sách Toán là x, giá sách Ngữ Văn là y và giữ điều kiện x > 0, y > 0.", visualization_ids=[primary]),
                PedagogyRevealStep(id="discount_list_equation", title="Dựng tổng giá niêm yết", goal="Ghép hai thanh giá gốc để lập phương trình x + y bằng tổng niêm yết.", visualization_ids=[primary]),
                PedagogyRevealStep(id="discount_paid_equation", title="Tô phần thực trả", goal="Bỏ phần giảm giá trên từng thanh để lập phương trình từ hai phần trăm còn lại.", visualization_ids=[primary]),
                PedagogyRevealStep(id="discount_eliminate", title="Khử một ẩn", goal="Nhân phương trình tổng với tỉ lệ giữ lại nhỏ hơn rồi trừ để chỉ còn một ẩn.", visualization_ids=[primary]),
                PedagogyRevealStep(id="discount_prices", title="Tìm hai giá niêm yết", goal="Tìm giá thứ nhất rồi lấy tổng trừ đi để tìm giá thứ hai.", visualization_ids=[primary]),
                PedagogyRevealStep(id="discount_verify", title="Thay lại và kiểm tra", goal="Tính tiền thực trả của từng sách, cộng lại và đối chiếu từng khẳng định trong đề.", visualization_ids=[primary]),
            ]
        elif primary.value == "percent_grid":
            reveal_steps = [
                PedagogyRevealStep(id="percent_whole", title="Xác định toàn bộ", goal="Coi toàn bộ là 100 ô bằng nhau.", visualization_ids=[primary]),
                PedagogyRevealStep(id="percent_part", title="Đặt phần đã biết", goal="Nối số lượng phần với vùng tương ứng trong toàn bộ.", visualization_ids=[primary]),
                PedagogyRevealStep(id="percent_scale", title="Quy về 100", goal="Phóng hoặc thu cùng tỉ lệ để đọc số ô trên 100.", visualization_ids=[primary]),
                PedagogyRevealStep(id="percent_result", title="Kết luận", goal="Đọc đồng thời phân số, số thập phân và phần trăm.", visualization_ids=[primary]),
            ]
        elif primary.value == "algebra_tiles":
            reveal_steps = [
                PedagogyRevealStep(id="tiles_terms", title="Dựng từng hạng tử", goal="Mỗi hệ số trở thành số tile có đúng bậc và dấu.", visualization_ids=[primary]),
                PedagogyRevealStep(id="tiles_degree", title="Xếp theo bậc", goal="Đặt x², x và đơn vị vào các cột riêng.", visualization_ids=[primary]),
                PedagogyRevealStep(id="tiles_combine", title="Gộp hạng tử đồng dạng", goal="Chỉ cộng hoặc trừ các tile có cùng hình và cùng bậc.", visualization_ids=[primary]),
                PedagogyRevealStep(id="tiles_result", title="Đọc đa thức kết quả", goal="Chuyển các nhóm tile trở lại biểu thức ký hiệu.", visualization_ids=[primary]),
            ]
        elif primary.value == "part_whole":
            reveal_steps = [
                PedagogyRevealStep(id="part_whole_read", title="Đọc ô trống", goal="Xác định ô trống là một phần hay toàn bộ.", visualization_ids=[primary]),
                PedagogyRevealStep(id="part_whole_build", title="Dựng sơ đồ phần–toàn bộ", goal="Đặt hai phần cạnh nhau dưới cùng một thanh toàn bộ.", visualization_ids=[primary]),
                PedagogyRevealStep(id="part_whole_inverse", title="Chọn phép tính ngược", goal="Nếu thiếu một phần, lấy toàn bộ trừ phần đã biết.", visualization_ids=[primary]),
                PedagogyRevealStep(id="part_whole_result", title="Điền ô trống", goal="Đối chiếu kết quả với cả sơ đồ và phép tính ban đầu.", visualization_ids=[primary]),
            ]
        elif primary.value == "shape_pattern":
            reveal_steps = [
                PedagogyRevealStep(id="shape_outline", title="Tách từng hình", goal="Khoanh biên và đánh số từng hình để không đếm trùng.", visualization_ids=[primary]),
                PedagogyRevealStep(id="shape_classify", title="Phân loại", goal="Ghép các hình cùng loại và đọc số lượng từng nhóm.", visualization_ids=[primary]),
                PedagogyRevealStep(id="shape_cycle", title="Tìm chu kỳ", goal="Đánh dấu nhóm hình nhỏ nhất được lặp lại.", visualization_ids=[primary]),
                PedagogyRevealStep(id="shape_next", title="Kết luận", goal="Đọc số lượng hoặc phần tử tiếp theo từ overlay đã kiểm tra.", visualization_ids=[primary]),
            ]
        elif primary.value == "place_value":
            reveal_steps = [
                PedagogyRevealStep(id="place_read", title="Đọc số", goal="Đặt mỗi chữ số vào đúng cột giá trị hàng.", visualization_ids=[primary]),
                PedagogyRevealStep(id="place_expand", title="Tách theo hàng", goal="Nối chữ số với số đơn vị mà chữ số đó đại diện.", visualization_ids=[primary]),
                PedagogyRevealStep(id="place_blocks", title="Dựng khối cơ số 10", goal="Đối chiếu dạng số với nghìn, trăm, chục, đơn vị và phần thập phân.", visualization_ids=[primary]),
                PedagogyRevealStep(id="place_conclude", title="Kết luận", goal="Đọc lại số từ tổng các giá trị hàng.", visualization_ids=[primary]),
            ]
        elif primary.value == "column_algorithm":
            reveal_steps = [
                PedagogyRevealStep(id="column_align", title="Đặt thẳng cột", goal="Căn các chữ số theo cùng giá trị hàng và căn dấu thập phân.", visualization_ids=[primary]),
                PedagogyRevealStep(id="column_units", title="Tính từ phải sang trái", goal="Tính cột nhỏ nhất trước.", visualization_ids=[primary]),
                PedagogyRevealStep(id="column_regroup", title="Nhớ hoặc mượn", goal="Cho thấy đơn vị được đổi sang cột liền kề, không giấu bước chuyển hàng.", visualization_ids=[primary]),
                PedagogyRevealStep(id="column_result", title="Đọc kết quả", goal="Ghép các chữ số kết quả đúng theo giá trị hàng.", visualization_ids=[primary]),
            ]
        elif primary.value == "unit_scale":
            reveal_steps = [
                PedagogyRevealStep(id="unit_source", title="Xác định đơn vị ban đầu", goal="Đặt số đo lên đúng bậc của thang đơn vị.", visualization_ids=[primary]),
                PedagogyRevealStep(id="unit_target", title="Xác định đơn vị đích", goal="Đếm số bậc và chiều di chuyển trên thang.", visualization_ids=[primary]),
                PedagogyRevealStep(id="unit_factor", title="Áp dụng hệ số", goal="Mỗi bậc làm dịch dấu thập phân theo hệ số tương ứng.", visualization_ids=[primary]),
                PedagogyRevealStep(id="unit_result", title="Kiểm tra cùng đại lượng", goal="Hai số đo khác cách viết nhưng có cùng giá trị chuẩn.", visualization_ids=[primary]),
            ]
        elif primary.value == "data_chart":
            reveal_steps = [
                PedagogyRevealStep(id="chart_table", title="Đọc bảng dữ liệu", goal="Ghép đúng nhãn với tần số trước khi vẽ.", visualization_ids=[primary]),
                PedagogyRevealStep(id="chart_scale", title="Dựng trục và tỉ lệ", goal="Mọi cột dùng cùng một thang đo bắt đầu từ 0.", visualization_ids=[primary]),
                PedagogyRevealStep(id="chart_bars", title="Dựng từng cột", goal="Chiều cao cột được tính trực tiếp từ tần số.", visualization_ids=[primary]),
                PedagogyRevealStep(id="chart_reason", title="So sánh và kết luận", goal="Đọc cực trị, tổng hoặc xác suất từ cùng dữ liệu gốc.", visualization_ids=[primary]),
            ]
        elif "circle_radius_diameter" in problem:
            reveal_steps = [
                PedagogyRevealStep(id="circle_center", title="Xác định tâm", goal="Đặt tâm O làm mốc chung cho mọi bán kính.", visualization_ids=[primary]),
                PedagogyRevealStep(id="circle_radius", title="Dựng bán kính", goal="Nối tâm với một điểm trên đường tròn.", visualization_ids=[primary]),
                PedagogyRevealStep(id="circle_diameter", title="Dựng đường kính", goal="Kéo dài bán kính qua tâm đến phía đối diện.", visualization_ids=[primary]),
                PedagogyRevealStep(id="circle_relation", title="Kết luận", goal="Nhìn thấy đường kính gồm đúng hai bán kính thẳng hàng.", visualization_ids=[primary]),
            ]
        elif "rhombus_area_properties" in problem or "parallelogram_area_properties" in problem:
            reveal_steps = [
                PedagogyRevealStep(id="quad_build", title="Dựng tứ giác", goal="Dựng đáy, cạnh bên và các cặp cạnh song song.", visualization_ids=[primary]),
                PedagogyRevealStep(id="quad_height", title="Hạ đường cao", goal="Phân biệt chiều cao vuông góc với cạnh bên nghiêng.", visualization_ids=[primary]),
                PedagogyRevealStep(id="quad_rearrange", title="Cắt và ghép", goal="Chuyển tam giác ở một đầu sang đầu kia để tạo hình chữ nhật.", visualization_ids=[primary]),
                PedagogyRevealStep(id="quad_area", title="Kết luận diện tích", goal="Đọc diện tích bằng đáy nhân chiều cao từ hình chữ nhật tương ứng.", visualization_ids=[primary]),
            ]
        elif "angle_bisector" in problem:
            reveal_steps = [
                PedagogyRevealStep(id="angle_rays", title="Dựng góc đã cho", goal="Dựng hai tia Ox và Oy với đúng số đo góc xOy.", visualization_ids=[primary]),
                PedagogyRevealStep(id="angle_measure", title="Đánh dấu toàn góc", goal="Giữ nguyên số đo góc ban đầu là dữ kiện của đề.", visualization_ids=[primary]),
                PedagogyRevealStep(id="angle_bisector", title="Dựng tia phân giác", goal="Đặt tia Ot ở giữa để hai góc xOt và tOy bằng nhau.", visualization_ids=[primary]),
                PedagogyRevealStep(id="angle_half", title="Tính mỗi nửa", goal="Chia số đo toàn góc cho 2 và kiểm tra hai cung góc bằng nhau.", visualization_ids=[primary]),
            ]
        elif "ray_segment_midpoint" in problem:
            reveal_steps = [
                PedagogyRevealStep(id="segment_points", title="Đặt hai đầu mút", goal="Đoạn thẳng AB có hai đầu mút xác định.", visualization_ids=[primary]),
                PedagogyRevealStep(id="segment_ray", title="Phân biệt tia", goal="Tia AB bắt đầu tại A và kéo dài qua B theo một hướng.", visualization_ids=[primary]),
                PedagogyRevealStep(id="segment_midpoint", title="Đặt trung điểm", goal="Đặt M trên AB sao cho AM và MB bằng nhau.", visualization_ids=[primary]),
                PedagogyRevealStep(id="segment_measure", title="Kiểm tra độ dài", goal="Mỗi nửa có độ dài bằng một nửa đoạn AB.", visualization_ids=[primary]),
            ]
        elif any(token in problem for token in ("fraction_power", "power_of_fraction", "fraction_exponent")):
            reveal_steps = [
                PedagogyRevealStep(
                    id="power_read",
                    title="Đọc cơ số và số mũ",
                    goal="Nhận ra toàn bộ phân số âm là cơ số và 3 là số lần nhân lặp lại.",
                    visualization_ids=[primary],
                ),
                PedagogyRevealStep(
                    id="power_repeat",
                    title="Viết phép nhân lặp",
                    goal="Viết ba thừa số giống nhau: (−2/5) × (−2/5) × (−2/5).",
                    visualization_ids=[primary],
                ),
                PedagogyRevealStep(
                    id="power_sign",
                    title="Xác định dấu",
                    goal="Ba thừa số âm là số lẻ nên tích mang dấu âm.",
                    visualization_ids=[primary],
                ),
                PedagogyRevealStep(
                    id="power_parts",
                    title="Tính tử và mẫu",
                    goal="Tính riêng 2³ = 8 và 5³ = 125 để không làm mất cấu trúc phân số.",
                    visualization_ids=[primary],
                ),
                PedagogyRevealStep(
                    id="power_magnitude",
                    title="Nhìn thấy độ lớn",
                    goal="Xem 8 ô được tô trong khối 5 × 5 × 5 gồm 125 ô bằng nhau.",
                    visualization_ids=[primary],
                ),
                PedagogyRevealStep(
                    id="power_result",
                    title="Kết luận",
                    goal="Ghép dấu âm với độ lớn 8/125 và đối chiếu phương án C.",
                    visualization_ids=[primary],
                ),
            ]
        elif "parenthesized_" in problem and "_multiplication" in problem:
            reveal_steps = [
                PedagogyRevealStep(
                    id="parentheses_read",
                    title="Đọc thứ tự thực hiện",
                    goal="Khoanh phép tính trong ngoặc và giữ phép nhân bên ngoài chờ xử lý.",
                    visualization_ids=[primary],
                ),
                PedagogyRevealStep(
                    id="parentheses_solve",
                    title="Tính trong ngoặc trước",
                    goal="Ghép hoặc bớt các đồ vật trong ngoặc để tìm giá trị của một thừa số.",
                    visualization_ids=[primary],
                ),
                PedagogyRevealStep(
                    id="parentheses_groups",
                    title="Dựng các nhóm bằng nhau",
                    goal="Dùng giá trị trong ngoặc và thừa số còn lại để dựng mảng phép nhân.",
                    visualization_ids=[primary],
                ),
                PedagogyRevealStep(
                    id="parentheses_result",
                    title="Đếm và kết luận",
                    goal="Đếm toàn bộ đồ vật rồi nối mô hình với kết quả biểu thức.",
                    visualization_ids=[primary],
                ),
            ]
        elif "distance_time_direct_proportion" in problem:
            reveal_steps = [
                PedagogyRevealStep(
                    id="motion_known_pair",
                    title="Dựng quãng đường đã biết",
                    goal="Chia quãng đường đã biết thành các phần thời gian bằng nhau.",
                    visualization_ids=[primary],
                ),
                PedagogyRevealStep(
                    id="motion_unit_rate",
                    title="Tìm quãng đường trong 1 đơn vị thời gian",
                    goal="Lấy quãng đường đã biết chia cho thời gian tương ứng.",
                    visualization_ids=[primary],
                ),
                PedagogyRevealStep(
                    id="motion_target_blocks",
                    title="Dựng thời gian mới",
                    goal="Xếp đúng số phần thời gian mới, mỗi phần giữ nguyên quãng đường đơn vị.",
                    visualization_ids=[primary],
                ),
                PedagogyRevealStep(
                    id="motion_target_distance",
                    title="Tính quãng đường mới",
                    goal="Nhân quãng đường trong một đơn vị thời gian với thời gian mới.",
                    visualization_ids=[primary],
                ),
                PedagogyRevealStep(
                    id="motion_ratio_check",
                    title="Kiểm tra tỉ lệ thuận",
                    goal="Đối chiếu để quãng đường trên mỗi đơn vị thời gian không đổi.",
                    visualization_ids=[primary],
                ),
            ]
        elif "work_rate_with_variable_people" in problem:
            reveal_steps = [
                PedagogyRevealStep(
                    id="work_initial_plan",
                    title="Dựng kế hoạch ban đầu",
                    goal="Xếp số người ban đầu theo số ngày dự định để biểu diễn toàn bộ công việc.",
                    visualization_ids=[primary],
                ),
                PedagogyRevealStep(
                    id="work_total_invariant",
                    title="Tính khối lượng công việc",
                    goal="Đếm toàn bộ ô công-ngày: số người nhân số ngày.",
                    visualization_ids=[primary],
                ),
                PedagogyRevealStep(
                    id="work_new_team",
                    title="Cập nhật số người",
                    goal="Cộng hoặc bớt đúng số người để có quy mô tổ mới.",
                    visualization_ids=[primary],
                ),
                PedagogyRevealStep(
                    id="work_redistribute",
                    title="Xếp lại cùng một công việc",
                    goal="Giữ nguyên số ô công-ngày và chia đều chúng cho tổ mới.",
                    visualization_ids=[primary],
                ),
                PedagogyRevealStep(
                    id="work_result",
                    title="Đọc số ngày mới",
                    goal="Lấy tổng công-ngày chia cho số người mới và kiểm tra tích không đổi.",
                    visualization_ids=[primary],
                ),
            ]
        elif "sequential_fraction_remainder_quantity" in problem:
            reveal_steps = [
                PedagogyRevealStep(
                    id="remainder_normalize_total",
                    title="Đổi về cùng đơn vị và ghép tổng",
                    goal="Đưa các thành phần của đại lượng ban đầu về cùng đơn vị rồi cộng thành toàn bộ.",
                    visualization_ids=[primary],
                ),
                PedagogyRevealStep(
                    id="remainder_first_allocation",
                    title="Lấy phân số lần thứ nhất",
                    goal="Chia toàn bộ theo mẫu số thứ nhất và tô đúng số phần đã sử dụng.",
                    visualization_ids=[primary],
                ),
                PedagogyRevealStep(
                    id="remainder_new_whole",
                    title="Coi phần còn lại là toàn bộ mới",
                    goal="Giữ riêng phần còn lại sau lần thứ nhất và chia lại theo mẫu số thứ hai.",
                    visualization_ids=[primary],
                ),
                PedagogyRevealStep(
                    id="remainder_second_allocation",
                    title="Lấy phân số của phần còn lại",
                    goal="Tô phân số dùng lần thứ hai trên toàn bộ mới, không lấy trên tổng ban đầu.",
                    visualization_ids=[primary],
                ),
                PedagogyRevealStep(
                    id="remainder_final_quantity",
                    title="Đọc phần cuối cùng",
                    goal="Đọc lượng chưa tô còn lại và kiểm tra tổng ba phần bằng đại lượng ban đầu.",
                    visualization_ids=[primary],
                ),
            ]
        elif "sequential_fraction_remainder_ratio" in problem:
            reveal_steps = [
                PedagogyRevealStep(
                    id="rice_total_parts",
                    title="Chia toàn bộ thành phần bằng nhau",
                    goal="Đặt toàn bộ lượng gạo ban đầu vào đúng số phần của phân số ngày thứ nhất.",
                    visualization_ids=[primary],
                ),
                PedagogyRevealStep(
                    id="rice_day_one",
                    title="Tách lượng bán ngày thứ nhất",
                    goal="Tô số phần bán ngày thứ nhất và đọc lượng gạo còn lại.",
                    visualization_ids=[primary],
                ),
                PedagogyRevealStep(
                    id="rice_repartition_remainder",
                    title="Chia lại phần còn lại",
                    goal="Coi lượng gạo còn sau ngày thứ nhất là một toàn bộ mới và chia theo mẫu số ngày thứ hai.",
                    visualization_ids=[primary],
                ),
                PedagogyRevealStep(
                    id="rice_day_two_three",
                    title="Tách ngày thứ hai và ngày thứ ba",
                    goal="Lấy đúng phân số của phần còn lại cho ngày thứ hai; phần cuối là ngày thứ ba.",
                    visualization_ids=[primary],
                ),
                PedagogyRevealStep(
                    id="rice_ratio_reduce",
                    title="So sánh và rút gọn tỉ số",
                    goal="Đặt hai lượng ngày thứ ba và ngày thứ nhất cạnh nhau rồi chia cả hai cho cùng ước chung.",
                    visualization_ids=[primary],
                ),
            ]
        elif any(token in problem for token in ("average", "trung_binh", "mean")):
            reveal_steps = [
                PedagogyRevealStep(
                    id="month_1",
                    title="Mốc tháng thứ nhất",
                    goal="Ghi sản lượng tháng thứ nhất trên dòng thời gian.",
                    visualization_ids=[primary],
                ),
                PedagogyRevealStep(
                    id="month_2",
                    title="Mốc tháng thứ hai",
                    goal="Cộng sản lượng tháng thứ hai vào tổng đang có.",
                    visualization_ids=[primary],
                ),
                PedagogyRevealStep(
                    id="month_3",
                    title="Mốc tháng thứ ba",
                    goal="Cộng sản lượng tháng thứ ba để có tổng ba tháng.",
                    visualization_ids=[primary],
                ),
                PedagogyRevealStep(
                    id="equal_groups",
                    title="Chia theo số công nhân",
                    goal="Chia tổng sản phẩm thành các phần bằng nhau theo số công nhân.",
                    visualization_ids=[primary],
                ),
                PedagogyRevealStep(
                    id="average_result",
                    title="Kết luận trung bình",
                    goal="Đọc số sản phẩm trong mỗi phần bằng nhau.",
                    visualization_ids=[primary],
                ),
            ]
        elif "ratio_total_parts" in problem:
            reveal_steps = [
                PedagogyRevealStep(id="ratio_total_parts", title="Đếm tổng số phần", goal="Cộng số phần của hai đại lượng trong tỉ số.", visualization_ids=[primary]),
                PedagogyRevealStep(id="ratio_total_map", title="Đặt tổng vào sơ đồ", goal="Nối tổng đã biết với toàn bộ các phần bằng nhau.", visualization_ids=[primary]),
                PedagogyRevealStep(id="ratio_total_one", title="Tìm một phần", goal="Chia tổng cho tổng số phần.", visualization_ids=[primary]),
                PedagogyRevealStep(id="ratio_total_values", title="Tìm hai đại lượng", goal="Nhân một phần với số phần tương ứng của từng đại lượng.", visualization_ids=[primary]),
            ]
        elif "ratio" in problem:
            reveal_steps = [
                PedagogyRevealStep(
                    id="known_parts",
                    title="Đặt đại lượng đã biết vào sơ đồ",
                    goal="Biểu diễn số đã biết bằng số phần ở mẫu của tỉ số.",
                    visualization_ids=[primary],
                ),
                PedagogyRevealStep(
                    id="one_part",
                    title="Tìm giá trị một phần",
                    goal="Chia đại lượng đã biết cho số phần tương ứng.",
                    visualization_ids=[primary],
                ),
                PedagogyRevealStep(
                    id="target_parts",
                    title="Dựng đại lượng cần tìm",
                    goal="Dùng giá trị một phần để dựng đủ số phần ở tử của tỉ số.",
                    visualization_ids=[primary],
                ),
                PedagogyRevealStep(
                    id="ratio_result",
                    title="Kết luận",
                    goal="Nhân số phần cần tìm với giá trị của một phần.",
                    visualization_ids=[primary],
                ),
            ]
        elif model.domain.value == "fraction" and any(
            token in problem for token in ("addition", "subtraction", "add", "subtract")
        ):
            reveal_steps = [
                PedagogyRevealStep(
                    id="fraction_read",
                    title="Đọc hai phân số",
                    goal="Nhận ra mỗi mẫu số đang chia đơn vị thành các phần có kích thước khác nhau.",
                    visualization_ids=[primary],
                ),
                PedagogyRevealStep(
                    id="fraction_common_parts",
                    title="Tạo phần bằng nhau",
                    goal="Chia lại hai mô hình theo mẫu số chung nhỏ nhất mà không đổi lượng đã tô.",
                    visualization_ids=[primary],
                ),
                PedagogyRevealStep(
                    id="fraction_rewrite",
                    title="Quy đồng",
                    goal="Nối phép nhân tử và mẫu với số phần mới trên từng thanh.",
                    visualization_ids=[primary],
                ),
                PedagogyRevealStep(
                    id="fraction_combine",
                    title="Ghép các phần cùng cỡ",
                    goal="Cộng hoặc bớt phần đã tô chỉ sau khi mọi phần có cùng kích thước.",
                    visualization_ids=[primary],
                ),
                PedagogyRevealStep(
                    id="fraction_simplify",
                    title="Rút gọn kết quả",
                    goal="Chia cả tử và mẫu cho cùng một ước rồi kết luận.",
                    visualization_ids=[primary],
                ),
            ]
        elif model.domain.value == "fraction" and any(
            token in problem for token in ("multiplication", "multiply", "product")
        ):
            reveal_steps = [
                PedagogyRevealStep(
                    id="fraction_factor_one",
                    title="Tô phân số thứ nhất",
                    goal="Tô số cột tương ứng với phân số thứ nhất.",
                    visualization_ids=[primary],
                ),
                PedagogyRevealStep(
                    id="fraction_factor_two",
                    title="Lấy một phần của phần đã tô",
                    goal="Tô số hàng tương ứng với phân số thứ hai theo hướng vuông góc.",
                    visualization_ids=[primary],
                ),
                PedagogyRevealStep(
                    id="fraction_intersection",
                    title="Đếm phần giao",
                    goal="Phần giao của hai lớp màu biểu diễn tích hai phân số.",
                    visualization_ids=[primary],
                ),
                PedagogyRevealStep(
                    id="fraction_product",
                    title="Viết và rút gọn tích",
                    goal="Đếm ô giao trên tổng số ô và rút gọn.",
                    visualization_ids=[primary],
                ),
            ]
        elif model.domain.value == "fraction" and any(
            token in problem for token in ("division", "divide", "quotient")
        ):
            reveal_steps = [
                PedagogyRevealStep(id="fraction_division_read", title="Đọc phép đo", goal="Xác định lượng có sẵn và cỡ của mỗi nhóm phân số.", visualization_ids=[primary]),
                PedagogyRevealStep(id="fraction_division_common_parts", title="Tạo phần cùng cỡ", goal="Chia hai lượng theo một mẫu chung để đo bằng cùng đơn vị nhỏ.", visualization_ids=[primary]),
                PedagogyRevealStep(id="fraction_division_groups", title="Đếm nhóm", goal="Đếm số nhóm cỡ bằng số chia nằm trong số bị chia.", visualization_ids=[primary]),
                PedagogyRevealStep(id="fraction_division_reciprocal", title="Nối với ký hiệu", goal="Đối chiếu mô hình đo với phép nhân nghịch đảo và rút gọn.", visualization_ids=[primary]),
            ]
        elif model.domain.value in {"arithmetic", "number"} and any(
            token in problem for token in ("multiplication", "division", "group")
        ):
            reveal_steps = [
                PedagogyRevealStep(
                    id="equal_group_setup",
                    title="Dựng nhóm bằng nhau",
                    goal="Đặt đúng số đồ vật vào từng hàng hoặc từng nhóm.",
                    visualization_ids=[primary],
                ),
                PedagogyRevealStep(
                    id="equal_group_count",
                    title="Đếm theo nhóm",
                    goal="Theo dõi tổng tăng theo cùng một số lượng ở mỗi nhóm.",
                    visualization_ids=[primary],
                ),
                PedagogyRevealStep(
                    id="equal_group_result",
                    title="Nối mô hình với phép tính",
                    goal="Đọc số nhóm, số phần tử mỗi nhóm và kết quả.",
                    visualization_ids=[primary],
                ),
            ]
        elif model.domain.value == "algebra" and any(
            token in problem for token in ("expansion", "binomial", "algebraic_identity")
        ):
            reveal_steps = [
                PedagogyRevealStep(id="area_whole", title="Dựng hình vuông", goal="Dựng hình vuông cạnh a + b.", visualization_ids=[primary]),
                PedagogyRevealStep(id="area_split", title="Chia hai cạnh", goal="Chia mỗi cạnh thành đoạn a và đoạn b.", visualization_ids=[primary]),
                PedagogyRevealStep(id="area_terms", title="Đọc bốn miền", goal="Đọc a², ab, ab và b² từ diện tích từng miền.", visualization_ids=[primary]),
                PedagogyRevealStep(id="area_like_terms", title="Gộp hai miền ab", goal="Hai hình chữ nhật ab tạo thành 2ab.", visualization_ids=[primary]),
                PedagogyRevealStep(id="area_identity", title="Kết luận hằng đẳng thức", goal="Tổng bốn miền bằng diện tích toàn hình vuông.", visualization_ids=[primary]),
            ]
        elif "time_calendar_duration" in problem or primary.value == "calendar":
            reveal_steps = [
                PedagogyRevealStep(id="calendar_start", title="Đánh dấu ngày bắt đầu", goal="Tìm ngày bắt đầu trên lịch tháng.", visualization_ids=[primary]),
                PedagogyRevealStep(id="calendar_count", title="Đếm số ngày", goal="Đếm từng ô trên lịch thay vì cộng nhẩm.", visualization_ids=[primary]),
                PedagogyRevealStep(id="calendar_month", title="Kiểm tra ranh giới tháng", goal="Đối chiếu với số ngày thực tế của tháng để biết có sang tháng sau không.", visualization_ids=[primary]),
                PedagogyRevealStep(id="calendar_end", title="Đọc ngày kết thúc", goal="Đọc ngày và thứ ở ô cuối cùng của khoảng thời gian.", visualization_ids=[primary]),
            ]
        elif "fractional_linear_equation" in problem:
            reveal_steps = [
                PedagogyRevealStep(id="fractional_denominators", title="Tìm mẫu số", goal="Liệt kê các mẫu số và tìm bội chung nhỏ nhất.", visualization_ids=[primary]),
                PedagogyRevealStep(id="fractional_clear", title="Khử mẫu", goal="Nhân cả hai vế với bội chung nhỏ nhất để được phương trình tương đương.", visualization_ids=[primary]),
                PedagogyRevealStep(id="fractional_collect", title="Thu gọn", goal="Gộp các hạng tử chứa ẩn và các hằng số.", visualization_ids=[primary]),
                PedagogyRevealStep(id="fractional_solve", title="Cô lập ẩn", goal="Chia hai vế cho hệ số của ẩn và thay lại để kiểm tra.", visualization_ids=[primary]),
            ]
        elif "absolute_value_equation" in problem:
            reveal_steps = [
                PedagogyRevealStep(id="absolute_read", title="Đọc khoảng cách", goal="Giá trị tuyệt đối biểu diễn khoảng cách tới 0 nên luôn không âm.", visualization_ids=[primary]),
                PedagogyRevealStep(id="absolute_split", title="Tách hai trường hợp", goal="Cho biểu thức trong dấu giá trị tuyệt đối lần lượt bằng số dương và số đối của nó.", visualization_ids=[primary]),
                PedagogyRevealStep(id="absolute_solve", title="Giải hai phương trình", goal="Giải từng phương trình bậc nhất vừa nhận được.", visualization_ids=[primary]),
                PedagogyRevealStep(id="absolute_mark", title="Đánh dấu nghiệm", goal="Đặt mọi nghiệm hợp lệ lên trục số và thay lại để kiểm tra.", visualization_ids=[primary]),
            ]
        elif "biquadratic_equation" in problem:
            reveal_steps = [
                PedagogyRevealStep(id="biquadratic_substitute", title="Đặt ẩn phụ", goal="Đặt t = x² và nhớ điều kiện t ≥ 0.", visualization_ids=[primary]),
                PedagogyRevealStep(id="biquadratic_quadratic", title="Giải theo t", goal="Giải phương trình bậc hai theo ẩn t.", visualization_ids=[primary]),
                PedagogyRevealStep(id="biquadratic_filter", title="Lọc t không âm", goal="Loại nghiệm t âm vì không thể bằng x² trong tập số thực.", visualization_ids=[primary]),
                PedagogyRevealStep(id="biquadratic_back", title="Trở lại x", goal="Mỗi t dương tạo hai nghiệm x đối nhau; t = 0 tạo một nghiệm.", visualization_ids=[primary]),
            ]
        elif "radical_equation" in problem:
            reveal_steps = [
                PedagogyRevealStep(id="radical_domain", title="Đặt điều kiện", goal="Biểu thức trong căn và vế còn lại phải không âm.", visualization_ids=[primary]),
                PedagogyRevealStep(id="radical_square", title="Bình phương hai vế", goal="Khử căn bằng một phép biến đổi có thể sinh nghiệm ngoại lai.", visualization_ids=[primary]),
                PedagogyRevealStep(id="radical_candidates", title="Tìm nghiệm ứng viên", goal="Giải phương trình thu được sau khi bình phương.", visualization_ids=[primary]),
                PedagogyRevealStep(id="radical_verify", title="Thử lại đề gốc", goal="Giữ nghiệm thỏa phương trình ban đầu và gạch bỏ nghiệm ngoại lai.", visualization_ids=[primary]),
            ]
        elif "rational_equation" in problem and "domain" not in problem:
            reveal_steps = [
                PedagogyRevealStep(id="rational_domain", title="Điều kiện xác định", goal="Cho mọi mẫu thức khác 0 và đánh dấu các giá trị bị loại.", visualization_ids=[primary]),
                PedagogyRevealStep(id="rational_common", title="Quy đồng, khử mẫu", goal="Nhân hai vế với mẫu thức chung trên miền xác định.", visualization_ids=[primary]),
                PedagogyRevealStep(id="rational_candidates", title="Giải phương trình tử", goal="Tìm các nghiệm ứng viên của phương trình sau khi khử mẫu.", visualization_ids=[primary]),
                PedagogyRevealStep(id="rational_filter", title="Đối chiếu điều kiện", goal="Loại mọi ứng viên làm mẫu bằng 0 rồi viết tập nghiệm.", visualization_ids=[primary]),
            ]
        elif "linear_inequality" in problem:
            reveal_steps = [
                PedagogyRevealStep(id="inequality_collect", title="Chuyển vế", goal="Đưa hạng tử chứa ẩn về một vế, hằng số về vế kia.", visualization_ids=[primary]),
                PedagogyRevealStep(id="inequality_divide", title="Chia hai vế cho hệ số", goal="Chia cho hệ số của ẩn; nếu hệ số âm thì phải đổi chiều bất phương trình.", visualization_ids=[primary]),
                PedagogyRevealStep(id="inequality_mark", title="Đánh dấu điểm biên", goal="Đặt điểm biên lên trục số, tô rỗng khi dấu ngặt và tô đặc khi có dấu bằng.", visualization_ids=[primary]),
                PedagogyRevealStep(id="inequality_shade", title="Tô miền nghiệm", goal="Tô phần trục số chứa mọi giá trị thỏa mãn rồi thử lại một giá trị.", visualization_ids=[primary]),
            ]
        elif "product_equation_roots" in problem:
            reveal_steps = [
                PedagogyRevealStep(id="product_read", title="Đọc hai thừa số", goal="Nhận ra tích hai biểu thức bằng 0.", visualization_ids=[primary]),
                PedagogyRevealStep(id="product_rule", title="Dùng quy tắc tích bằng 0", goal="Tích bằng 0 khi và chỉ khi ít nhất một thừa số bằng 0.", visualization_ids=[primary]),
                PedagogyRevealStep(id="product_roots", title="Giải từng thừa số", goal="Cho lần lượt mỗi thừa số bằng 0 để tìm nghiệm.", visualization_ids=[primary]),
                PedagogyRevealStep(id="product_check", title="Đặt nghiệm lên trục số", goal="Đánh dấu các nghiệm và thay lại vào tích để kiểm tra.", visualization_ids=[primary]),
            ]
        elif "rational_equation_domain" in problem:
            reveal_steps = [
                PedagogyRevealStep(id="domain_denominators", title="Tìm các mẫu thức", goal="Liệt kê mọi mẫu thức có chứa ẩn.", visualization_ids=[primary]),
                PedagogyRevealStep(id="domain_zero", title="Cho từng mẫu bằng 0", goal="Giải từng mẫu thức bằng 0 để tìm giá trị bị loại.", visualization_ids=[primary]),
                PedagogyRevealStep(id="domain_exclude", title="Loại các giá trị đó", goal="Đánh dấu rỗng các điểm bị loại trên trục số.", visualization_ids=[primary]),
                PedagogyRevealStep(id="domain_conclude", title="Viết điều kiện xác định", goal="Điều kiện xác định là mọi giá trị còn lại của ẩn.", visualization_ids=[primary]),
            ]
        elif "angle_of_depression" in problem:
            reveal_steps = [
                PedagogyRevealStep(id="depression_horizontal", title="Kẻ phương ngang qua điểm quan sát", goal="Dựng đường nằm ngang để nhìn đúng góc nghiêng xuống.", visualization_ids=[primary]),
                PedagogyRevealStep(id="depression_parallel", title="Chuyển góc xuống chân công trình", goal="Hai đường ngang song song nên góc nghiêng xuống bằng góc nâng từ con tàu.", visualization_ids=[primary]),
                PedagogyRevealStep(id="depression_ratio", title="Chọn tỉ số tan", goal="Chiều cao là cạnh đối, khoảng cách ngang là cạnh kề.", visualization_ids=[primary]),
                PedagogyRevealStep(id="depression_distance", title="Tính khoảng cách", goal="Lấy chiều cao chia tan của góc rồi làm tròn theo yêu cầu.", visualization_ids=[primary]),
            ]
        elif "oblique_triangle_altitude" in problem:
            reveal_steps = [
                PedagogyRevealStep(id="oblique_split", title="Hạ đường cao", goal="Đường cao chia tam giác thành hai tam giác vuông dùng chung một cạnh.", visualization_ids=[primary]),
                PedagogyRevealStep(id="oblique_left", title="Giải tam giác vuông bên trái", goal="Dùng sin và tan của góc đáy thứ nhất để tìm cạnh bên và đoạn đáy.", visualization_ids=[primary]),
                PedagogyRevealStep(id="oblique_right", title="Giải tam giác vuông bên phải", goal="Làm tương tự với góc đáy thứ hai.", visualization_ids=[primary]),
                PedagogyRevealStep(id="oblique_join", title="Ghép cạnh đáy", goal="Cộng hai đoạn ở chân đường cao để được cạnh đáy toàn tam giác.", visualization_ids=[primary]),
                PedagogyRevealStep(id="oblique_check", title="Kiểm tra", goal="Đối chiếu tổng ba góc và hai tam giác vuông thành phần.", visualization_ids=[primary]),
            ]
        elif "parallelogram_perpendicular_diagonal" in problem:
            reveal_steps = [
                PedagogyRevealStep(id="para_draw", title="Dựng hình bình hành và đường chéo", goal="Ghi đúng cạnh, đường chéo và góc vuông đã cho.", visualization_ids=[primary]),
                PedagogyRevealStep(id="para_triangle", title="Tách tam giác vuông", goal="Đường chéo vuông góc với cạnh tạo tam giác vuông chứa góc đã biết.", visualization_ids=[primary]),
                PedagogyRevealStep(id="para_diagonal", title="Tính đường chéo làm chiều cao", goal="Dùng tan của góc để tìm độ dài đường chéo vuông góc.", visualization_ids=[primary]),
                PedagogyRevealStep(id="para_area", title="Tính diện tích", goal="Nhân cạnh đáy với đường cao vừa tìm và làm tròn.", visualization_ids=[primary]),
            ]
        elif "right_triangle_solution" in problem:
            reveal_steps = [
                PedagogyRevealStep(id="triangle_draw", title="Dựng tam giác vuông", goal="Dựng tam giác theo hai cạnh đã cho và đánh dấu góc vuông.", visualization_ids=[primary]),
                PedagogyRevealStep(id="triangle_pythagoras", title="Tìm cạnh còn lại", goal="Dùng định lí Pythagoras cho ba cạnh của tam giác vuông.", visualization_ids=[primary]),
                PedagogyRevealStep(id="triangle_first_angle", title="Tính góc thứ nhất", goal="Dùng tỉ số lượng giác của cạnh đối và cạnh huyền.", visualization_ids=[primary]),
                PedagogyRevealStep(id="triangle_second_angle", title="Tính góc thứ hai", goal="Hai góc nhọn phụ nhau nên góc còn lại bằng 90° trừ góc vừa tìm.", visualization_ids=[primary]),
                PedagogyRevealStep(id="triangle_check", title="Kiểm tra lại", goal="Thay ba cạnh vào định lí Pythagoras và cộng hai góc nhọn để kiểm tra.", visualization_ids=[primary]),
            ]
        elif "triangle_similarity" in problem:
            reveal_steps = [
                PedagogyRevealStep(id="similar_small", title="Dựng tam giác thứ nhất", goal="Dựng tam giác nhỏ theo hai cạnh đã cho.", visualization_ids=[primary]),
                PedagogyRevealStep(id="similar_large", title="Dựng tam giác thứ hai", goal="Dựng tam giác lớn với cạnh tương ứng đã biết.", visualization_ids=[primary]),
                PedagogyRevealStep(id="similar_ratio", title="Tính tỉ số đồng dạng", goal="Lập tỉ số giữa hai cạnh tương ứng.", visualization_ids=[primary]),
                PedagogyRevealStep(id="similar_conclude", title="Suy ra cạnh còn lại", goal="Nhân cạnh còn lại với cùng tỉ số rồi kiểm tra hai tỉ số bằng nhau.", visualization_ids=[primary]),
            ]
        elif "centroid" in problem or "triangle_congruence" in problem:
            reveal_steps = [
                PedagogyRevealStep(id="centroid_triangle", title="Dựng tam giác", goal="Dựng tam giác ABC và ghi tên các đỉnh.", visualization_ids=[primary]),
                PedagogyRevealStep(id="centroid_midpoint", title="Xác định trung điểm", goal="Đánh dấu M là trung điểm BC bằng hai dấu bằng nhau.", visualization_ids=[primary]),
                PedagogyRevealStep(id="centroid_median", title="Dựng trung tuyến và trọng tâm", goal="Nối A với M rồi đặt trọng tâm G trên đoạn đó.", visualization_ids=[primary]),
                PedagogyRevealStep(id="centroid_ratio", title="Đo hai phần", goal="Đo AG và GM để đọc trực tiếp tỉ số 2 : 1.", visualization_ids=[primary]),
            ]
        elif "word_equation_rectangle" in problem:
            reveal_steps = [
                PedagogyRevealStep(id="rectangle_unknown", title="Đặt ẩn cho chiều rộng", goal="Gọi chiều rộng là x và viết chiều dài theo x.", visualization_ids=[primary]),
                PedagogyRevealStep(id="rectangle_equation", title="Lập phương trình từ chu vi", goal="Nửa chu vi bằng tổng chiều dài và chiều rộng.", visualization_ids=[primary]),
                PedagogyRevealStep(id="rectangle_solve", title="Giải phương trình", goal="Thực hiện cùng phép toán ở hai vế để tìm x.", visualization_ids=[primary]),
                PedagogyRevealStep(id="rectangle_check", title="Dựng lại hình và kiểm tra", goal="Vẽ hình chữ nhật với kích thước tìm được và kiểm tra chu vi.", visualization_ids=[primary]),
            ]
        elif "algebraic_expression_modeling" in problem:
            reveal_steps = [
                PedagogyRevealStep(id="model_unknown", title="Chọn ẩn", goal="Gọi đại lượng chưa biết là x và nói rõ x biểu thị điều gì.", visualization_ids=[primary]),
                PedagogyRevealStep(id="model_terms", title="Dịch từng cụm từ", goal="Mỗi cụm từ trong đề trở thành đúng một hạng tử.", visualization_ids=[primary]),
                PedagogyRevealStep(id="model_expression", title="Ghép thành biểu thức", goal="Xếp các tile theo bậc để đọc biểu thức hoàn chỉnh.", visualization_ids=[primary]),
                PedagogyRevealStep(id="model_evaluate", title="Thử với vài giá trị", goal="Thay vài giá trị của x để kiểm tra biểu thức mô tả đúng tình huống.", visualization_ids=[primary]),
            ]
        elif "factorial" in problem:
            reveal_steps = [
                PedagogyRevealStep(id="factorial_read", title="Đọc ký hiệu", goal="Đọc n! là tích các số tự nhiên từ n giảm dần đến 1.", visualization_ids=[primary]),
                PedagogyRevealStep(id="factorial_expand", title="Khai triển tích", goal="Viết vài thừa số đầu và cuối để thấy đúng thứ tự nhân.", visualization_ids=[primary]),
                PedagogyRevealStep(id="factorial_checkpoints", title="Theo dõi các mốc", goal="Kiểm tra tích tại các mốc 10!, 20!, ... thay vì giấu toàn bộ phép nhân.", visualization_ids=[primary]),
                PedagogyRevealStep(id="factorial_result", title="Đọc kết quả chính xác", goal="Hiện đủ mọi chữ số và dùng số chữ số cùng số 0 tận cùng để kiểm tra.", visualization_ids=[primary]),
            ]
        elif "mixed_rational" in problem or "expression_tree" in problem:
            reveal_steps = [
                PedagogyRevealStep(id="expression_read", title="Đọc biểu thức", goal="Đọc từng số hạng và từng dấu phép tính.", visualization_ids=[primary]),
                PedagogyRevealStep(id="expression_priority", title="Chọn phép tính ưu tiên", goal="Xác định các phép nhân và chia phải làm trước.", visualization_ids=[primary]),
                PedagogyRevealStep(id="expression_reduce", title="Rút gọn từng nút", goal="Thay mỗi phép tính đã làm bằng giá trị của nó.", visualization_ids=[primary]),
                PedagogyRevealStep(id="expression_result", title="Kết luận giá trị", goal="Còn lại một giá trị duy nhất cho toàn biểu thức.", visualization_ids=[primary]),
            ]
        elif "discount_tax_percentage" in problem:
            reveal_steps = [
                PedagogyRevealStep(id="price_list", title="Đọc giá niêm yết", goal="Đặt giá gốc làm mốc 100%.", visualization_ids=[primary]),
                PedagogyRevealStep(id="price_discount", title="Trừ phần giảm giá", goal="Tính phần trăm giảm trên chính giá niêm yết.", visualization_ids=[primary]),
                PedagogyRevealStep(id="price_tax", title="Cộng thuế", goal="Tính thuế trên giá đã giảm, không phải trên giá gốc.", visualization_ids=[primary]),
                PedagogyRevealStep(id="price_final", title="Đọc số tiền phải trả", goal="Cộng các thay đổi để có giá cuối cùng và kiểm tra lại.", visualization_ids=[primary]),
            ]
        elif "multi_segment" in problem:
            reveal_steps = [
                PedagogyRevealStep(id="segment_route", title="Chia hành trình thành chặng", goal="Vẽ từng chặng theo đúng quãng đường của nó.", visualization_ids=[primary]),
                PedagogyRevealStep(id="segment_times", title="Tính thời gian từng chặng", goal="Chia quãng đường của mỗi chặng cho vận tốc của chính chặng đó.", visualization_ids=[primary]),
                PedagogyRevealStep(id="segment_total", title="Cộng thời gian", goal="Cộng thời gian các chặng để có tổng thời gian.", visualization_ids=[primary]),
                PedagogyRevealStep(id="segment_average", title="Tính vận tốc trung bình", goal="Lấy tổng quãng đường chia tổng thời gian, không lấy trung bình hai vận tốc.", visualization_ids=[primary]),
            ]
        elif "compound_linear_equation" in problem:
            reveal_steps = [
                PedagogyRevealStep(id="compound_read", title="Đọc hai vế như đề in", goal="Đọc nguyên vẹn hai vế, kể cả phần trong ngoặc.", visualization_ids=[primary]),
                PedagogyRevealStep(id="compound_expand", title="Phá ngoặc", goal="Nhân hệ số vào từng hạng tử trong ngoặc rồi thu gọn từng vế.", visualization_ids=[primary]),
                PedagogyRevealStep(id="compound_collect", title="Chuyển vế và gộp", goal="Đưa mọi hạng tử chứa ẩn về một vế, hằng số về vế còn lại.", visualization_ids=[primary]),
                PedagogyRevealStep(id="compound_divide", title="Chia đều hai vế", goal="Chia hai vế cho hệ số của ẩn.", visualization_ids=[primary]),
                PedagogyRevealStep(id="compound_check", title="Thử lại nghiệm", goal="Thay giá trị tìm được vào phương trình ban đầu để kiểm tra.", visualization_ids=[primary]),
            ]
        elif "arithmetic_mean" in problem:
            reveal_steps = [
                PedagogyRevealStep(id="mean_columns", title="Dựng các cột số liệu", goal="Dựng mỗi số liệu thành một cột đúng chiều cao.", visualization_ids=[primary]),
                PedagogyRevealStep(id="mean_total", title="Gộp thành tổng", goal="Cộng tất cả các số liệu thành một tổng chung.", visualization_ids=[primary]),
                PedagogyRevealStep(id="mean_share", title="Chia đều", goal="Chia tổng cho số lượng số liệu để tìm mức chung.", visualization_ids=[primary]),
                PedagogyRevealStep(id="mean_level", title="San bằng và kiểm tra", goal="San mọi cột về cùng mức rồi nhân ngược lại để kiểm tra tổng.", visualization_ids=[primary]),
            ]
        elif "proportional_system_two_variables" in problem:
            reveal_steps = [
                PedagogyRevealStep(id="proportional_bars", title="Vẽ hai thanh theo tỉ số", goal="Vẽ hai thanh có số phần bằng đúng tỉ số đã cho.", visualization_ids=[primary]),
                PedagogyRevealStep(id="proportional_gap", title="Đọc phần chênh lệch", goal="Số phần dôi ra chính là hiệu hai đại lượng.", visualization_ids=[primary]),
                PedagogyRevealStep(id="proportional_one_part", title="Tìm giá trị một phần", goal="Chia hiệu cho số phần chênh lệch.", visualization_ids=[primary]),
                PedagogyRevealStep(id="proportional_values", title="Suy ra hai đại lượng", goal="Nhân giá trị một phần với số phần của từng đại lượng rồi kiểm tra hiệu.", visualization_ids=[primary]),
            ]
        elif "multi_step_arithmetic" in problem:
            reveal_steps = [
                PedagogyRevealStep(id="multi_step_start", title="Đọc đại lượng ban đầu", goal="Dựng thanh biểu diễn số lượng ban đầu.", visualization_ids=[primary]),
                PedagogyRevealStep(id="multi_step_first", title="Thực hiện phép tính thứ nhất", goal="Áp dụng phép tính thứ nhất và giữ lại kết quả trung gian.", visualization_ids=[primary]),
                PedagogyRevealStep(id="multi_step_second", title="Thực hiện phép tính thứ hai", goal="Dùng kết quả trung gian làm đầu vào cho phép tính thứ hai.", visualization_ids=[primary]),
                PedagogyRevealStep(id="multi_step_conclusion", title="Đọc kết quả cuối", goal="So sánh thanh cuối với thanh ban đầu rồi kết luận.", visualization_ids=[primary]),
            ]
        elif "map_scale" in problem:
            reveal_steps = [
                PedagogyRevealStep(id="scale_measure", title="Đo trên bản đồ", goal="Đặt độ dài đo được lên thước bản đồ.", visualization_ids=[primary]),
                PedagogyRevealStep(id="scale_meaning", title="Hiểu tỉ lệ", goal="Đọc tỉ lệ 1 : n là một đơn vị bản đồ ứng với n đơn vị thật.", visualization_ids=[primary]),
                PedagogyRevealStep(id="scale_multiply", title="Nhân theo tỉ lệ", goal="Nhân độ dài đo được với mẫu số của tỉ lệ.", visualization_ids=[primary]),
                PedagogyRevealStep(id="scale_convert", title="Đổi đơn vị và kết luận", goal="Đổi kết quả về đơn vị dễ đọc rồi đối chiếu hai thước.", visualization_ids=[primary]),
            ]
        elif "circle_area" in problem:
            reveal_steps = [
                PedagogyRevealStep(id="circle_radius", title="Đọc bán kính", goal="Đánh dấu tâm O và bán kính r trên hình tròn.", visualization_ids=[primary]),
                PedagogyRevealStep(id="circle_sectors", title="Cắt thành hình quạt", goal="Chia hình tròn thành các hình quạt bằng nhau quanh tâm.", visualization_ids=[primary]),
                PedagogyRevealStep(id="circle_unroll", title="Xếp lại thành hình chữ nhật", goal="Xếp xen kẽ các hình quạt thành hình gần chữ nhật, dài nửa chu vi và rộng r.", visualization_ids=[primary]),
                PedagogyRevealStep(id="circle_formula", title="Đọc công thức", goal="Nửa chu vi π × r nhân với r cho diện tích π × r².", visualization_ids=[primary]),
                PedagogyRevealStep(id="circle_value", title="Thay số và kết luận", goal="Thay bán kính đã cho vào công thức rồi kết luận diện tích.", visualization_ids=[primary]),
            ]
        elif "circle_tangent_cyclic" in problem:
            reveal_steps = [
                PedagogyRevealStep(id="circle_setup", title="Dựng đường tròn", goal="Dựng đường tròn tâm O bán kính r và các điểm trên đường tròn.", visualization_ids=[primary]),
                PedagogyRevealStep(id="circle_tangent", title="Dựng tiếp tuyến", goal="Dựng tiếp tuyến tại tiếp điểm và đánh dấu góc vuông với bán kính.", visualization_ids=[primary]),
                PedagogyRevealStep(id="circle_central_angle", title="Đánh dấu góc ở tâm", goal="Đánh dấu góc ở tâm và cung bị chắn tương ứng.", visualization_ids=[primary]),
                PedagogyRevealStep(id="circle_inscribed_angle", title="Đánh dấu góc nội tiếp", goal="Đánh dấu góc nội tiếp cùng chắn một cung với góc ở tâm.", visualization_ids=[primary]),
                PedagogyRevealStep(id="circle_conclusion", title="Kết luận quan hệ", goal="Góc nội tiếp bằng nửa góc ở tâm cùng chắn một cung.", visualization_ids=[primary]),
            ]
        elif "divisibility_common_multiple" in problem:
            reveal_steps = [
                PedagogyRevealStep(id="lattice_first", title="Đánh dấu bội của số thứ nhất", goal="Tô các ô là bội của số thứ nhất trên lưới số.", visualization_ids=[primary]),
                PedagogyRevealStep(id="lattice_second", title="Đánh dấu bội của số thứ hai", goal="Tô các ô là bội của số thứ hai bằng ký hiệu khác.", visualization_ids=[primary]),
                PedagogyRevealStep(id="lattice_common", title="Tìm ô chung", goal="Các ô mang cả hai dấu là bội chung của hai số.", visualization_ids=[primary]),
                PedagogyRevealStep(id="lattice_least", title="Chọn bội chung nhỏ nhất", goal="Ô chung đầu tiên khác 0 là bội chung nhỏ nhất.", visualization_ids=[primary]),
            ]
        elif "linear_system_two_variables" in problem:
            reveal_steps = [
                PedagogyRevealStep(id="system_axes", title="Dựng hệ trục Oxy", goal="Dựng trục x và trục y cùng tỉ lệ, đánh dấu gốc O.", visualization_ids=[primary]),
                PedagogyRevealStep(id="system_first_line", title="Vẽ đường thứ nhất", goal="Lập bảng giá trị của phương trình thứ nhất rồi nối thành đường thẳng.", visualization_ids=[primary]),
                PedagogyRevealStep(id="system_second_line", title="Vẽ đường thứ hai", goal="Lập bảng giá trị của phương trình thứ hai trên cùng hệ trục.", visualization_ids=[primary]),
                PedagogyRevealStep(id="system_state", title="Đọc vị trí hai đường", goal="Xem hai đường cắt nhau, song song hay trùng nhau.", visualization_ids=[primary]),
                PedagogyRevealStep(id="system_check", title="Kiểm tra nghiệm", goal="Thay cặp giá trị đọc được vào cả hai phương trình để kiểm tra.", visualization_ids=[primary]),
            ]
        elif "linear_system_three_variables" in problem:
            reveal_steps = [
                PedagogyRevealStep(id="system3_read", title="Giữ nguyên ba phương trình", goal="Viết từng phương trình theo đúng thứ tự đề bài và bổ sung hệ số 0 cho hạng tử không xuất hiện.", visualization_ids=[primary]),
                PedagogyRevealStep(id="system3_matrix", title="Lập ma trận mở rộng", goal="Đưa hệ số của x, y, z và vế phải vào từng hàng; không bỏ bất kỳ phương trình nào.", visualization_ids=[primary]),
                PedagogyRevealStep(id="system3_eliminate", title="Khử từng ẩn", goal="Dùng phép biến đổi hàng tương đương để tạo các phần tử dẫn đầu và loại dần x, y, z.", visualization_ids=[primary]),
                PedagogyRevealStep(id="system3_planes", title="Dựng các mặt phẳng", goal="Mỗi phương trình là một mặt phẳng trên cùng hệ trục Oxyz; nghiệm chung nằm trên tất cả các mặt.", visualization_ids=[primary]),
                PedagogyRevealStep(id="system3_conclude", title="Kết luận tập nghiệm", goal="So sánh hạng ma trận để kết luận nghiệm duy nhất, vô số nghiệm hoặc vô nghiệm.", visualization_ids=[primary]),
                PedagogyRevealStep(id="system3_check", title="Thay lại để kiểm tra", goal="Nếu có nghiệm duy nhất, thay bộ (x; y; z) vào từng phương trình ban đầu và xác nhận hai vế bằng nhau.", visualization_ids=[primary]),
            ]
        elif "quadratic_surface" in problem:
            reveal_steps = [
                PedagogyRevealStep(id="surface_classify", title="Nhận ra hạng tử bình phương", goal="Phân biệt mặt cong với mặt phẳng: chỉ một biến có số mũ 2.", visualization_ids=[primary]),
                PedagogyRevealStep(id="surface_solve_output", title="Tách biến trên trục đứng", goal="Viết biến đầu ra theo hai biến còn lại để lấy độ cao của từng điểm.", visualization_ids=[primary]),
                PedagogyRevealStep(id="surface_parabolas", title="Dựng các lát parabol", goal="Giữ một biến cố định và vẽ nhiều parabol song song.", visualization_ids=[primary]),
                PedagogyRevealStep(id="surface_rulings", title="Nối thành mặt cong", goal="Nối các điểm cùng tham số để thấy hướng thẳng và hướng bị uốn cong.", visualization_ids=[primary]),
                PedagogyRevealStep(id="surface_check", title="Kiểm tra điểm mẫu", goal="Thay vài bộ tọa độ vào phương trình ban đầu để xác nhận chúng nằm trên mặt.", visualization_ids=[primary]),
            ]
        elif "linear_equation_three_variables" in problem:
            through_origin = _plane_passes_through_origin(model)
            locate_step = (
                PedagogyRevealStep(
                    id="plane_origin",
                    title="Nhận ra mặt phẳng qua gốc O",
                    goal="Vế phải bằng 0 nên điểm O(0; 0; 0) đã là một nghiệm; mặt phẳng đi qua gốc.",
                    visualization_ids=[primary],
                )
                if through_origin
                else PedagogyRevealStep(
                    id="plane_intercepts",
                    title="Tìm ba giao điểm",
                    goal="Lần lượt cho hai biến bằng 0 để tìm giao điểm với từng trục.",
                    visualization_ids=[primary],
                )
            )
            reveal_steps = [
                PedagogyRevealStep(id="plane_canonical", title="Chuyển về một vế", goal="Chuyển mọi hạng tử chứa biến về vế trái để được dạng ax + by + cz = d.", visualization_ids=[primary]),
                PedagogyRevealStep(id="plane_axes", title="Dựng hệ trục Oxyz", goal="Đặt ba trục x, y, z vuông góc tại gốc O với cùng tỉ lệ.", visualization_ids=[primary]),
                locate_step,
                PedagogyRevealStep(id="plane_surface", title="Dựng mặt phẳng", goal="Dựng mặt phẳng vuông góc với vectơ pháp tuyến (a; b; c).", visualization_ids=[primary]),
                PedagogyRevealStep(id="plane_check", title="Kiểm tra các điểm nghiệm", goal="Thay từng điểm mẫu vào ax + by + cz = d; có vô số nghiệm nên không có một giá trị x, y, z duy nhất.", visualization_ids=[primary]),
            ]
        elif primary.value == "coordinate_graph" and "cubic_equation" in problem:
            reveal_steps = [
                PedagogyRevealStep(id="cubic_coefficients", title="Đưa về dạng chuẩn", goal="Chuyển hết sang một vế để được ax³ + bx² + cx + d = 0, với a khác 0.", visualization_ids=[primary]),
                PedagogyRevealStep(id="cubic_shape", title="Nhìn dạng đồ thị", goal="Dựng đường cong bậc ba và đọc chiều đi lên hoặc đi xuống từ dấu của a.", visualization_ids=[primary]),
                PedagogyRevealStep(id="cubic_roots", title="Tìm giao điểm với Ox", goal="Mỗi giao điểm với Ox là một nghiệm thực của phương trình.", visualization_ids=[primary]),
                PedagogyRevealStep(id="cubic_factor", title="Tách nhân tử", goal="Dùng nghiệm tìm được để tách một nhân tử bậc nhất và giải phần bậc hai còn lại.", visualization_ids=[primary]),
                PedagogyRevealStep(id="cubic_check", title="Thay lại để kiểm tra", goal="Thay từng nghiệm vào đa thức; giá trị phải bằng 0.", visualization_ids=[primary]),
            ]
        elif primary.value == "coordinate_graph" and "quadratic_equation_vieta" in problem:
            reveal_steps = [
                PedagogyRevealStep(id="vieta_coefficients", title="Đọc hệ số", goal="Xác định a, b, c và điều kiện a khác 0.", visualization_ids=[primary]),
                PedagogyRevealStep(id="vieta_discriminant", title="Kiểm tra nghiệm", goal="Dùng biệt thức để xác định số nghiệm thực và giao điểm với Ox.", visualization_ids=[primary]),
                PedagogyRevealStep(id="vieta_roots", title="Đặt hai nghiệm", goal="Đặt x1, x2 trên trục và kiểm tra trực tiếp vào tam thức.", visualization_ids=[primary]),
                PedagogyRevealStep(id="vieta_sum_product", title="Nối với Viète", goal="Đối chiếu tổng nghiệm bằng -b/a và tích nghiệm bằng c/a.", visualization_ids=[primary]),
            ]
        elif primary.value == "coordinate_graph" and "quadratic_equation" in problem:
            reveal_steps = [
                PedagogyRevealStep(id="quadratic_coefficients", title="Đọc đủ ba hệ số", goal="Đưa phương trình về ax² + bx + c = 0 và giữ nguyên a, b, c đã in trong đề.", visualization_ids=[primary]),
                PedagogyRevealStep(id="quadratic_discriminant", title="Tính biệt thức", goal="Tính Δ = b² − 4ac để xác định phương trình có bao nhiêu nghiệm thực.", visualization_ids=[primary]),
                PedagogyRevealStep(id="quadratic_equation_roots", title="Tìm nghiệm", goal="Dùng công thức nghiệm phù hợp với dấu của Δ và đặt các nghiệm lên trục Ox.", visualization_ids=[primary]),
                PedagogyRevealStep(id="quadratic_equation_check", title="Kiểm tra bằng parabol", goal="Dựng y = ax² + bx + c; mỗi giao điểm với Ox phải trùng đúng một nghiệm vừa tính.", visualization_ids=[primary]),
            ]
        elif primary.value == "coordinate_graph" and "quadratic_function_graph" in problem:
            reveal_steps = [
                PedagogyRevealStep(id="quadratic_axes", title="Dựng hệ trục", goal="Dựng trục và đọc dấu hệ số a để biết chiều mở của parabol.", visualization_ids=[primary]),
                PedagogyRevealStep(id="quadratic_vertex", title="Tìm đỉnh", goal="Tính và đặt đỉnh cùng trục đối xứng trên hệ tọa độ.", visualization_ids=[primary]),
                PedagogyRevealStep(id="quadratic_roots", title="Đặt giao điểm", goal="Dùng biệt thức để đặt các nghiệm thực trên trục Ox.", visualization_ids=[primary]),
                PedagogyRevealStep(id="quadratic_curve", title="Dựng parabol", goal="Nối bảng điểm đối xứng thành đường cong liên tục.", visualization_ids=[primary]),
            ]
        elif primary.value == "coordinate_graph":
            reveal_steps = [
                PedagogyRevealStep(id="axes", title="Dựng hệ trục", goal="Dựng trục x, y với cùng tỉ lệ và đánh dấu gốc O.", visualization_ids=[primary]),
                PedagogyRevealStep(id="intercept", title="Đặt tung độ gốc", goal="Đặt điểm (0; b) từ hằng số của hàm số.", visualization_ids=[primary]),
                PedagogyRevealStep(id="slope", title="Dựng hệ số góc", goal="Đi ngang một đơn vị rồi đi dọc theo hệ số góc.", visualization_ids=[primary]),
                PedagogyRevealStep(id="function_line", title="Nối thành đồ thị", goal="Nối các điểm và đối chiếu với bảng giá trị.", visualization_ids=[primary]),
            ]
        elif model.domain.value == "algebra":
            reveal_steps = [
                PedagogyRevealStep(id="balance_observe", title="Quan sát hai vế", goal="Đọc mỗi vế như khối lượng trên một đĩa cân.", visualization_ids=[primary]),
                PedagogyRevealStep(id="balance_inverse", title="Khử hằng số", goal="Thực hiện cùng một phép toán nghịch đảo ở cả hai vế.", visualization_ids=[primary]),
                PedagogyRevealStep(id="balance_divide", title="Chia đều", goal="Chia hai vế cho hệ số của ẩn.", visualization_ids=[primary]),
                PedagogyRevealStep(id="balance_solution", title="Kiểm tra nghiệm", goal="Đọc giá trị một khối x và kiểm tra lại phương trình.", visualization_ids=[primary]),
            ]
        elif model.domain.value == "coordinate":
            reveal_steps = [
                PedagogyRevealStep(id="axes", title="Dựng hệ trục", goal="Dựng trục x, y với cùng tỉ lệ và đánh dấu gốc O.", visualization_ids=[primary]),
                PedagogyRevealStep(id="intercept", title="Đặt tung độ gốc", goal="Đặt điểm (0; b) từ hằng số của hàm số.", visualization_ids=[primary]),
                PedagogyRevealStep(id="slope", title="Dựng hệ số góc", goal="Đi ngang một đơn vị rồi đi dọc theo hệ số góc.", visualization_ids=[primary]),
                PedagogyRevealStep(id="function_line", title="Nối thành đồ thị", goal="Nối các điểm và đối chiếu với bảng giá trị.", visualization_ids=[primary]),
            ]
        elif model.domain.value == "geometry_3d" and any(token in problem for token in ("cylinder_volume", "cone_volume", "sphere_volume")):
            reveal_steps = [
                PedagogyRevealStep(id="solid_cross_section", title="Nhận mặt cắt tròn", goal="Xác định bán kính của mặt cắt qua trục.", visualization_ids=[primary]),
                PedagogyRevealStep(id="solid_revolve", title="Tạo khối tròn xoay", goal="Quay mặt cắt quanh trục để nhìn thấy toàn bộ khối.", visualization_ids=[primary]),
                PedagogyRevealStep(id="solid_compare", title="So sánh lớp thể tích", goal="Liên hệ hình nón với một phần ba hình trụ hoặc cầu với các lớp tròn.", visualization_ids=[primary]),
                PedagogyRevealStep(id="solid_volume", title="Tính thể tích", goal="Thay bán kính và chiều cao vào đúng công thức của khối.", visualization_ids=[primary]),
            ]
        elif model.domain.value == "geometry_3d":
            reveal_steps = [
                PedagogyRevealStep(id="xyz_base", title="Dựng mặt đáy", goal="Đặt chiều dài và chiều rộng trên mặt phẳng x-y.", visualization_ids=[primary]),
                PedagogyRevealStep(id="xyz_area", title="Tính diện tích đáy", goal="Nhân hai kích thước của mặt đáy.", visualization_ids=[primary]),
                PedagogyRevealStep(id="xyz_height", title="Nâng theo trục z", goal="Dựng chiều cao vuông góc với mặt đáy.", visualization_ids=[primary]),
                PedagogyRevealStep(id="xyz_volume", title="Ghép các lớp", goal="Nhân diện tích đáy với chiều cao để được thể tích.", visualization_ids=[primary]),
            ]
        return PedagogyPlan(
            grade_band=band,
            representation_level=level,
            primary_visualization=primary,
            supporting_visualizations=supporting,
            explanation_strategy=explanation,
            interaction_strategy=interactions,
            reveal_steps=reveal_steps,
        )
