from __future__ import annotations

import json
from io import BytesIO
from unittest.mock import AsyncMock

import httpx
import pytest
from fastapi import HTTPException, UploadFile

from app.api import math_lab as math_lab_api
from app.core.config import Settings
from app.schemas.math_lab import EvidenceSource, MathQuantityRole
from app.schemas.math_lab_text import extract_two_item_discount_system
from app.services.math_lab.analyzer import (
    MathProblemAnalyzer,
    OllamaMathVisionProvider,
    ProviderDocument,
)
from app.services.math_lab.foundation import MathLabFoundationService


TWO_BOOK_DISCOUNT_PROBLEM = """Câu 13. Bạn An mua một quyển sách bồi dưỡng Toán và một quyển sách bồi dưỡng Ngữ Văn với tổng số tiền theo giá niêm yết là 270 000 đồng. Vì An mua vào lúc cửa hàng có chương trình giảm giá nên khi thanh toán quyển sách Toán được giảm giá 10%; quyển sách Ngữ Văn được giảm giá 20%. Do đó An chỉ cần phải trả 228 000 đồng. Gọi giá niêm yết của quyển sách bồi dưỡng Toán và quyển sách bồi dưỡng Ngữ Văn lần lượt là x, y (đồng).
a) Điều kiện xác định x > 0, y > 0.
b) x + y = 270 000.
c) Hệ phương trình x + y = 270 000; 0,9x + 0,8y = 228 000.
d) Giá niêm yết của quyển sách bồi dưỡng Toán là 150 000 đồng và quyển sách bồi dưỡng Ngữ Văn là 120 000 đồng."""


def provider_document() -> ProviderDocument:
    return ProviderDocument.model_validate({
        "extracted_text": "Một xe đi 18 km trong 1,5 giờ. Hỏi quãng đường đi trong 2 giờ.",
        "confidence": 0.93,
        "requires_review": False,
        "questions": [{
            "question_number": "1",
            "stem": "Một xe đi 18 km trong 1,5 giờ. Hỏi quãng đường đi trong 2 giờ.",
            "question_format": "word_problem",
            "choices": [],
            "subquestions": [],
            "grade": 5,
            "domain": "motion",
            "problem_type": "distance_speed_time",
            "entities": [
                {"role": "moving_entity", "type": "vehicle", "label": "Xe", "evidence": {"confidence": 1, "status": "explicit"}},
                {"role": "origin", "type": "location", "label": "Điểm xuất phát", "evidence": {"confidence": 0.6, "status": "uncertain"}},
            ],
            "quantities": [
                {"role": "distance", "value": 18, "unit": "km", "label": "Quãng đường đã biết", "evidence": {"confidence": 1, "status": "explicit"}},
                {"role": "duration", "value": 1.5, "unit": "hour", "label": "Thời gian đã biết", "evidence": {"confidence": 1, "status": "explicit"}},
            ],
            "unknowns": [
                {"role": "distance", "kind": "distance", "unit": "km", "label": "Quãng đường trong 2 giờ"},
            ],
            "constraints": [],
            "start_time": None,
            "end_time": None,
            "confidence": 0.91,
            "requires_review": False,
            "review_notes": [],
        }],
    })


def test_ollama_grammar_schema_keeps_structure_but_drops_unsupported_annotations() -> None:
    schema = OllamaMathVisionProvider._grammar_schema(ProviderDocument.model_json_schema())
    encoded = json.dumps(schema)

    assert "$defs" in schema
    assert "properties" in schema
    assert "maxLength" not in encoded
    assert "minimum" not in encoded
    assert "pattern" not in encoded


def test_analyzer_prompt_preserves_operands_needed_for_visual_simulation() -> None:
    prompt = OllamaMathVisionProvider._prompt("text", 5, "1/2 + 1/3")

    assert "fraction_addition" in prompt
    assert "addend_numerator/addend_denominator" in prompt
    assert "linear_function" in prompt
    assert "cuboid_volume" in prompt
    assert "không rút gọn chúng thành riêng đáp số" in prompt
    assert "participant_roles" in prompt
    assert "remaining_of" in prompt


def test_provider_relationship_roles_become_stable_semantic_references() -> None:
    payload = provider_document().model_dump(mode="json")
    payload["questions"][0]["relationships"] = [{
        "type": "motion",
        "participant_roles": {
            "subject": "moving_entity",
            "from": "origin",
        },
        "parameters": {},
        "evidence": {"confidence": 1, "status": "explicit"},
    }]

    analysis = MathProblemAnalyzer(Settings())._finalize(
        ProviderDocument.model_validate(payload), "text", 5
    )
    relation = analysis.questions[0].semantic_model.relations[0]

    assert relation.type == "motion"
    assert relation.participants == {"subject": "entity_1", "from": "entity_2"}


def test_provider_schema_discards_an_inferred_value_that_solves_the_unknown() -> None:
    payload = provider_document().model_dump(mode="json")
    payload["questions"][0]["quantities"].append({
        "role": "distance",
        "value": 24,
        "unit": "km",
        "label": "Đáp số",
        "evidence": {"confidence": 0.9, "status": "inferred"},
    })

    sanitized = ProviderDocument.model_validate(payload)

    assert [item.role.value for item in sanitized.questions[0].quantities] == [
        "distance", "duration"
    ]
    assert sanitized.questions[0].unknowns[0].role.value == "distance"


def test_provider_schema_discards_an_explicit_result_when_result_is_still_unknown() -> None:
    payload = provider_document().model_dump(mode="json")
    payload["questions"][0].update({
        "domain": "fraction",
        "problem_type": "fraction_addition",
        "quantities": [
            {"role": "numerator", "value": 1, "unit": "one", "label": "Tử số 1", "evidence": {"confidence": 1, "status": "explicit"}},
            {"role": "denominator", "value": 2, "unit": "one", "label": "Mẫu số 1", "evidence": {"confidence": 1, "status": "explicit"}},
            {"role": "addend_numerator", "value": 1, "unit": "one", "label": "Tử số 2", "evidence": {"confidence": 1, "status": "explicit"}},
            {"role": "addend_denominator", "value": 3, "unit": "one", "label": "Mẫu số 2", "evidence": {"confidence": 1, "status": "explicit"}},
            {"role": "result", "value": 5 / 6, "unit": "one", "label": "Đáp số AI tự tính", "evidence": {"confidence": 1, "status": "explicit"}},
        ],
        "unknowns": [{"role": "result", "kind": "fraction", "unit": "one", "label": "Kết quả"}],
    })

    sanitized = ProviderDocument.model_validate(payload)

    assert [item.role.value for item in sanitized.questions[0].quantities] == [
        "numerator", "denominator", "addend_numerator", "addend_denominator"
    ]


def test_provider_schema_discards_fraction_roles_hallucinated_from_an_exponent() -> None:
    payload = provider_document().model_dump(mode="json")
    payload["questions"][0].update({
        "stem": "Khai triển (x + 3)^2.",
        "domain": "algebra",
        "problem_type": "binomial_expansion",
        "quantities": [
            {"role": "numerator", "value": 3, "unit": "one", "label": "AI đọc nhầm tử", "evidence": {"confidence": 1, "status": "explicit"}},
            {"role": "denominator", "value": 2, "unit": "one", "label": "AI đọc nhầm mẫu", "evidence": {"confidence": 1, "status": "explicit"}},
        ],
        "unknowns": [{"role": "result", "kind": "expression", "unit": "one", "label": "Biểu thức khai triển"}],
    })

    sanitized = ProviderDocument.model_validate(payload)

    assert sanitized.questions[0].quantities == []


def test_provider_schema_recovers_literal_linear_function_operands() -> None:
    payload = provider_document().model_dump(mode="json")
    payload["questions"][0].update({
        "stem": "Vẽ đồ thị hàm số y = 2x + 1.",
        "domain": "algebra",
        "problem_type": "linear_function",
        "quantities": [],
        "unknowns": [{"role": "result", "kind": "graph", "unit": "one", "label": "Đồ thị"}],
    })

    recovered = ProviderDocument.model_validate(payload).questions[0]

    assert [(item.role.value, item.value) for item in recovered.quantities] == [
        ("coefficient", 2.0),
        ("constant", 1.0),
    ]


def test_provider_schema_recovers_implicit_slope_and_zero_intercept() -> None:
    payload = provider_document().model_dump(mode="json")
    payload["questions"][0].update({
        "stem": "Vẽ đồ thị y = -x.",
        "domain": "algebra",
        "problem_type": "linear_function",
        "quantities": [],
        "unknowns": [{"role": "result", "kind": "graph", "unit": "one", "label": "Đồ thị"}],
    })

    recovered = ProviderDocument.model_validate(payload).questions[0]

    assert [(item.role.value, item.value) for item in recovered.quantities] == [
        ("coefficient", -1.0),
        ("constant", 0.0),
    ]
    assert all(item.evidence.status.value == "inferred" for item in recovered.quantities)


def test_provider_schema_recovers_printed_angle_without_solving_bisector() -> None:
    payload = provider_document().model_dump(mode="json")
    payload["questions"][0].update({
        "stem": "Cho ∠xOy = 80°, Ot là tia phân giác của ∠xOy. Số đo xOt bằng?",
        "domain": "geometry_2d",
        "problem_type": "angle_bisector",
        "quantities": [],
        "unknowns": [{"role": "result", "kind": "angle", "unit": "degree", "label": "Góc xOt"}],
    })

    recovered = ProviderDocument.model_validate(payload).questions[0]

    assert [(item.role.value, item.value, item.unit) for item in recovered.quantities] == [
        ("angle", 80.0, "degree"),
    ]
    assert recovered.unknowns[0].role.value == "result"
    assert all(item.value != 40 for item in recovered.quantities)


def test_provider_schema_recovers_sequential_remainder_ratio_operands() -> None:
    payload = provider_document().model_dump(mode="json")
    stem = (
        "Một cửa hàng có 160kg gạo và bán hết trong 3 ngày. "
        "Ngày thứ nhất cửa hàng bán được 3/8 số gạo. "
        "Ngày thứ hai cửa hàng bán được 1/4 số gạo còn lại. "
        "Tính tỉ số gạo bán được của ngày thứ ba và ngày thứ nhất."
    )
    payload["questions"][0].update({
        "stem": stem,
        "grade": 7,
        "domain": "arithmetic",
        "problem_type": "ratio calculation",
        "quantities": [],
        "unknowns": [{
            "role": "result",
            "kind": "ratio",
            "unit": "one",
            "label": "Tỉ số cần tìm",
        }],
        "requires_review": True,
        "review_notes": ["Mô hình chưa chắc dạng bài"],
    })

    recovered = ProviderDocument.model_validate(payload).questions[0]

    assert recovered.problem_type == "sequential_fraction_remainder_ratio"
    assert recovered.domain.value == "ratio"
    assert [(item.role.value, item.value, item.unit) for item in recovered.quantities] == [
        ("mass", 160.0, "kg"),
        ("numerator", 3.0, "one"),
        ("denominator", 8.0, "one"),
        ("addend_numerator", 1.0, "one"),
        ("addend_denominator", 4.0, "one"),
    ]
    assert recovered.unknowns[0].role.value == "result"
    assert all(item.role.value != "result" for item in recovered.quantities)
    assert recovered.requires_review is False
    assert recovered.review_notes == []


def test_provider_schema_recovers_mixed_area_sequential_remainder_operands() -> None:
    payload = provider_document().model_dump(mode="json")
    stem = (
        "Một khu đất rộng 10dam2 80m2, người ta sử dụng\n2\n5\n diện tích "
        "để làm nhà và\n1\n3\ndiện tích đất còn lại để trồng hoa, phần đất "
        "cuối cùng để làm chuồng trại chăn nuôi. Tính diện tích đất làm "
        "chuồng trại chăn nuôi?"
    )
    payload["questions"][0].update({
        "stem": stem,
        "grade": 6,
        # Reproduce the exact compact-model payload from the live failure.
        "domain": "geometry_2d",
        "problem_type": "sequential_fraction_remainder_ratio",
        "quantities": [
            {"role": "mass", "value": 10, "unit": "kg", "label": "diện tích ban đầu (dam2)", "evidence": {"confidence": 1, "status": "explicit"}},
            {"role": "mass", "value": 80, "unit": "kg", "label": "diện tích ban đầu (m2)", "evidence": {"confidence": 1, "status": "explicit"}},
        ],
        "unknowns": [{"role": "result", "kind": "area", "unit": None, "label": "Diện tích chuồng trại"}],
    })

    recovered = ProviderDocument.model_validate(payload).questions[0]

    assert recovered.problem_type == "sequential_fraction_remainder_quantity"
    assert recovered.domain.value == "ratio"
    assert [(item.role.value, item.value, item.unit) for item in recovered.quantities] == [
        ("area", 1000.0, "m2"),
        ("area", 80.0, "m2"),
        ("numerator", 2.0, "one"),
        ("denominator", 5.0, "one"),
        ("addend_numerator", 1.0, "one"),
        ("addend_denominator", 3.0, "one"),
    ]
    assert recovered.unknowns[0].role.value == "result"
    assert recovered.unknowns[0].unit == "m2"
    assert all(item.role.value != "result" for item in recovered.quantities)


def test_provider_schema_recovers_variable_people_work_rate_operands() -> None:
    payload = provider_document().model_dump(mode="json")
    stem = (
        "Một tổ gồm 8 người dự định làm xong một con đường trong 6 ngày "
        "nhưng sau đó tổ được bổ sung thêm 4 người. Hỏi con đường được làm "
        "xong trong bao nhiêu ngày biết sức làm việc của mỗi người như nhau."
    )
    payload["questions"][0].update({
        "stem": stem,
        "grade": 5,
        # Reproduce the real Qwen output from the teacher demo.
        "domain": "probability",
        "problem_type": "work_rate_with_variable_people",
        "quantities": [],
        "unknowns": [{
            "role": "result",
            "kind": "duration",
            "unit": None,
            "label": "Số ngày hoàn thành sau khi bổ sung người",
        }],
        "requires_review": True,
        "review_notes": ["Thiếu dữ kiện"],
    })

    recovered = ProviderDocument.model_validate(payload).questions[0]

    assert recovered.problem_type == "work_rate_with_variable_people"
    assert recovered.domain.value == "ratio"
    assert [(item.role.value, item.value, item.unit) for item in recovered.quantities] == [
        ("count_initial", 8.0, "one"),
        ("duration", 6.0, "one"),
        ("count_change", 4.0, "one"),
    ]
    assert recovered.unknowns[0].role.value == "result"
    assert recovered.unknowns[0].unit == "one"
    assert all(item.value != 4 for item in recovered.quantities[:-1])
    assert recovered.requires_review is False


def test_provider_schema_normalizes_blank_optional_clocks_and_recovers_direct_distance() -> None:
    payload = provider_document().model_dump(mode="json")
    stem = (
        "Một ô tô đi trong 5 giờ được 225 km. "
        "Ô tô đó đi trong 8 giờ được quãng đường là bao nhiêu"
    )
    payload["questions"][0].update({
        "stem": stem,
        "grade": 5,
        # Exact invalid fields emitted by Qwen during the live demo.
        "start_time": "",
        "end_time": "",
        "domain": "motion",
        "problem_type": "distance_speed_time",
        "quantities": [],
        "unknowns": [{
            "role": "result",
            "kind": "distance",
            "unit": None,
            "label": "Quãng đường cần tìm",
        }],
        "relationships": [],
    })

    recovered = ProviderDocument.model_validate(payload).questions[0]

    assert recovered.start_time is None
    assert recovered.end_time is None
    assert recovered.problem_type == "distance_time_direct_proportion"
    assert recovered.domain.value == "ratio"
    assert [(item.role.value, item.value, item.unit) for item in recovered.quantities] == [
        ("duration", 5.0, "hour"),
        ("distance", 225.0, "km"),
        ("duration", 8.0, "hour"),
    ]
    assert recovered.unknowns[0].role.value == "result"
    assert recovered.unknowns[0].unit == "km"
    assert all(item.value != 360 for item in recovered.quantities)
    assert recovered.relationships[0].participant_roles["target_duration"] == "duration[2]"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("stem", "expected"),
    [
        (
            "Một ô tô đi trong 5 giờ được 225 km. Ô tô đó đi trong 8 giờ "
            "được quãng đường là bao nhiêu",
            (5.0, 225.0, 8.0),
        ),
        (
            "Một xe chạy được 180 km trong 4 giờ. Trong 7 giờ xe đó đi được "
            "quãng đường là bao nhiêu?",
            (4.0, 180.0, 7.0),
        ),
    ],
)
async def test_direct_distance_text_uses_fast_deterministic_semantics(
    stem: str,
    expected: tuple[float, float, float],
) -> None:
    # Provider output is irrelevant for this strict grammar; this also keeps a
    # common classroom problem working if the VLM is temporarily unavailable.
    provider = StubProvider()
    provider.available = AsyncMock(return_value=False)
    provider.analyze_text = AsyncMock(side_effect=AssertionError("VLM must not be called"))
    analyzer = MathProblemAnalyzer(Settings(), provider=provider)

    result = await analyzer.analyze_text(stem, 5)
    model = result.questions[0].semantic_model
    plan = MathLabFoundationService().plan(model)

    assert model.problem_type == "distance_time_direct_proportion"
    assert model.domain.value == "ratio"
    assert tuple(item.value for item in model.quantities) == expected
    assert [item.role.value for item in model.quantities] == ["duration", "distance", "duration"]
    assert model.unknowns[0].role.value == "result"
    assert all(item.role.value != "result" for item in model.quantities)
    assert model.relations[0].type == "direct_proportion"
    assert plan.decisions[0].visualization.value == "bar_model"
    assert plan.visual_plan.status == "ready"
    assert len(plan.pedagogy.reveal_steps) == 5
    provider.analyze_text.assert_not_awaited()


def test_provider_schema_recovers_parenthesized_multiplication_operands() -> None:
    payload = provider_document().model_dump(mode="json")
    payload["questions"][0].update({
        "stem": "(1+1) x 2 bầng mấy",
        "grade": 3,
        # Exact schema-valid but renderer-empty output observed on the live web.
        "domain": "arithmetic",
        "problem_type": "multiplication_basic",
        "quantities": [],
        "unknowns": [{
            "role": "result",
            "kind": "number",
            "unit": "one",
            "label": "Kết quả",
        }],
        "relationships": [],
    })

    recovered = ProviderDocument.model_validate(payload).questions[0]

    assert recovered.problem_type == "parenthesized_addition_multiplication"
    assert [(item.role.value, item.value) for item in recovered.quantities] == [
        ("count_initial", 1.0),
        ("count_change", 1.0),
        ("coefficient", 2.0),
    ]
    assert all(item.value != 4 for item in recovered.quantities)
    assert recovered.relationships[0].parameters == {
        "inner_operation": "addition",
        "outer_operation": "multiplication",
        "order": "parentheses_first",
    }


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("stem", "expected_values", "expected_type"),
    [
        ("(1+1) x 2 bầng mấy", [1.0, 1.0, 2.0], "parenthesized_addition_multiplication"),
        ("( 1 + 1 ) x 2 bang may?", [1.0, 1.0, 2.0], "parenthesized_addition_multiplication"),
        ("Tính ( 2 + 3 ) nhân 4 bằng bao nhiêu?", [2.0, 3.0, 4.0], "parenthesized_addition_multiplication"),
        ("(5 - 2) × 4 = ?", [5.0, 2.0, 4.0], "parenthesized_subtraction_multiplication"),
    ],
)
async def test_parenthesized_multiplication_bypasses_empty_vlm_payload(
    stem: str,
    expected_values: list[float],
    expected_type: str,
) -> None:
    provider = StubProvider()
    provider.available = AsyncMock(return_value=False)
    provider.analyze_text = AsyncMock(side_effect=AssertionError("VLM must not be called"))
    analyzer = MathProblemAnalyzer(Settings(), provider=provider)

    result = await analyzer.analyze_text(stem, None)
    model = result.questions[0].semantic_model
    plan = MathLabFoundationService().plan(model)

    assert model.problem_type == expected_type
    assert model.grade == 3
    assert [item.value for item in model.quantities] == expected_values
    assert [item.role.value for item in model.quantities] == [
        "count_initial", "count_change", "coefficient"
    ]
    assert all(item.role.value != "result" for item in model.quantities)
    assert plan.decisions[0].visualization.value == "grouping"
    assert plan.visual_plan.status == "ready"
    assert len(plan.pedagogy.reveal_steps) == 4
    provider.analyze_text.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("grade", "stem", "expected_type", "quantity_count", "renderer"),
    [
        (1, "Lan có 5 quả táo, mẹ cho thêm 3 quả. Hỏi Lan có tất cả bao nhiêu quả táo?", "addition_basic", 2, "object_group"),
        (1, "Trong bãi có 58 chiếc xe tải. Có 38 chiếc xe rời bãi. Hỏi xe tải còn lại trong bãi là bao nhiêu?", "subtraction_basic", 2, "object_group"),
        (2, "Có 60 con chim, 17 con chim bay đi. Hỏi còn lại bao nhiêu con chim?", "subtraction_basic", 2, "object_group"),
        (2, "Có 24 cái kẹo chia đều cho 6 bạn. Mỗi bạn được bao nhiêu cái kẹo?", "division_basic", 2, "grouping"),
        (4, "Tính 1/2 + 1/4 bằng bao nhiêu?", "fraction_addition", 4, "fraction"),
        (4, "Một hình chữ nhật dài 8 cm, rộng 5 cm. Tính diện tích hình chữ nhật.", "rectangle_area", 2, "geometry_2d"),
        (7, "2x+y=1", "linear_equation_two_variables_graph", 2, "coordinate_graph"),
        (7, "2x+1", "polynomial_evaluate_reorder", 4, "algebra_tiles"),
        (8, "Giải phương trình 2x + 3 = 9.", "linear_equation", 3, "balance"),
        (9, "3x+y+z=6", "linear_equation_three_variables_plane", 4, "geometry_3d"),
        (9, "Tam giác ABC vuông tại A, AB = 3 cm, AC = 4 cm. Tính độ dài BC.", "right_triangle_hypotenuse", 2, "geometry_2d"),
    ],
)
async def test_common_text_families_have_complete_deterministic_visual_plans(
    grade: int,
    stem: str,
    expected_type: str,
    quantity_count: int,
    renderer: str,
) -> None:
    provider = StubProvider()
    provider.available = AsyncMock(return_value=False)
    provider.analyze_text = AsyncMock(side_effect=AssertionError("VLM must not be called"))
    analyzer = MathProblemAnalyzer(Settings(), provider=provider)

    result = await analyzer.analyze_text(stem, grade)
    model = result.questions[0].semantic_model
    plan = MathLabFoundationService().plan(model)

    assert model.problem_type == expected_type
    assert len(model.quantities) == quantity_count
    assert all(item.role != MathQuantityRole.RESULT for item in model.quantities) or expected_type == "linear_equation"
    assert plan.decisions[0].visualization.value == renderer
    assert plan.visual_plan.status == "ready"
    assert len(plan.pedagogy.reveal_steps) >= 3
    provider.analyze_text.assert_not_awaited()


def test_provider_schema_recovers_short_addition_operands_without_solving() -> None:
    payload = provider_document().model_dump(mode="json")
    payload["questions"][0].update({
        "stem": "4+3 = ?",
        "grade": 1,
        "domain": "arithmetic",
        "problem_type": "addition_basic",
        "quantities": [],
        "unknowns": [{"role": "result", "kind": "number", "unit": "one", "label": "?"}],
    })

    recovered = ProviderDocument.model_validate(payload).questions[0]

    assert recovered.problem_type == "addition_basic"
    assert [(item.role.value, item.value) for item in recovered.quantities] == [
        ("count_initial", 4.0),
        ("count_change", 3.0),
    ]
    assert [(item.role.value, item.kind) for item in recovered.unknowns] == [
        ("result", "number"),
    ]
    assert all(item.value != 7 for item in recovered.quantities)
    assert recovered.requires_review is False
    assert recovered.review_notes == []


def test_provider_schema_corrects_discount_checkout_misclassification() -> None:
    payload = provider_document().model_dump(mode="json")
    stem = (
        "Bác Thu mua ba món hàng ở một siêu thị. "
        "Món hàng thứ nhất giá 125 000 đồng và được giảm giá 30%, "
        "món hàng thứ hai giá 300 000 đồng và được giảm giá 15%, "
        "món hàng thứ ba được giảm giá 12,5%. "
        "Tổng số tiền bác Thu phải thanh toán là 692 500 đồng. "
        "Hỏi giá tiền món hàng thứ ba lúc chưa giảm giá là bao nhiêu?"
    )
    payload["questions"][0].update({
        "stem": stem,
        "grade": 7,
        "domain": "ratio",
        # Reproduce the real compact-model mistake from the teacher demo.
        "problem_type": "sequential_fraction_remainder_ratio",
        "quantities": [
            {"role": "mass", "value": 692500, "unit": "g", "label": "Tổng thanh toán (đồng)", "evidence": {"confidence": 1, "status": "explicit"}},
            {"role": "mass", "value": 125000, "unit": "g", "label": "Giá món 1 (đồng)", "evidence": {"confidence": 1, "status": "explicit"}},
        ],
        "unknowns": [{"role": "result", "kind": "money", "unit": "one", "label": "Giá gốc món thứ ba"}],
        "requires_review": True,
        "review_notes": ["Sai dạng bài"],
    })

    recovered = ProviderDocument.model_validate(payload).questions[0]

    assert recovered.problem_type == "multi_item_reverse_discount"
    assert recovered.domain.value == "ratio"
    assert [(item.role.value, item.value, item.unit) for item in recovered.quantities] == [
        ("count_initial", 125000.0, "one"),
        ("count_initial", 300000.0, "one"),
        ("probability", 30.0, "one"),
        ("probability", 15.0, "one"),
        ("probability", 12.5, "one"),
        ("total", 692500.0, "one"),
    ]
    assert recovered.unknowns[0].role.value == "result"
    assert recovered.requires_review is False
    assert recovered.review_notes == []


@pytest.mark.parametrize(
    ("stem", "expected_type", "expected_values"),
    [
        ("2 nhân 4 bằng mấy?", "multiplication_basic", [2.0, 4.0]),
        ("12 chia 3 bằng mấy?", "division_basic", [12.0, 3.0]),
    ],
)
def test_provider_schema_recovers_basic_operation_operands_for_grouping(
    stem: str,
    expected_type: str,
    expected_values: list[float],
) -> None:
    payload = provider_document().model_dump(mode="json")
    payload["questions"][0].update({
        "stem": stem,
        "grade": 1,
        "domain": "arithmetic",
        "problem_type": expected_type,
        # Reproduce the schema-valid but renderer-invalid model from the demo.
        "quantities": [],
        "unknowns": [{
            "role": "result",
            "kind": "number",
            "unit": "one",
            "label": "Kết quả",
        }],
    })

    recovered = ProviderDocument.model_validate(payload).questions[0]

    assert recovered.problem_type == expected_type
    assert [item.role.value for item in recovered.quantities] == [
        "count_initial",
        "count_change",
    ]
    assert [item.value for item in recovered.quantities] == expected_values
    assert recovered.unknowns[0].role.value == "result"
    assert all(item.role.value != "result" for item in recovered.quantities)


@pytest.mark.parametrize("expression", ["Kết quả (−2/5)³ là", "Kết quả (-2/5)^3 là"])
def test_provider_schema_recovers_fraction_power_operands_without_solving(expression: str) -> None:
    payload = provider_document().model_dump(mode="json")
    payload["questions"][0].update({
        "stem": expression,
        "choices": ["A. 8/125", "B. 4/25", "C. -8/125", "D. 8/15"],
        "domain": "algebra",
        "problem_type": "power",
        "quantities": [],
        "unknowns": [{"role": "result", "kind": "fraction", "unit": "one", "label": "Kết quả"}],
    })

    draft = ProviderDocument.model_validate(payload)
    question = draft.questions[0]

    assert question.problem_type == "fraction_power"
    assert [(item.role.value, item.value) for item in question.quantities] == [
        ("numerator", -2.0), ("denominator", 5.0), ("exponent", 3.0),
    ]
    assert all(item.role.value != "result" for item in question.quantities)


def test_provider_schema_rejects_units_that_do_not_match_roles() -> None:
    payload = provider_document().model_dump(mode="json")
    payload["questions"][0]["quantities"][0].update({
        "role": "count_initial",
        "unit": "m",
    })

    with pytest.raises(ValueError, match="unit=one"):
        ProviderDocument.model_validate(payload)


def test_provider_schema_rejects_length_unit_for_mass_role() -> None:
    payload = provider_document().model_dump(mode="json")
    payload["questions"][0]["quantities"][0].update({
        "role": "mass",
        "unit": "m",
    })

    with pytest.raises(ValueError, match="mass unit"):
        ProviderDocument.model_validate(payload)


def test_provider_schema_rejects_fake_variable_quantity_for_unknown() -> None:
    payload = provider_document().model_dump(mode="json")
    payload["questions"][0].update({
        "domain": "algebra",
        "problem_type": "linear_equation",
        "quantities": [{
            "role": "variable",
            "value": 0,
            "unit": "one",
            "label": "x",
            "evidence": {"confidence": 1, "status": "explicit"},
        }],
        "unknowns": [{
            "role": "variable",
            "kind": "number",
            "unit": "one",
            "label": "x",
        }],
    })

    with pytest.raises(ValueError, match="role=result"):
        ProviderDocument.model_validate(payload)


class StubProvider:
    name = "test-provider"
    model = "test-model"

    async def available(self) -> bool:
        return True

    async def analyze_text(self, _text, _grade_hint):
        return provider_document()

    async def analyze_image(self, _image, _media_type, _grade_hint):
        return provider_document()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "stem",
    [
        "4*98",
        "4x98",
        "4X98",
        "4 x 98 bằng mấy ?",
        "4 × 98",
        "4·98",
        "4⋅98",
        "4 nhân 98 bằng mấy?",
    ],
)
async def test_large_multiplication_keyboard_variants_keep_both_operands_and_plan(
    stem: str,
) -> None:
    provider = StubProvider()
    provider.analyze_text = AsyncMock(side_effect=AssertionError("VLM must not be called"))
    analyzer = MathProblemAnalyzer(Settings(), provider=provider)

    result = await analyzer.analyze_text(stem, 2)
    model = result.questions[0].semantic_model
    plan = MathLabFoundationService().plan(model)

    assert provider.analyze_text.await_count == 0
    assert model.source_text == stem
    assert model.problem_type == "multiplication_basic"
    assert [item.value for item in model.quantities] == [4.0, 98.0]
    assert [item.role.value for item in model.quantities] == [
        "count_initial",
        "count_change",
    ]
    assert plan.decisions[0].visualization.value == "grouping"
    assert plan.visual_plan.status == "ready"


@pytest.mark.parametrize(
    ("stem", "expected_type", "expected_values", "expected_visualization"),
    [
        ("38475*9374", "multiplication_basic", [38475.0, 9374.0], "column_algorithm"),
        ("38475\\*9374", "multiplication_basic", [38475.0, 9374.0], "column_algorithm"),
        ("993948 chia 7", "division_basic", [993948.0, 7.0], "column_algorithm"),
        ("92!", "factorial", [92.0], "expression_tree"),
        ("92 giai thừa", "factorial", [92.0], "expression_tree"),
        ("giai thừa của 92 bằng mấy?", "factorial", [92.0], "expression_tree"),
    ],
)
@pytest.mark.anyio
async def test_large_integer_and_factorial_inputs_use_deterministic_exact_plans(
    stem: str,
    expected_type: str,
    expected_values: list[float],
    expected_visualization: str,
) -> None:
    provider = StubProvider()
    provider.analyze_text = AsyncMock(side_effect=AssertionError("VLM must not be called"))
    analyzer = MathProblemAnalyzer(Settings(), provider=provider)

    result = await analyzer.analyze_text(stem, None)
    model = result.questions[0].semantic_model
    plan = MathLabFoundationService().plan(model)

    provider.analyze_text.assert_not_awaited()
    assert model.source_text == stem
    assert model.problem_type == expected_type
    assert [item.value for item in model.quantities] == expected_values
    assert plan.decisions[0].visualization.value == expected_visualization
    assert plan.visual_plan.status == "ready"


def test_two_book_discount_extractor_keeps_printed_prices_as_a_claim() -> None:
    facts = extract_two_item_discount_system(TWO_BOOK_DISCOUNT_PROBLEM)

    assert facts is not None
    assert facts.list_total == 270_000
    assert facts.paid_total == 228_000
    assert facts.first_discount == 10
    assert facts.second_discount == 20
    assert facts.claimed_first == 150_000
    assert facts.claimed_second == 120_000


def test_two_book_discount_extractor_does_not_widen_a_single_item_sale() -> None:
    assert extract_two_item_discount_system(
        "Một chiếc áo giá 300 000 đồng, được giảm giá 20%. Hỏi số tiền phải trả."
    ) is None


@pytest.mark.asyncio
async def test_two_book_discount_text_bypasses_vlm_and_builds_an_exact_scene() -> None:
    provider = StubProvider()
    provider.analyze_text = AsyncMock(side_effect=AssertionError("VLM must not be called"))
    analyzer = MathProblemAnalyzer(Settings(), provider=provider)

    result = await analyzer.analyze_text(TWO_BOOK_DISCOUNT_PROBLEM, 9)

    assert provider.analyze_text.await_count == 0
    assert len(result.questions) == 1
    semantic = result.questions[0].semantic_model
    assert semantic.problem_type == "two_item_discount_system"
    assert [(item.role.value, item.value) for item in semantic.quantities] == [
        ("total", 270_000),
        ("total", 228_000),
        ("probability", 10),
        ("probability", 20),
    ]
    assert [(item.role.value, item.label) for item in semantic.unknowns] == [
        ("variable", "Giá niêm yết Sách Toán (x, đồng)"),
        ("variable", "Giá niêm yết Sách Ngữ Văn (y, đồng)"),
    ]
    assert 150_000 not in [item.value for item in semantic.quantities]
    assert 120_000 not in [item.value for item in semantic.quantities]
    assert semantic.relations[0].parameters["claimed_first"] == 150_000
    assert semantic.relations[0].parameters["claimed_second"] == 120_000

    plan = MathLabFoundationService().plan(semantic)
    assert plan.decisions[0].visualization.value == "percent_grid"
    assert plan.visual_plan.status == "ready"
    assert [step.id for step in plan.pedagogy.reveal_steps] == [
        "discount_variables",
        "discount_list_equation",
        "discount_paid_equation",
        "discount_eliminate",
        "discount_prices",
        "discount_verify",
    ]


def test_provider_schema_repairs_an_empty_generic_two_book_discount_result() -> None:
    payload = provider_document().model_dump(mode="json")
    payload["questions"][0].update({
        "stem": TWO_BOOK_DISCOUNT_PROBLEM,
        "grade": 9,
        "domain": "algebra",
        "problem_type": "linear_equation_system",
        "entities": [],
        "quantities": [],
        "unknowns": [{
            "role": "result",
            "kind": "number",
            "unit": "one",
            "label": "Kết quả AI chưa cấu trúc",
        }],
        "relationships": [],
    })

    repaired = ProviderDocument.model_validate(payload).questions[0]

    assert repaired.problem_type == "two_item_discount_system"
    assert [item.value for item in repaired.quantities] == [270_000, 228_000, 10, 20]
    assert len(repaired.unknowns) == 2
    assert repaired.relationships[0].type == "two_item_discount_system"


@pytest.mark.asyncio
async def test_image_analysis_collapses_split_true_false_rows_into_one_scene() -> None:
    payload = provider_document().model_dump(mode="json")
    payload["extracted_text"] = TWO_BOOK_DISCOUNT_PROBLEM
    base = payload["questions"][0]
    payload["questions"] = []
    for index, stem in enumerate([
        "Bạn An mua sách Toán và Ngữ Văn.",
        "a) x > 0, y > 0.",
        "b) x + y = 270 000.",
        "c) 0,9x + 0,8y = 228 000.",
        "d) x = 150 000, y = 120 000.",
    ], start=1):
        question = dict(base)
        question.update({
            "question_number": str(index),
            "stem": stem,
            "grade": 9,
            "domain": "algebra",
            "problem_type": "linear_equation_system",
            "entities": [],
            "quantities": [],
            "unknowns": [{
                "role": "result",
                "kind": "number",
                "unit": "one",
                "label": "Kết quả AI chưa cấu trúc",
            }],
            "relationships": [],
        })
        payload["questions"].append(question)
    provider = StubProvider()
    provider.analyze_image = AsyncMock(return_value=ProviderDocument.model_validate(payload))
    analyzer = MathProblemAnalyzer(Settings(), provider=provider)

    result = await analyzer.analyze_image(b"image-bytes", "image/png", 9)

    assert provider.analyze_image.await_count == 1
    assert len(result.questions) == 1
    semantic = result.questions[0].semantic_model
    assert semantic.problem_type == "two_item_discount_system"
    assert (
        MathLabFoundationService().plan(semantic).decisions[0].visualization.value
        == "percent_grid"
    )


@pytest.mark.asyncio
async def test_text_analysis_normalizes_provider_dto_and_preserves_evidence() -> None:
    analyzer = MathProblemAnalyzer(Settings(), provider=StubProvider())
    result = await analyzer.analyze_text("Đề mới không nằm trong preset", 6)
    question = result.questions[0]
    model = question.semantic_model

    assert result.extracted_text == "Đề mới không nằm trong preset"
    assert question.stem == "Đề mới không nằm trong preset"
    assert model.source_text == "Đề mới không nằm trong preset"
    assert model.grade == 6
    assert model.quantities[0].id == "quantity_1"
    assert model.quantities[0].role.value == "distance"
    assert model.quantities[0].evidence.source == EvidenceSource.TEXT_INPUT
    assert model.entities[1].evidence.source == EvidenceSource.SYSTEM
    assert question.requires_review is True

    scene = MathLabFoundationService().plan(model).scene
    assert scene.metadata["source_text"] == "Đề mới không nằm trong preset"
    assert scene.metadata["source_preserved"] is True
    motion = next(item for item in scene.visualizations if item.type.value == "motion_path")
    assert motion.bindings["distance"] == ["quantity_1"]
    assert motion.bindings["moving_entity"] == ["entity_1"]


@pytest.mark.asyncio
async def test_motion_analysis_does_not_derive_the_requested_speed_answer() -> None:
    payload = provider_document().model_dump(mode="json")
    payload["questions"][0]["unknowns"][0].update({
        "role": "speed",
        "unit": "km/h",
    })
    draft = ProviderDocument.model_validate(payload)
    analyzer = MathProblemAnalyzer(Settings(), provider=StubProvider())

    result = analyzer._finalize(draft, "text", 5)

    roles = [item.role.value for item in result.questions[0].semantic_model.quantities]
    assert "speed" not in roles


@pytest.mark.asyncio
async def test_capabilities_are_derived_from_provider_health() -> None:
    capabilities = await MathProblemAnalyzer(Settings(), provider=StubProvider()).capabilities()
    assert capabilities.text_analysis is True
    assert capabilities.image_analysis is True
    assert capabilities.provider_available is True


@pytest.mark.asyncio
async def test_ollama_adapter_validates_structured_thinking_field() -> None:
    draft = provider_document()

    async def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api/tags":
            return httpx.Response(200, json={"models": [{"name": "qwen3-vl:8b-instruct"}]})
        event = {
            "message": {
                "role": "assistant",
                "content": "",
                "thinking": (
                    '<think>\n{"questions": []}\n</think>\n'
                    + draft.model_dump_json()
                ),
            },
            "done": True,
        }
        return httpx.Response(200, text=json.dumps(event) + "\n")

    provider = OllamaMathVisionProvider(
        Settings(math_lab_analysis_timeout_seconds=2),
        transport=httpx.MockTransport(handler),
    )
    result = await provider.analyze_text("Một đề Toán thật", 5)
    assert result.questions[0].quantities[0].role.value == "distance"


@pytest.mark.asyncio
async def test_image_analysis_retries_only_when_multiple_choice_rows_are_missing() -> None:
    first_payload = provider_document().model_dump(mode="json")
    first_payload["questions"][0].update({
        "question_format": "multiple_choice",
        "choices": [],
    })
    recovered_payload = provider_document().model_dump(mode="json")
    recovered_payload["extracted_text"] += "\nA. 8/125\nB. 4/25\nC. -8/125\nD. 8/15"
    recovered_payload["questions"][0].update({
        "question_format": "multiple_choice",
        "choices": ["A. 8/125", "B. 4/25", "C. -8/125", "D. 8/15"],
    })
    provider = OllamaMathVisionProvider(Settings())
    provider._request = AsyncMock(side_effect=[
        ProviderDocument.model_validate(first_payload),
        ProviderDocument.model_validate(recovered_payload),
    ])

    result = await provider.analyze_image(b"png-bytes", "image/png", 7)

    assert provider._request.await_count == 2
    assert result.questions[0].choices[2] == "C. -8/125"
    assert "C. -8/125" in result.extracted_text


@pytest.mark.asyncio
async def test_image_endpoint_forwards_real_jpeg_bytes_to_analyzer(monkeypatch) -> None:
    image = b"\xff\xd8\xff\xe0" + b"synthetic-jpeg-bytes"
    analyzer = AsyncMock()
    analyzer.analyze_image.return_value = {"questions": []}
    monkeypatch.setattr(math_lab_api, "_analyzer", lambda _settings: analyzer)

    result = await math_lab_api.analyze_math_image(
        _user=object(),
        file=UploadFile(filename="de-toan.jpg", file=BytesIO(image)),
        grade_hint=4,
        settings=Settings(math_lab_max_image_bytes=1024),
    )

    assert result == {"questions": []}
    analyzer.analyze_image.assert_awaited_once_with(image, "image/jpeg", 4)


@pytest.mark.asyncio
async def test_image_endpoint_rejects_extension_only_fake_image() -> None:
    with pytest.raises(HTTPException) as exc_info:
        await math_lab_api.analyze_math_image(
            _user=object(),
            file=UploadFile(filename="fake.jpg", file=BytesIO(b"not really an image")),
            grade_hint=None,
            settings=Settings(math_lab_max_image_bytes=1024),
        )

    assert exc_info.value.status_code == 415
