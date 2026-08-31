from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.math_lab import (
    Evidence,
    MathDomain,
    MathLabHistoryEntry,
    MathLabPlanRequest,
    MathQuantityRole,
    MathSemanticModel,
    SemanticConstraint,
    VisualizationId,
)
from app.services.math_lab import MathLabFoundationService
from app.services.math_lab.units import UnitConversionError, canonicalize, convert


FIXTURES = json.loads(
    (Path(__file__).parent / "fixtures" / "math_lab_golden.json").read_text()
)


@pytest.mark.parametrize("case", FIXTURES, ids=lambda case: case["name"])
def test_golden_visualization_decisions(case: dict) -> None:
    model = MathSemanticModel.model_validate(case["model"])
    result = MathLabFoundationService().plan(model)
    selected = [item.visualization.value for item in result.decisions]
    for expected in case["expected"]:
        assert expected in selected
    assert result.scene.semantic_model_id == model.id
    assert result.scene.visualizations
    assert result.scene.world.revision == 0


def test_motion_scene_uses_data_and_one_canonical_world_state() -> None:
    case = next(item for item in FIXTURES if item["name"] == "grade_5_motion")
    result = MathLabFoundationService().plan(MathSemanticModel.model_validate(case["model"]))

    assert result.scene.world.values["distance"].canonical_value == pytest.approx(1200)
    assert result.scene.world.values["distance"].canonical_unit == "m"
    assert result.scene.world.values["speed"].canonical_value == pytest.approx(4 / 3.6)
    assert result.scene.world.values["start_time"].value == "06:45"
    assert [item.label for item in result.scene.objects] == ["Lan", "Nhà", "Trường"]
    assert "07:03" not in result.model_dump_json()


def test_semantic_model_rejects_duplicate_and_unknown_references() -> None:
    with pytest.raises(ValidationError, match="unknown IDs"):
        MathSemanticModel.model_validate(
            {
                "grade": 5,
                "domain": "motion",
                "problem_type": "distance_speed_time",
                "entities": [{"id": "person", "type": "person", "label": "Bạn nhỏ"}],
                "relations": [
                    {
                        "id": "move",
                        "type": "motion",
                        "participants": {"subject": "person", "to": "missing_place"},
                    }
                ],
            }
        )


def test_uncertain_geometry_cannot_become_a_locked_constraint() -> None:
    with pytest.raises(ValidationError, match="cannot become a locked constraint"):
        SemanticConstraint.model_validate(
            {
                "id": "maybe_right",
                "type": "perpendicular",
                "target_ids": ["a", "b"],
                "evidence": {
                    "confidence": 0.61,
                    "status": "uncertain",
                    "source": "vision_inference",
                },
            }
        )


def test_constraint_evidence_reaches_the_renderer_scene() -> None:
    model = MathSemanticModel.model_validate(
        {
            "grade": 6,
            "domain": "geometry_2d",
            "problem_type": "triangle",
            "entities": [
                {"id": "point_a", "type": "point", "label": "A"},
                {"id": "point_b", "type": "point", "label": "B"},
            ],
            "constraints": [
                {
                    "id": "possible_right_angle",
                    "type": "perpendicular",
                    "target_ids": ["point_a", "point_b"],
                    "locked": False,
                    "evidence": {
                        "confidence": 0.8,
                        "status": "inferred",
                        "source": "vision_inference",
                    },
                }
            ],
        }
    )

    scene_constraint = MathLabFoundationService().plan(model).scene.constraints[0]

    assert scene_constraint.locked is False
    assert scene_constraint.evidence.status.value == "inferred"
    assert scene_constraint.evidence.source.value == "vision_inference"
    assert scene_constraint.evidence.confidence == pytest.approx(0.8)


def test_low_confidence_evidence_is_not_explicit() -> None:
    with pytest.raises(ValidationError, match="cannot be explicit"):
        Evidence(confidence=0.4, status="explicit", source="vision_ocr")


def test_unit_conversion_is_dimension_safe() -> None:
    assert convert(1.2, "km", "m") == pytest.approx(1200)
    assert convert(0.3, "hour", "minute") == pytest.approx(18)
    assert convert(4, "km/h", "m/s") == pytest.approx(4 / 3.6)
    canonical_value, canonical_unit = canonicalize(1, "liter")
    assert canonical_value == pytest.approx(0.001)
    assert canonical_unit == "m3"
    angle_value, angle_unit = canonicalize(80, "degree")
    assert angle_value == pytest.approx(80)
    assert angle_unit == "degree"
    with pytest.raises(UnitConversionError):
        convert(1, "kg", "m")


def test_angle_bisector_uses_exact_geometry_and_four_reveal_steps() -> None:
    model = MathSemanticModel.model_validate({
        "grade": 7,
        "domain": "geometry_2d",
        "problem_type": "angle_bisector",
        "source_text": "Cho góc xOy = 80°, Ot là tia phân giác. Số đo xOt bằng?",
        "quantities": [
            {"id": "whole_angle", "value": 80, "unit": "degree", "role": "angle", "label": "Góc xOy"},
        ],
        "unknowns": [
            {"id": "half_angle", "kind": "angle", "unit": "degree", "role": "result", "label": "Góc xOt"},
        ],
    })

    result = MathLabFoundationService().plan(model)

    assert [item.visualization for item in result.decisions] == [VisualizationId.GEOMETRY_2D]
    assert result.scene.visualizations[0].bindings["angle"] == ["whole_angle"]
    assert result.scene.world.values["whole_angle"].canonical_value == pytest.approx(80)
    assert result.scene.world.values["half_angle"].value is None
    assert [item.id for item in result.pedagogy.reveal_steps] == [
        "angle_rays", "angle_measure", "angle_bisector", "angle_half",
    ]


def test_semantic_quantities_reject_unsupported_units() -> None:
    with pytest.raises(ValidationError):
        MathSemanticModel.model_validate(
            {
                "grade": 5,
                "domain": "measurement",
                "problem_type": "length",
                "quantities": [{"id": "length", "value": 4, "unit": "parsec"}],
            }
        )


def test_teacher_selection_only_accepts_registered_compatible_visualizations() -> None:
    model = MathSemanticModel.model_validate(
        {
            "grade": 3,
            "domain": "fraction",
            "problem_type": "part_whole",
            "quantities": [
                {"id": "numerator", "value": 3},
                {"id": "denominator", "value": 4},
            ],
        }
    )
    request = MathLabPlanRequest(
        semantic_model=model,
        requested_visualizations=[VisualizationId.GEOMETRY_3D, VisualizationId.FRACTION],
    )
    result = MathLabFoundationService().plan(
        request.semantic_model,
        request.requested_visualizations,
    )
    assert [item.visualization for item in result.decisions] == [VisualizationId.FRACTION]
    assert result.warnings and "geometry_3d" in result.warnings[0]


def test_all_semantic_domains_have_a_registered_fallback() -> None:
    service = MathLabFoundationService()
    for grade in range(1, 10):
        for domain in MathDomain:
            result = service.plan(
                MathSemanticModel(
                    grade=grade,
                    domain=domain,
                    problem_type="foundation_fallback",
                )
            )
            assert result.scene.visualizations


def test_fraction_power_uses_dedicated_six_step_model_and_preserves_choices() -> None:
    model = MathSemanticModel.model_validate({
        "grade": 7,
        "domain": "algebra",
        "problem_type": "fraction_power",
        "source_text": "Kết quả (−2/5)³ là",
        "choices": ["A. 8/125", "B. 4/25", "C. -8/125", "D. 8/15"],
        "quantities": [
            {"id": "numerator", "value": -2, "role": "numerator"},
            {"id": "denominator", "value": 5, "role": "denominator"},
            {"id": "exponent", "value": 3, "role": "exponent"},
        ],
        "unknowns": [{"id": "result", "kind": "fraction", "role": "result"}],
    })

    result = MathLabFoundationService().plan(model)

    assert result.decisions[0].visualization == VisualizationId.POWER_MODEL
    assert result.scene.visualizations[0].type == VisualizationId.POWER_MODEL
    assert result.scene.metadata["choices"][2] == "C. -8/125"
    assert [item.id for item in result.pedagogy.reveal_steps] == [
        "power_read", "power_repeat", "power_sign", "power_parts",
        "power_magnitude", "power_result",
    ]


def test_average_per_person_uses_a_five_milestone_equal_share_model() -> None:
    model = MathSemanticModel.model_validate(
        {
            "grade": 4,
            "domain": "arithmetic",
            "problem_type": "average_per_person",
            "quantities": [
                {"id": "workers", "value": 25, "role": "count_initial", "label": "Số công nhân"},
                {"id": "month_1", "value": 954, "role": "count_change", "label": "Sản phẩm tháng thứ nhất"},
                {"id": "month_2", "value": 821, "role": "count_change", "label": "Sản phẩm tháng thứ hai"},
                {"id": "month_3", "value": 1350, "role": "count_change", "label": "Sản phẩm tháng thứ ba"},
            ],
            "unknowns": [{"id": "average", "kind": "number", "role": "result"}],
        }
    )

    result = MathLabFoundationService().plan(model)

    assert result.decisions[0].visualization == VisualizationId.BAR_MODEL
    assert result.scene.visualizations[0].type == VisualizationId.BAR_MODEL
    assert len(result.scene.steps) == 5
    assert [item.id for item in result.pedagogy.reveal_steps] == [
        "month_1", "month_2", "month_3", "equal_groups", "average_result"
    ]


def test_find_value_from_ratio_uses_four_equal_part_steps_not_a_number_line() -> None:
    model = MathSemanticModel.model_validate(
        {
            "grade": 4,
            "domain": "arithmetic",
            "problem_type": "find value from ratio",
            "quantities": [
                {"id": "boys", "value": 16, "role": "count_initial", "label": "Số học sinh nam"},
                {"id": "numerator", "value": 9, "role": "numerator", "label": "Tử số"},
                {"id": "denominator", "value": 8, "role": "denominator", "label": "Mẫu số"},
            ],
            "unknowns": [{"id": "girls", "kind": "count", "role": "result", "label": "Số học sinh nữ"}],
        }
    )

    result = MathLabFoundationService().plan(model)

    assert [item.visualization for item in result.decisions] == [VisualizationId.BAR_MODEL]
    assert [item.id for item in result.pedagogy.reveal_steps] == [
        "known_parts", "one_part", "target_parts", "ratio_result"
    ]
    assert len(result.scene.steps) == 4


def test_sequential_remainder_ratio_has_five_exact_bar_steps() -> None:
    model = MathSemanticModel.model_validate({
        "grade": 7,
        "domain": "ratio",
        "problem_type": "sequential_fraction_remainder_ratio",
        "source_text": "160kg gạo; ngày 1 bán 3/8; ngày 2 bán 1/4 phần còn lại.",
        "quantities": [
            {"id": "rice_total", "value": 160, "unit": "kg", "role": "mass"},
            {"id": "day_1_numerator", "value": 3, "role": "numerator"},
            {"id": "day_1_denominator", "value": 8, "role": "denominator"},
            {"id": "day_2_numerator", "value": 1, "role": "addend_numerator"},
            {"id": "day_2_denominator", "value": 4, "role": "addend_denominator"},
        ],
        "unknowns": [{"id": "day_ratio", "kind": "ratio", "role": "result"}],
    })

    result = MathLabFoundationService().plan(model)
    descriptor = result.scene.visualizations[0]

    assert [item.visualization for item in result.decisions] == [VisualizationId.BAR_MODEL]
    assert descriptor.bindings["mass"] == ["rice_total"]
    assert descriptor.bindings["addend_denominator"] == ["day_2_denominator"]
    assert result.scene.world.values["day_ratio"].value is None
    assert [item.id for item in result.pedagogy.reveal_steps] == [
        "rice_total_parts",
        "rice_day_one",
        "rice_repartition_remainder",
        "rice_day_two_three",
        "rice_ratio_reduce",
    ]
    assert len(result.scene.steps) == 5


def test_mixed_area_remainder_migrates_wrong_history_and_uses_generic_bar_strategy() -> None:
    source = (
        "Một khu đất rộng 10dam2 80m2, người ta sử dụng\n2\n5\n diện tích "
        "để làm nhà và\n1\n3\ndiện tích đất còn lại để trồng hoa, phần đất "
        "cuối cùng để làm chuồng trại chăn nuôi. Tính diện tích đất làm "
        "chuồng trại chăn nuôi?"
    )
    model = MathSemanticModel.model_validate({
        "grade": 6,
        "domain": "geometry_2d",
        "problem_type": "sequential_fraction_remainder_ratio",
        "source_text": source,
        "quantities": [
            {"id": "wrong_dam2", "value": 10, "unit": "kg", "role": "mass"},
            {"id": "wrong_m2", "value": 80, "unit": "kg", "role": "mass"},
        ],
        "unknowns": [{"id": "unknown_area", "kind": "area", "role": "result"}],
    })

    result = MathLabFoundationService().plan(model)
    descriptor = result.scene.visualizations[0]

    assert model.problem_type == "sequential_fraction_remainder_quantity"
    assert model.domain == MathDomain.RATIO
    assert [(item.role.value, item.value, item.unit) for item in model.quantities] == [
        ("area", 1000.0, "m2"),
        ("area", 80.0, "m2"),
        ("numerator", 2.0, "one"),
        ("denominator", 5.0, "one"),
        ("addend_numerator", 1.0, "one"),
        ("addend_denominator", 3.0, "one"),
    ]
    assert [item.visualization for item in result.decisions] == [VisualizationId.BAR_MODEL]
    assert descriptor.bindings["area"] == ["area_component_1", "area_component_2"]
    assert result.scene.world.values["area_component_1"].canonical_value == 1000
    assert result.scene.world.values["unknown_area"].value is None
    assert [item.id for item in result.pedagogy.reveal_steps] == [
        "remainder_normalize_total",
        "remainder_first_allocation",
        "remainder_new_whole",
        "remainder_second_allocation",
        "remainder_final_quantity",
    ]
    history_entry = MathLabHistoryEntry(
        id=uuid4(),
        created_at=datetime.now(timezone.utc),
        source_type="text",
        source_text=source,
        grade=6,
        domain="geometry_2d",
        problem_type="sequential_fraction_remainder_ratio",
        semantic_model=model,
    )
    assert history_entry.domain == MathDomain.RATIO
    assert history_entry.problem_type == "sequential_fraction_remainder_quantity"


def test_short_addition_history_recovers_operands_and_never_renders_zero_defaults() -> None:
    model = MathSemanticModel.model_validate({
        "grade": 1,
        "domain": "arithmetic",
        "problem_type": "addition_basic",
        "source_text": "4+3 = ?",
        "quantities": [],
        "unknowns": [{"id": "unknown_result", "kind": "number", "role": "result"}],
    })

    result = MathLabFoundationService().plan(model)

    assert [(item.role.value, item.value) for item in model.quantities] == [
        ("count_initial", 4.0),
        ("count_change", 3.0),
    ]
    assert [item.visualization for item in result.decisions] == [
        VisualizationId.OBJECT_GROUP,
        VisualizationId.NUMBER_LINE,
    ]
    assert model.relations[0].type == "part_whole"
    assert model.relations[0].participants["whole"] == "arithmetic_result"
    assert result.visual_plan.status == "ready"
    assert result.visual_plan.concepts[0].type.value == "part_whole"
    assert result.visual_plan.primary_renderer == VisualizationId.OBJECT_GROUP
    assert all(
        "unknown_not_preloaded" in stage.oracle_checks
        for stage in result.visual_plan.stages
    )
    assert result.scene.world.values["left_operand"].value == 4
    assert result.scene.world.values["right_operand"].value == 3
    assert result.scene.world.values["arithmetic_result"].value is None


def test_short_addition_without_printed_operands_abstains() -> None:
    model = MathSemanticModel.model_validate({
        "grade": 1,
        "domain": "arithmetic",
        "problem_type": "addition_basic",
        "source_text": "Hãy thực hiện phép cộng đã cho.",
        "quantities": [],
        "unknowns": [{"id": "unknown_result", "kind": "number", "role": "result"}],
    })

    result = MathLabFoundationService().plan(model)

    assert [item.visualization for item in result.decisions] == [VisualizationId.UNSUPPORTED]
    assert result.visual_plan.status == "blocked"


def test_variable_people_work_rate_uses_conserved_worker_day_bar_model() -> None:
    model = MathSemanticModel.model_validate({
        "grade": 5,
        "domain": "ratio",
        "problem_type": "work_rate_with_variable_people",
        "source_text": "Tổ 8 người làm 6 ngày, sau đó thêm 4 người; sức làm việc như nhau.",
        "quantities": [
            {"id": "initial_workers", "value": 8, "role": "count_initial", "label": "Số người ban đầu"},
            {"id": "planned_days", "value": 6, "unit": "day", "role": "duration", "label": "Số ngày dự định"},
            {"id": "added_workers", "value": 4, "role": "count_change", "label": "Số người bổ sung"},
        ],
        "unknowns": [{"id": "new_days", "kind": "duration", "unit": "day", "role": "result"}],
    })

    result = MathLabFoundationService().plan(model)
    descriptor = result.scene.visualizations[0]

    # Compatibility migration: previously stored work-rate entries may still
    # carry the physical `day` unit, while older browser bundles only know the
    # original unit allow-list.
    assert model.quantities[1].unit == "one"
    assert model.unknowns[0].unit == "one"
    assert [item.visualization for item in result.decisions] == [VisualizationId.BAR_MODEL]
    assert descriptor.bindings["count_initial"] == ["initial_workers"]
    assert descriptor.bindings["duration"] == ["planned_days"]
    assert descriptor.bindings["count_change"] == ["added_workers"]
    assert result.scene.world.values["planned_days"].canonical_value == 6
    assert result.scene.world.values["planned_days"].canonical_unit == "one"
    assert result.scene.world.values["new_days"].value is None
    assert [item.id for item in result.pedagogy.reveal_steps] == [
        "work_initial_plan",
        "work_total_invariant",
        "work_new_team",
        "work_redistribute",
        "work_result",
    ]
    assert len(result.scene.steps) == 5


def test_legacy_work_rate_history_recovers_printed_operands_without_answer_leakage() -> None:
    model = MathSemanticModel.model_validate({
        "grade": 5,
        "domain": "probability",
        "problem_type": "work_rate_with_variable_people",
        "source_text": (
            "Một tổ gồm 8 người dự định làm xong một con đường trong 6 ngày "
            "nhưng sau đó tổ được bổ sung thêm 4 người. Hỏi con đường được làm "
            "xong trong bao nhiêu ngày biết sức làm việc của mỗi người như nhau."
        ),
        "quantities": [],
        "unknowns": [{
            "id": "legacy_unknown",
            "kind": "duration",
            "role": "result",
        }],
    })

    result = MathLabFoundationService().plan(model)

    assert model.domain == MathDomain.RATIO
    assert [(item.role.value, item.value, item.unit) for item in model.quantities] == [
        ("count_initial", 8.0, "one"),
        ("duration", 6.0, "one"),
        ("count_change", 4.0, "one"),
    ]
    assert model.unknowns[0].unit == "one"
    assert all(item.role != MathQuantityRole.RESULT for item in model.quantities)
    assert result.decisions[0].visualization == VisualizationId.BAR_MODEL


def test_reverse_discount_checkout_has_six_exact_percent_steps() -> None:
    model = MathSemanticModel.model_validate({
        "grade": 7,
        "domain": "ratio",
        "problem_type": "multi_item_reverse_discount",
        "source_text": "Ba món hàng giảm giá, tổng trả 692 500 đồng; tìm giá gốc món ba.",
        "quantities": [
            {"id": "price_1", "value": 125000, "role": "count_initial", "label": "Giá gốc món 1"},
            {"id": "price_2", "value": 300000, "role": "count_initial", "label": "Giá gốc món 2"},
            {"id": "discount_1", "value": 30, "role": "probability", "label": "Giảm món 1"},
            {"id": "discount_2", "value": 15, "role": "probability", "label": "Giảm món 2"},
            {"id": "discount_3", "value": 12.5, "role": "probability", "label": "Giảm món 3"},
            {"id": "paid_total", "value": 692500, "role": "total", "label": "Tổng đã trả"},
        ],
        "unknowns": [{"id": "price_3", "kind": "money", "role": "result", "label": "Giá gốc món 3"}],
    })

    result = MathLabFoundationService().plan(model)

    assert [item.visualization for item in result.decisions] == [VisualizationId.PERCENT_GRID]
    assert result.scene.visualizations[0].bindings["count_initial"] == ["price_1", "price_2"]
    assert result.scene.visualizations[0].bindings["probability"] == ["discount_1", "discount_2", "discount_3"]
    assert [item.id for item in result.pedagogy.reveal_steps] == [
        "discount_item_one",
        "discount_item_two",
        "discount_known_total",
        "discount_third_paid",
        "discount_third_rate",
        "discount_original",
    ]
    assert len(result.scene.steps) == 6


def test_quantity_bindings_do_not_include_entities_with_the_same_role() -> None:
    model = MathSemanticModel.model_validate({
        "grade": 7,
        "domain": "ratio",
        "problem_type": "multi_item_reverse_discount",
        "entities": [
            {"id": "price_list", "type": "list", "label": "Các giá gốc", "role": "count_initial"},
            {"id": "discount_list", "type": "list", "label": "Các mức giảm", "role": "probability"},
            {"id": "checkout", "type": "number", "label": "Tổng thanh toán", "role": "total"},
        ],
        "quantities": [
            {"id": "price_1", "value": 125000, "role": "count_initial"},
            {"id": "price_2", "value": 300000, "role": "count_initial"},
            {"id": "discount_1", "value": 30, "role": "probability"},
            {"id": "discount_2", "value": 15, "role": "probability"},
            {"id": "discount_3", "value": 12.5, "role": "probability"},
            {"id": "paid_total", "value": 692500, "role": "total"},
        ],
        "unknowns": [{"id": "price_3", "kind": "money", "role": "result"}],
    })

    descriptor = MathLabFoundationService().plan(model).scene.visualizations[0]

    assert descriptor.bindings["count_initial"] == ["price_1", "price_2"]
    assert descriptor.bindings["probability"] == ["discount_1", "discount_2", "discount_3"]
    assert descriptor.bindings["total"] == ["paid_total"]
    assert descriptor.bindings["entity_count_initial"] == ["price_list"]
    assert descriptor.bindings["entity_probability"] == ["discount_list"]
    assert descriptor.bindings["entity_total"] == ["checkout"]


def test_incomplete_grouping_abstains_before_renderer_receives_empty_operands() -> None:
    model = MathSemanticModel.model_validate({
        "grade": 1,
        "domain": "arithmetic",
        "problem_type": "multiplication_basic",
        "unknowns": [{"id": "answer", "kind": "number", "role": "result"}],
    })

    result = MathLabFoundationService().plan(model)

    assert result.decisions[0].visualization == VisualizationId.UNSUPPORTED


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        ("38475*9374", VisualizationId.COLUMN_ALGORITHM),
        ("993948 chia 7", VisualizationId.COLUMN_ALGORITHM),
        ("92!", VisualizationId.EXPRESSION_TREE),
    ],
)
def test_large_typed_operations_choose_compact_visual_algorithms(
    source: str,
    expected: VisualizationId,
) -> None:
    model = MathSemanticModel.model_validate({
        "grade": 9,
        "domain": "unknown",
        "problem_type": "provider_guess",
        "source_text": source,
    })

    result = MathLabFoundationService().plan(model)

    assert result.semantic_model.source_text == source
    assert result.decisions[0].visualization == expected
    assert result.scene.visualizations[0].type == expected


@pytest.mark.parametrize(
    ("domain", "problem_type", "quantities", "expected_visualization", "expected_steps"),
    [
        (
            "fraction",
            "fraction_addition",
            [
                {"id": "n1", "value": 1, "role": "numerator"},
                {"id": "d1", "value": 2, "role": "denominator"},
                {"id": "n2", "value": 1, "role": "addend_numerator"},
                {"id": "d2", "value": 3, "role": "addend_denominator"},
            ],
            VisualizationId.FRACTION,
            ["fraction_read", "fraction_common_parts", "fraction_rewrite", "fraction_combine", "fraction_simplify"],
        ),
        (
            "fraction",
            "fraction_multiplication",
            [
                {"id": "n1", "value": 2, "role": "numerator"},
                {"id": "d1", "value": 3, "role": "denominator"},
                {"id": "n2", "value": 3, "role": "addend_numerator"},
                {"id": "d2", "value": 4, "role": "addend_denominator"},
            ],
            VisualizationId.FRACTION,
            ["fraction_factor_one", "fraction_factor_two", "fraction_intersection", "fraction_product"],
        ),
        (
            "algebra",
            "linear_equation",
            [
                {"id": "a", "value": 2, "role": "coefficient"},
                {"id": "b", "value": 3, "role": "constant"},
                {"id": "c", "value": 9, "role": "result"},
            ],
            VisualizationId.BALANCE,
            ["balance_observe", "balance_inverse", "balance_divide", "balance_solution"],
        ),
        (
            "algebra",
            "binomial_expansion",
            [{"id": "a", "value": 3}, {"id": "b", "value": 2}],
            VisualizationId.BAR_MODEL,
            ["area_whole", "area_split", "area_terms", "area_like_terms", "area_identity"],
        ),
        (
            "coordinate",
            "linear_function",
            [
                {"id": "m", "value": 2, "role": "coefficient"},
                {"id": "b", "value": 1, "role": "constant"},
            ],
            VisualizationId.COORDINATE_GRAPH,
            ["axes", "intercept", "slope", "function_line"],
        ),
        (
            "algebra",
            "linear_function",
            [
                {"id": "m", "value": 2, "role": "coefficient"},
                {"id": "b", "value": 1, "role": "constant"},
            ],
            VisualizationId.COORDINATE_GRAPH,
            ["axes", "intercept", "slope", "function_line"],
        ),
        (
            "geometry_3d",
            "cuboid_volume",
            [
                {"id": "length", "value": 4, "unit": "cm", "role": "length"},
                {"id": "width", "value": 3, "unit": "cm", "role": "width"},
                {"id": "height", "value": 2, "unit": "cm", "role": "height"},
            ],
            VisualizationId.GEOMETRY_3D,
            ["xyz_base", "xyz_area", "xyz_height", "xyz_volume"],
        ),
    ],
)
def test_visual_reasoning_families_have_operation_specific_steps(
    domain: str,
    problem_type: str,
    quantities: list[dict],
    expected_visualization: VisualizationId,
    expected_steps: list[str],
) -> None:
    model = MathSemanticModel.model_validate({
        "grade": 7,
        "domain": domain,
        "problem_type": problem_type,
        "quantities": quantities,
    })

    result = MathLabFoundationService().plan(model)

    assert result.decisions[0].visualization == expected_visualization
    assert [step.id for step in result.pedagogy.reveal_steps] == expected_steps
    assert len(result.scene.steps) == len(expected_steps)
    descriptor = result.scene.visualizations[0]
    for quantity in model.quantities:
        if quantity.role:
            assert quantity.id in descriptor.bindings[quantity.role.value]


def test_math_lab_route_is_teacher_guarded_and_published() -> None:
    from app.api.math_lab import router
    from app.dependencies import require_teacher
    from app.main import create_app

    route = next(item for item in router.routes if item.path == "/math-lab/plan")
    dependencies = {item.call for item in route.dependant.dependencies}
    assert require_teacher in dependencies
    assert "/api/v1/math-lab/plan" in create_app().openapi()["paths"]
