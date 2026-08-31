"""Permanent regressions for the general linear family.

Before the canonicalizer, each printed shape needed its own regular expression.
``3x+y=z`` matched none of them, fell through to the vision model and reached
teachers as an ``unsupported`` card. These tests lock the structural rules the
repair depends on, not the specific strings that exposed it.
"""

from __future__ import annotations

import pytest

from app.core.config import Settings
from app.schemas.math_lab import MathQuantityRole
from app.schemas.math_lab_input import canonical_problem_type, canonicalize_typed_math
from app.schemas.math_lab_linear import (
    classify_linear,
    format_canonical,
    parse_rational_domain,
    parse_linear_form,
    parse_linear_system,
    sample_plane_points,
)
from app.schemas.math_lab_text import (
    extract_angle_of_depression,
    extract_binary_fraction,
    extract_oblique_triangle_altitude,
    extract_perpendicular_diagonal_parallelogram,
)
from app.schemas.math_lab_nonlinear import (
    parse_cubic_equation,
    parse_quadratic_equation,
    parse_quadratic_surface,
)
from app.schemas.math_lab_equations import (
    parse_absolute_value_equation,
    parse_biquadratic_equation,
    parse_fractional_linear_equation,
    parse_radical_equation,
    parse_rational_equation,
)
from app.services.math_lab.analyzer import MathProblemAnalyzer
from app.services.math_lab.foundation import MathLabFoundationService


class RefusingProvider:
    """Any call here means the deterministic grammar failed to claim the input."""

    name = "refusing-provider"
    model = "refusing-model"

    async def available(self) -> bool:
        return False

    async def analyze_text(self, _text, _grade_hint):
        raise AssertionError("A printed linear input must not need the vision model")

    async def analyze_image(self, _image, _media_type, _grade_hint):
        raise AssertionError("A printed linear input must not need the vision model")


def _analyzer() -> MathProblemAnalyzer:
    return MathProblemAnalyzer(Settings(), provider=RefusingProvider())


# --- canonicalization ------------------------------------------------------


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("3x+y=z", "3x + y - z = 0"),
        ("3x + y = z", "3x + y - z = 0"),
        ("z = 3x + y", "-3x - y + z = 0"),
        ("x+y=z", "x + y - z = 0"),
        ("y=2x+1", "-2x + y = 1"),
        ("2x+y=1", "2x + y = 1"),
        ("3x+y+z=6", "3x + y + z = 6"),
        ("-2x+4y-z=8", "-2x + 4y - z = 8"),
        ("2x+3=9", "2x = 6"),
        ("5x = 2x + 9", "3x = 9"),
        ("0.5x + 2 = 4", "1/2x = 2"),
    ],
)
def test_both_sides_are_collected_into_one_canonical_form(text: str, expected: str) -> None:
    form = parse_linear_form(text)
    assert form is not None
    assert format_canonical(form) == expected


@pytest.mark.parametrize(
    "text",
    [
        "vẽ đồ thị y = 2x + 1",
        "Vẽ đồ thị hàm số y = 2x + 1",
        "ve do thi y = 2x + 1",
        "  Y = 2X + 1  ",
        "y=2·x+1",
        "y = 2*x + 1",
    ],
)
def test_accents_spacing_and_symbols_reach_the_same_line(text: str) -> None:
    """Accented, unaccented, spaced and symbolic variants share one family."""

    form = parse_linear_form(text)
    assert form is not None
    assert format_canonical(form) == "-2x + y = 1"


@pytest.mark.parametrize(
    "text",
    [
        "x^2 + 1 = 0",
        "x² = 4",
        "2/x = 4",
        "xy = 6",
        "√x = 2",
        "Trong bãi có 58 chiếc xe tải. Có 38 chiếc xe rời bãi.",
        "Tính 4 + 3",
        "(1+1)x2",
        "12",
    ],
)
def test_non_linear_and_non_algebraic_input_is_refused_without_crashing(text: str) -> None:
    assert classify_linear(text) is None or classify_linear(text).kind not in {
        "expression_one_variable",
        "equation_one_variable",
        "equation_two_variables",
        "equation_three_variables",
    }


@pytest.mark.parametrize(
    ("text", "kind"),
    [
        ("2x+1", "expression_one_variable"),
        ("2x+3=9", "equation_one_variable"),
        ("2x+y=1", "equation_two_variables"),
        ("y=2x+1", "equation_two_variables"),
        ("3x+y=z", "equation_three_variables"),
        ("x+y=z", "equation_three_variables"),
        ("3x+y+z=6", "equation_three_variables"),
        ("-2x+4y-z=8", "equation_three_variables"),
        ("x+y=3; x-y=1", "system_two_variables"),
        ("4x+5y+z=0 và 6y=9 và 4x+9z=0", "system_three_variables"),
        ("x=x", "identity"),
        ("x+1=x+2", "contradiction"),
    ],
)
def test_structure_alone_decides_the_family(text: str, kind: str) -> None:
    classification = classify_linear(text)
    assert classification is not None
    assert classification.kind == kind


@pytest.mark.parametrize(
    ("text", "state", "intersection"),
    [
        ("x+y=3; x-y=1", "intersecting", (2.0, 1.0)),
        ("4x+y=9 và 5y=10", "intersecting", (1.75, 2.0)),
        ("2x+y=5 và 4x+2y=10", "coincident", None),
        ("2x+y=5 va 4x+2y=3", "parallel", None),
        ("x + y = 3\nx - y = 1", "intersecting", (2.0, 1.0)),
    ],
)
def test_two_equations_report_the_state_they_actually_have(
    text: str,
    state: str,
    intersection: tuple[float, float] | None,
) -> None:
    system = parse_linear_system(text)
    assert system is not None
    assert system.state == state
    if intersection is None:
        assert system.intersection is None
    else:
        assert system.intersection == pytest.approx(intersection)


@pytest.mark.parametrize(
    ("text", "state", "solution"),
    [
        (
            "4x +5y +z=0 và 6y=9 và 4x+9z=0",
            "unique",
            ("-135/64", "3/2", "15/16"),
        ),
        (
            "4x+5y+z=0; 6y=9; 4x+9z=0",
            "unique",
            ("-135/64", "3/2", "15/16"),
        ),
        (
            "{ 4x+5y+z=0\n6y=9\n4x+9z=0 }",
            "unique",
            ("-135/64", "3/2", "15/16"),
        ),
        (
            "4x+5y+z=0, 6y=9, 4x+9z=0",
            "unique",
            ("-135/64", "3/2", "15/16"),
        ),
        ("x+y+z=3; 2x+2y+2z=6", "infinite", None),
        ("x+y+z=3; x+y+z=4", "inconsistent", None),
    ],
)
def test_three_variable_system_uses_rank_and_exact_row_reduction(
    text: str,
    state: str,
    solution: tuple[str, str, str] | None,
) -> None:
    system = parse_linear_system(text)
    assert system is not None
    assert system.variables == ("x", "y", "z")
    assert system.state == state
    assert system.solution_exact == solution
    assert system.elimination_steps
    assert all(len(row) == 4 for step in system.elimination_steps for row in step["matrix"])
    if system.solution is not None:
        assignment = dict(zip(system.variables, system.solution, strict=True))
        assert all(form.satisfies(assignment) for form in system.forms)


@pytest.mark.parametrize(
    ("text", "coefficients", "constant"),
    [
        ("3x+y=z", (3.0, 1.0, -1.0), 0.0),
        ("x+y=z", (1.0, 1.0, -1.0), 0.0),
        ("3x+y+z=6", (3.0, 1.0, 1.0), 6.0),
        ("-2x+4y-z=8", (-2.0, 4.0, -1.0), 8.0),
    ],
)
def test_every_generated_plane_point_satisfies_its_equation(
    text: str,
    coefficients: tuple[float, float, float],
    constant: float,
) -> None:
    form = parse_linear_form(text)
    assert form is not None
    assert tuple(form.coefficient(name) for name in ("x", "y", "z")) == coefficients
    assert form.constant == pytest.approx(constant)
    points = sample_plane_points(form, ("x", "y", "z"))
    assert len(points) >= 3
    for x, y, z in points:
        assert coefficients[0] * x + coefficients[1] * y + coefficients[2] * z == pytest.approx(constant)


# --- analyzer and plan -----------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("stem", "grade", "problem_type", "renderer"),
    [
        ("2x+1", 7, "polynomial_evaluate_reorder", "algebra_tiles"),
        ("2x + 1", 7, "polynomial_evaluate_reorder", "algebra_tiles"),
        ("2x+3=9", 8, "linear_equation", "balance"),
        ("Giải phương trình 2x + 3 = 9.", 8, "linear_equation", "balance"),
        ("5x = 2x + 9", 8, "linear_equation", "balance"),
        ("2x+y=1", 8, "linear_equation_two_variables_graph", "coordinate_graph"),
        ("y=2x+1", 8, "linear_equation_two_variables_graph", "coordinate_graph"),
        ("vẽ đồ thị y = 2x + 1", 8, "linear_equation_two_variables_graph", "coordinate_graph"),
        ("3x+y=z", 9, "linear_equation_three_variables_plane", "geometry_3d"),
        ("3x + y = z", 9, "linear_equation_three_variables_plane", "geometry_3d"),
        ("x+y=z", 9, "linear_equation_three_variables_plane", "geometry_3d"),
        ("3x+y+z=6", 9, "linear_equation_three_variables_plane", "geometry_3d"),
        ("-2x+4y-z=8", 9, "linear_equation_three_variables_plane", "geometry_3d"),
        ("x+y=3; x-y=1", 9, "linear_system_two_variables_graph", "coordinate_graph"),
        ("2x+y=5 và 4x+2y=10", 9, "linear_system_two_variables_graph", "coordinate_graph"),
        ("2x+y=5 và 4x+2y=3", 9, "linear_system_two_variables_graph", "coordinate_graph"),
        ("4x+y=9 và 5y=10", 7, "linear_system_two_variables_graph", "coordinate_graph"),
        ("4x +5y +z=0 và 6y=9 và 4x+9z=0", 9, "linear_system_three_variables_planes", "geometry_3d"),
    ],
)
async def test_printed_linear_input_reaches_a_ready_scene_without_the_vlm(
    stem: str,
    grade: int,
    problem_type: str,
    renderer: str,
) -> None:
    result = await _analyzer().analyze_text(stem, grade)
    model = result.questions[0].semantic_model
    plan = MathLabFoundationService().plan(model)

    assert model.problem_type == problem_type
    assert model.quantities, "a ready scene never has empty required quantities"
    assert plan.decisions[0].visualization.value == renderer
    assert plan.visual_plan.status == "ready"
    assert len(plan.pedagogy.reveal_steps) >= 3
    # Every reveal step must name a distinct transformation, not repeat one.
    step_ids = [step.id for step in plan.pedagogy.reveal_steps]
    assert len(set(step_ids)) == len(step_ids)


@pytest.mark.asyncio
async def test_three_variable_plane_through_origin_keeps_the_right_side_at_zero() -> None:
    result = await _analyzer().analyze_text("3x+y=z", 9)
    model = result.questions[0].semantic_model
    coefficients = [
        item.value for item in model.quantities if item.role == MathQuantityRole.COEFFICIENT
    ]
    constants = [
        item.value for item in model.quantities if item.role == MathQuantityRole.CONSTANT
    ]
    assert coefficients == [3.0, 1.0, -1.0]
    assert constants == [0.0]
    # The equation has infinitely many solutions, so what is sought is the
    # plane of solutions -- never a unique value for x, y or z.
    assert [unknown.kind for unknown in model.unknowns] == ["plane"]
    assert all(unknown.role != MathQuantityRole.VARIABLE for unknown in model.unknowns)

    plan = MathLabFoundationService().plan(model)
    assert plan.decisions[0].visualization.value == "geometry_3d"
    goals = " ".join(step.goal for step in plan.pedagogy.reveal_steps)
    assert "gốc" in goals
    assert "vô số nghiệm" in goals
    assert "giao điểm với từng trục" not in goals


@pytest.mark.asyncio
async def test_system_carries_three_operands_per_equation() -> None:
    result = await _analyzer().analyze_text("x+y=3; x-y=1", 9)
    model = result.questions[0].semantic_model
    coefficients = [
        item.value for item in model.quantities if item.role == MathQuantityRole.COEFFICIENT
    ]
    constants = [
        item.value for item in model.quantities if item.role == MathQuantityRole.CONSTANT
    ]
    assert coefficients == [1.0, 1.0, 1.0, -1.0]
    assert constants == [3.0, 1.0]
    relation = model.relations[0]
    assert relation.type == "linear_system"
    assert relation.parameters["state"] == "intersecting"


@pytest.mark.asyncio
async def test_three_variable_system_keeps_all_equations_and_verified_solution() -> None:
    stem = "4x +5y +z=0 và 6y=9 và 4x+9z=0"
    result = await _analyzer().analyze_text(stem, 9)
    model = result.questions[0].semantic_model
    assert model.source_text == stem
    assert model.problem_type == "linear_system_three_variables_planes"
    assert len(model.quantities) == 12
    relation = model.relations[0]
    assert relation.parameters["canonical_forms"] == [
        "4x + 5y + z = 0",
        "6y = 9",
        "4x + 9z = 0",
    ]
    assert relation.parameters["solution_exact"] == ["-135/64", "3/2", "15/16"]
    solution = dict(zip(("x", "y", "z"), relation.parameters["solution"], strict=True))
    parsed = parse_linear_system(stem)
    assert parsed is not None
    assert all(form.satisfies(solution) for form in parsed.forms)

    plan = MathLabFoundationService().plan(model)
    assert plan.decisions[0].visualization.value == "geometry_3d"
    assert plan.visual_plan.status == "ready"
    assert [step.id for step in plan.pedagogy.reveal_steps] == [
        "system3_read",
        "system3_matrix",
        "system3_eliminate",
        "system3_planes",
        "system3_conclude",
        "system3_check",
    ]


@pytest.mark.asyncio
@pytest.mark.parametrize("stem", ["x=x", "x+1=x+2", "x + 1 = x + 1"])
async def test_degenerate_statements_ask_for_clarification_instead_of_failing(stem: str) -> None:
    result = await _analyzer().analyze_text(stem, 8)
    model = result.questions[0].semantic_model
    assert model.problem_type in {"linear_identity", "linear_contradiction"}

    plan = MathLabFoundationService().plan(model)
    decision = plan.decisions[0]
    assert decision.visualization.value == "unsupported"
    # A teacher reads this sentence, so it stays Vietnamese and free of engine
    # vocabulary.
    lowered = decision.reason.lower()
    for internal in ("renderer", "schema", "semantic", "payload", "backend"):
        assert internal not in lowered


@pytest.mark.asyncio
async def test_answer_is_never_copied_into_the_printed_givens() -> None:
    """``2x + 3 = 9`` must keep 2, 3 and 9 only; ``x = 3`` is not a given."""

    result = await _analyzer().analyze_text("2x+3=9", 8)
    model = result.questions[0].semantic_model
    values = sorted(item.value for item in model.quantities if item.value is not None)
    assert values == [2.0, 3.0, 9.0]
    assert [unknown.role for unknown in model.unknowns] == [MathQuantityRole.VARIABLE]


@pytest.mark.asyncio
async def test_a_fraction_of_the_remainder_is_not_read_as_whole_number_subtraction() -> None:
    """The numerator of ``3/4`` must never become the amount removed.

    The primary word-arithmetic grammar used to match ``bán 3/4 phần còn lại``
    on the digit 3, relabel the question as ``subtraction_basic`` and show a
    confident subtraction scene for a two-stage fraction problem.
    """

    stem = (
        "Một kho có 352 kg ngũ cốc. Ngày 1 bán 5/8 toàn bộ, ngày 2 bán 3/4 phần còn lại. "
        "Hỏi số ngũ cốc còn lại là bao nhiêu ki-lô-gam?"
    )
    from app.schemas.math_lab_text import extract_primary_word_arithmetic

    assert extract_primary_word_arithmetic(stem) is None


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("3(x+2)-5=2x+7", "x = 6"),
        ("2(x-1)=x+4", "x = 6"),
        ("-2(3x-1)=8", "-6x = 6"),
        ("5-(x+2)=1", "-x = -2"),
        ("2(3(x+1))=4", "6x = -2"),
        ("Tìm x biết 5(x + 2) - 10 = x + 32.", "4x = 32"),
        ("Phá ngoặc rồi giải phương trình 4(x + 9) - 4 = x + 68.", "3x = 36"),
    ],
)
def test_brackets_are_distributed_before_the_sides_are_collected(text: str, expected: str) -> None:
    form = parse_linear_form(text)
    assert form is not None
    assert format_canonical(form) == expected


@pytest.mark.parametrize(
    "text",
    [
        "x(x+1)=0",
        "(x+1)(x+2)=0",
        "2/x = 4",
        "xy = 6",
        "√x = 2",
        "x^2 + 1 = 0",
        "x² = 4",
        # A blank is an operand the learner supplies, not an absent term.
        "Điền số thích hợp: ? + 6 = 12.",
        "? + 6 = 12",
        "5 + _ = 9",
        # Prose that merely contains numbers must never become algebra.
        "Có 58 xe tải. Có 38 xe rời bãi. Còn lại?",
        "Lan có 5 quả táo, mẹ cho thêm 3 quả. Hỏi Lan có tất cả bao nhiêu quả táo?",
        "Đặt tính rồi tính: 543 × 87.",
        "Tam giác ABC vuông tại A, AB = 3 cm, AC = 4 cm. Tính độ dài BC.",
        "Một ô tô đi trong 5 giờ được 225 km. Ô tô đó đi trong 8 giờ được quãng đường là bao nhiêu",
        # A measured quantity is not a term: "12 m" once parsed as 12·m.
        "Dựng hai bán kính thẳng hàng của đường tròn tâm I, bán kính 12 m.",
        "Hình tròn tâm O có bán kính 6 cm. Tính diện tích hình tròn.",
        # Two fractions plus a percentage is a mixed expression, not a pair.
        "Tính giá trị biểu thức: 5/6 + 6/7 × 75%.",
    ],
)
def test_the_word_scan_never_invents_an_equation_from_prose(text: str) -> None:
    """Dropping a leading word must not drop mathematics with it.

    A character-level scan once restarted "2/x = 4" at "x = 4" and
    "x^2 + 1 = 0" at "+ 1 = 0", converting explicitly refused input into a
    confident linear scene.
    """

    assert classify_linear(text) is None


@pytest.mark.asyncio
async def test_a_bracketed_equation_is_its_own_family_with_visible_expansion() -> None:
    result = await _analyzer().analyze_text("3(x+2)-5=2x+7", 8)
    model = result.questions[0].semantic_model
    assert model.problem_type == "compound_linear_equation"

    stages = model.relations[0].parameters["stages"]
    assert len(stages) == 3
    # Every stage must change something; a repeated line is not a step.
    assert len({stage.replace(" ", "") for stage in stages}) == 3
    assert "(" in stages[0] and "(" not in stages[1]

    plan = MathLabFoundationService().plan(model)
    assert plan.decisions[0].visualization.value == "balance"
    assert plan.visual_plan.status == "ready"
    assert any("ngoặc" in step.goal for step in plan.pedagogy.reveal_steps)


@pytest.mark.asyncio
async def test_a_vietnamese_lead_in_does_not_turn_a_simple_equation_into_a_compound_one() -> None:
    result = await _analyzer().analyze_text("Giải phương trình 2x + 3 = 9.", 8)
    model = result.questions[0].semantic_model
    assert model.problem_type == "linear_equation"


# --- right triangles ------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("stem", "problem_type", "known"),
    [
        (
            "Hãy giải tam giác ABC vuông tại A. Biết AB = 5 cm, BC = 13 cm. (Góc làm tròn đến phút).",
            "right_triangle_solution",
            [5.0, 13.0],
        ),
        (
            "Cho tam giác ABC vuông tại A có AB = 6 cm, BC = 10 cm. Giải tam giác ABC.",
            "right_triangle_solution",
            [6.0, 10.0],
        ),
        (
            "Cho tam giác MNP vuông tại N có MN = 6 dm, MP = 10 dm. Giải tam giác MNP.",
            "right_triangle_solution",
            [6.0, 10.0],
        ),
        # Two legs with only the hypotenuse asked stays the narrower family.
        (
            "Tam giác ABC vuông tại A, AB = 3 cm, AC = 4 cm. Tính độ dài BC.",
            "right_triangle_hypotenuse",
            [3.0, 4.0],
        ),
    ],
)
async def test_solving_a_right_triangle_keeps_both_printed_sides(
    stem: str,
    problem_type: str,
    known: list[float],
) -> None:
    """"Giải tam giác" gives a side and the hypotenuse, not two legs.

    The old grammar only understood "two legs, find the hypotenuse", so this
    ordinary grade-9 instruction lost both operands and the lab showed a
    "not enough data" card for a fully specified question.
    """

    result = await _analyzer().analyze_text(stem, 9)
    model = result.questions[0].semantic_model
    assert model.problem_type == problem_type
    assert sorted(item.value for item in model.quantities) == sorted(known)

    plan = MathLabFoundationService().plan(model)
    assert plan.decisions[0].visualization.value == "geometry_2d"
    assert plan.visual_plan.status == "ready"
    assert len(plan.pedagogy.reveal_steps) >= 3


@pytest.mark.asyncio
async def test_solving_a_right_triangle_asks_for_the_leg_and_both_acute_angles() -> None:
    result = await _analyzer().analyze_text(
        "Hãy giải tam giác ABC vuông tại A. Biết AB = 5 cm, BC = 13 cm. (Góc làm tròn đến phút).",
        9,
    )
    model = result.questions[0].semantic_model
    kinds = sorted(unknown.kind for unknown in model.unknowns)
    assert kinds == ["angle", "angle", "length"]

    relation = next(item for item in model.relations if item.type == "right_triangle")
    # Which side is the hypotenuse decides whether the third side comes from a
    # sum or a difference of squares, so it travels with the scene.
    assert relation.parameters["hypotenuse"] == "BC"
    assert relation.parameters["known_sides"] == {"AB": 5.0, "BC": 13.0}
    assert relation.parameters["round_to_minute"] is True
    # No angle or missing length may be presented as a printed given.
    assert all(item.role != MathQuantityRole.ANGLE for item in model.quantities)
    assert 12.0 not in [item.value for item in model.quantities]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "stem",
    [
        "Cho tam giác ABC vuông tại A có AB = 5 cm và góc B = 40 độ. Giải tam giác ABC.",
        "Tam giác ABC vuông tại A, BC = 10 cm, góc C = 30°. Tính AB và AC.",
    ],
)
async def test_one_side_and_one_acute_angle_also_determine_the_triangle(stem: str) -> None:
    """A side with an acute angle is as complete as two sides.

    Grade-9 papers give this pair far more often than two sides, and it is
    solved by the trigonometric ratios rather than by Pythagoras.
    """

    result = await _analyzer().analyze_text(stem, 9)
    model = result.questions[0].semantic_model
    assert model.problem_type == "right_triangle_solution"
    roles = {item.role for item in model.quantities}
    assert MathQuantityRole.LENGTH in roles
    assert MathQuantityRole.ANGLE in roles

    relation = next(item for item in model.relations if item.type == "right_triangle")
    assert relation.parameters["known_angles"]
    assert len(relation.parameters["known_sides"]) == 1

    plan = MathLabFoundationService().plan(model)
    assert plan.decisions[0].visualization.value == "geometry_2d"
    assert plan.visual_plan.status == "ready"


# --- grade-9 trigonometric geometry --------------------------------------


def test_the_three_trigonometric_grammars_copy_only_printed_measurements() -> None:
    lighthouse = extract_angle_of_depression(
        "Đài hải đăng cao 149 m, góc nghiêng xuống đất là 27°. "
        "Hỏi tàu cách chân hải đăng là bao nhiêu mét?"
    )
    assert lighthouse is not None
    assert (lighthouse.height, lighthouse.angle, lighthouse.unit) == (149.0, 27.0, "m")

    lighthouse_from_to = extract_angle_of_depression(
        "Một ngọn hải đăng cao 149 m. Từ đỉnh nhìn xuống một chiếc thuyền "
        "với góc hạ 27°. Tính khoảng cách từ thuyền đến chân hải đăng."
    )
    assert lighthouse_from_to is not None
    assert (lighthouse_from_to.height, lighthouse_from_to.angle) == (149.0, 27.0)

    oblique = extract_oblique_triangle_altitude(
        "Cho tam giác ABC có đường cao A H = 5 cm, ˆ B = 70°, ˆ C = 35°. "
        "Tính độ dài các cạnh của tam giác ABC."
    )
    assert oblique is not None
    assert oblique.height == 5.0
    assert oblique.base_angles == {"B": 70.0, "C": 35.0}

    parallelogram = extract_perpendicular_diagonal_parallelogram(
        "Cho hình bình hành ABCD có AC ⟂ AD, AD = 3,5; góc D = 50°. "
        "Hỏi diện tích hình bình hành là bao nhiêu?"
    )
    assert parallelogram is not None
    assert parallelogram.diagonal == "AC"
    assert parallelogram.side == "AD"
    assert parallelogram.side_length == 3.5
    # No unit was printed, so the schema must not invent metres or centimetres.
    assert parallelogram.unit == "one"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("stem", "family", "roles", "steps"),
    [
        (
            "Một người quan sát ở đài hải đăng cao 149 m nhìn thấy tàu với góc "
            "nghiêng xuống đất là 27°. Hỏi tàu cách chân hải đăng là bao nhiêu mét?",
            "angle_of_depression_distance",
            {MathQuantityRole.HEIGHT, MathQuantityRole.ANGLE},
            4,
        ),
        (
            "Cho tam giác ABC có đường cao AH = 5 cm, góc B = 70°, góc C = 35°. "
            "Tính độ dài các cạnh của tam giác ABC.",
            "oblique_triangle_altitude_solution",
            {MathQuantityRole.HEIGHT, MathQuantityRole.ANGLE},
            5,
        ),
        (
            "Cho hình bình hành ABCD có AC ⟂ AD và AD = 3,5; góc D = 50°. "
            "Tính diện tích hình bình hành.",
            "parallelogram_perpendicular_diagonal_area",
            {MathQuantityRole.COUNT_INITIAL, MathQuantityRole.ANGLE},
            4,
        ),
    ],
)
async def test_grade9_trigonometry_reaches_a_ready_exact_scene(
    stem: str,
    family: str,
    roles: set[MathQuantityRole],
    steps: int,
) -> None:
    model = (await _analyzer().analyze_text(stem, 9)).questions[0].semantic_model
    assert model.problem_type == family
    assert {item.role for item in model.quantities} == roles
    assert all(item.role != MathQuantityRole.RESULT for item in model.quantities)
    assert model.relations[0].type == "trigonometric_geometry"
    plan = MathLabFoundationService().plan(model)
    assert plan.decisions[0].visualization.value == "geometry_2d"
    assert plan.visual_plan.status == "ready"
    assert len(plan.pedagogy.reveal_steps) == steps


# --- one-square Oxyz surfaces --------------------------------------------


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("6x^2 - 5x - 1 = 0", (6.0, -5.0, -1.0)),
        ("x² = 4", (1.0, 0.0, -4.0)),
        ("2x² + 3 = 5x", (2.0, -5.0, 3.0)),
        ("Giải phương trình -x² + 4x = 0", (-1.0, 4.0, 0.0)),
    ],
)
def test_quadratic_equation_parser_collects_both_sides(
    text: str,
    expected: tuple[float, float, float],
) -> None:
    equation = parse_quadratic_equation(text)
    assert equation is not None
    assert (
        equation.quadratic_coefficient,
        equation.linear_coefficient,
        equation.constant,
    ) == expected


@pytest.mark.parametrize(
    "text",
    [
        "x² + y = 0",
        "x² + y² = 0",
        "xy + x² = 0",
        "x³ - x = 0",
        "√x + x² = 0",
        "Trong bãi có 6 xe và 2 xe rời đi",
    ],
)
def test_quadratic_equation_parser_refuses_a_different_family(text: str) -> None:
    assert parse_quadratic_equation(text) is None


@pytest.mark.asyncio
async def test_plain_quadratic_equation_reaches_a_solved_parabola_scene() -> None:
    model = (
        await _analyzer().analyze_text("6x^2 - 5x - 1 = 0", 9)
    ).questions[0].semantic_model

    assert model.problem_type == "quadratic_equation"
    assert [item.role.value for item in model.quantities] == [
        "coefficient",
        "coefficient",
        "constant",
    ]
    assert [item.value for item in model.quantities] == [6.0, -5.0, -1.0]
    assert model.unknowns[0].kind == "roots"
    assert model.relations[0].type == "quadratic_equation"

    plan = MathLabFoundationService().plan(model)
    assert plan.decisions[0].visualization.value == "coordinate_graph"
    assert plan.visual_plan.status == "ready"
    assert plan.scene.visualizations[0].bindings["coefficient"] == [
        model.quantities[0].id,
        model.quantities[1].id,
    ]
    assert len(plan.pedagogy.reveal_steps) == 4
    assert plan.scene.world.values[model.unknowns[0].id].value is None


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("x^3 - 6x^2 + 11x - 6 = 0", (1.0, -6.0, 11.0, -6.0)),
        ("x³ = 8", (1.0, 0.0, 0.0, -8.0)),
        ("Giải phương trình 2x³ + 3 = 5x", (2.0, 0.0, -5.0, 3.0)),
        ("t³ - t = 0", (1.0, 0.0, -1.0, 0.0)),
    ],
)
def test_cubic_equation_parser_collects_every_degree(
    text: str,
    expected: tuple[float, float, float, float],
) -> None:
    equation = parse_cubic_equation(text)
    assert equation is not None
    assert (
        equation.cubic_coefficient,
        equation.quadratic_coefficient,
        equation.linear_coefficient,
        equation.constant,
    ) == expected


@pytest.mark.parametrize(
    "text",
    [
        "x³ + y = 0",
        "x³ + xy = 0",
        "x^4 - x = 0",
        "sqrt(x) + x³ = 0",
        "Trong lớp có 3 học sinh và 2 bàn",
    ],
)
def test_cubic_equation_parser_refuses_other_families(text: str) -> None:
    assert parse_cubic_equation(text) is None


# --- strict grade 8-9 equation families -----------------------------------


def test_fractional_linear_equation_clears_the_printed_denominators() -> None:
    equation = parse_fractional_linear_equation("(2x-1)/3=(x+2)/5")
    assert equation is not None
    assert equation.denominators == (3, 5)
    assert equation.coefficient == 7
    assert equation.result == 11
    assert equation.stages == (
        "(2x-1)/3=(x+2)/5",
        "10x - 5 = 3x + 6",
        "7x = 11",
    )


def test_special_equation_parsers_keep_every_structural_coefficient() -> None:
    absolute = parse_absolute_value_equation("|2x-3|=5")
    assert absolute is not None
    assert (absolute.coefficient, absolute.constant, absolute.right_side) == (2, -3, 5)

    biquadratic = parse_biquadratic_equation("x^4-5x^2+4=0")
    assert biquadratic is not None
    assert (
        biquadratic.quartic_coefficient,
        biquadratic.quadratic_coefficient,
        biquadratic.constant,
    ) == (1, -5, 4)

    radical = parse_radical_equation("sqrt(x+1)=x-1")
    assert radical is not None
    assert (
        radical.radicand_coefficient,
        radical.radicand_constant,
        radical.right_coefficient,
        radical.right_constant,
    ) == (1, 1, 1, -1)

    rational = parse_rational_equation("1/x+1/(x+1)=1")
    assert rational is not None
    assert rational.numerator_coefficients == (-1, 1, 1)
    assert rational.denominators == ((1, 0), (1, 1))


def test_keyboard_vietnamese_is_canonicalized_without_guessing_ambiguity() -> None:
    assert canonicalize_typed_math(
        "6x mũ 3 + 4x mũ 2 - 5x - 1 bằng 0"
    ) == "6x^3 + 4x^2 - 5x - 1 = 0"
    assert canonicalize_typed_math(
        "căn bậc hai của (x + 1) bằng x - 1"
    ) == "sqrt(x + 1) = x - 1"
    assert canonicalize_typed_math("ba phần năm") == "3/5"
    assert canonicalize_typed_math("3 và 2 phần 5") == "(3+2/5)"
    assert canonicalize_typed_math("3 2 phần 5") == "3 2/5"
    assert canonicalize_typed_math("căn bậc 3 của x bằng 2") == "can bac 3 cua x = 2"
    assert canonical_problem_type(" Cubic equation ") == "cubic_equation"
    fraction_sum = extract_binary_fraction("ba phần năm cộng một phần năm")
    assert fraction_sum is not None
    assert (
        fraction_sum.left_numerator,
        fraction_sum.left_denominator,
        fraction_sum.right_numerator,
        fraction_sum.right_denominator,
        fraction_sum.operation,
    ) == (3, 5, 1, 5, "addition")


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("stem", "family"),
    [
        ("6x mũ 3 + 4x mũ 2 - 5x - 1 bằng 0", "cubic_equation"),
        ("x phần 3 cộng x phần 2 bằng 10", "fractional_linear_equation"),
        ("giá trị tuyệt đối của (2x trừ 3) bằng 5", "absolute_value_equation"),
        ("x mũ 4 trừ 5x mũ 2 cộng 4 bằng 0", "biquadratic_equation"),
        ("căn bậc hai của (x cộng 1) bằng x trừ 1", "radical_equation"),
        ("một phần x cộng một phần (x cộng 1) bằng 1", "rational_equation"),
    ],
)
async def test_spoken_keyboard_equations_reach_the_exact_deterministic_family(
    stem: str,
    family: str,
) -> None:
    model = (await _analyzer().analyze_text(stem, 9)).questions[0].semantic_model
    assert model.problem_type == family
    assert model.relations


@pytest.mark.parametrize(
    ("parser", "text"),
    [
        (parse_fractional_linear_equation, "x/(x+1)=2"),
        (parse_absolute_value_equation, "|x|=y"),
        (parse_biquadratic_equation, "x^4+x^3+1=0"),
        (parse_radical_equation, "sqrt(x^2+1)=x"),
        (parse_rational_equation, "1/x+1/y=1"),
        (parse_rational_equation, "1/(x^2+1)=0"),
    ],
)
def test_special_equation_parsers_refuse_a_different_family(parser, text: str) -> None:
    assert parser(text) is None


def test_special_equation_parsers_never_raise_on_malformed_classroom_input() -> None:
    malformed = [
        "", " ", "?", "x/0=1", "1/(x+)=2", "|x+1=3", "||=0",
        "sqrt()=1", "sqrt(x+1", "x^999=1", "x^4+y^2=1",
        "1/(x+1)+1/(x+2)+1/(x+3)=0", "../../etc/passwd", "<script>alert(1)</script>",
        "Một xe đi 60 km/h trong 2 giờ", "∞/x=NaN", "(((((x)))))=1",
    ]
    parsers = (
        parse_fractional_linear_equation,
        parse_absolute_value_equation,
        parse_biquadratic_equation,
        parse_radical_equation,
        parse_rational_equation,
    )
    for text in malformed:
        for parser in parsers:
            assert parser(text) is None


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("stem", "family", "renderer"),
    [
        ("x/3+x/2=10", "fractional_linear_equation", "balance"),
        ("(2x-1)/3=(x+2)/5", "fractional_linear_equation", "balance"),
        ("|2x-3|=5", "absolute_value_equation", "solution_set"),
        ("x^4-5x^2+4=0", "biquadratic_equation", "solution_set"),
        ("sqrt(x+1)=x-1", "radical_equation", "solution_set"),
        ("1/x+1/(x+1)=1", "rational_equation", "solution_set"),
    ],
)
async def test_special_equations_reach_a_ready_visual_without_the_vlm(
    stem: str,
    family: str,
    renderer: str,
) -> None:
    model = (await _analyzer().analyze_text(stem, 9)).questions[0].semantic_model
    plan = MathLabFoundationService().plan(model)
    assert model.problem_type == family
    assert model.relations
    assert model.unknowns[0].kind in {"variable", "solution_set"}
    assert plan.decisions[0].visualization.value == renderer
    assert plan.visual_plan.status == "ready"
    assert len(plan.pedagogy.reveal_steps) == 4


@pytest.mark.asyncio
async def test_plain_cubic_equation_reaches_a_ready_solved_graph() -> None:
    model = (
        await _analyzer().analyze_text("x^3 - 6x^2 + 11x - 6 = 0", 9)
    ).questions[0].semantic_model

    assert model.problem_type == "cubic_equation"
    assert [item.role.value for item in model.quantities] == [
        "coefficient",
        "coefficient",
        "coefficient",
        "constant",
    ]
    assert [item.value for item in model.quantities] == [1.0, -6.0, 11.0, -6.0]
    assert model.unknowns[0].kind == "roots"
    assert model.relations[0].type == "polynomial_equation"
    assert model.relations[0].parameters["degree"] == 3

    plan = MathLabFoundationService().plan(model)
    assert plan.decisions[0].visualization.value == "coordinate_graph"
    assert plan.visual_plan.status == "ready"
    assert plan.scene.visualizations[0].bindings["coefficient"] == [
        model.quantities[0].id,
        model.quantities[1].id,
        model.quantities[2].id,
    ]
    assert len(plan.pedagogy.reveal_steps) == 5
    assert plan.scene.world.values[model.unknowns[0].id].value is None


@pytest.mark.asyncio
async def test_typed_cubic_source_is_never_rewritten_by_analysis_or_scene() -> None:
    source = "  6X mũ 3 + 4X mũ 2 - 5X - 1 bằng 0  "
    result = await _analyzer().analyze_text(source, 9)
    question = result.questions[0]

    assert result.extracted_text == source
    assert question.stem == source
    assert question.semantic_model.source_text == source
    scene = MathLabFoundationService().plan(question.semantic_model).scene
    assert scene.metadata["source_text"] == source
    assert scene.metadata["source_preserved"] is True


def test_quadratic_surface_parser_is_strict_about_the_supported_shape() -> None:
    surface = parse_quadratic_surface("x² + 5y - z = 0")
    assert surface is not None
    assert surface.squared_symbol == "x"
    assert surface.squared_coefficient == 1
    assert surface.linear_coefficients == {"y": 5.0, "z": -1.0}
    assert surface.output_symbol == "z"

    # Two squared variables, a cross-product and a higher power are different
    # families.  None may be silently flattened into this renderer.
    assert parse_quadratic_surface("x² + y² - z = 0") is None
    assert parse_quadratic_surface("xy + z = 0") is None
    assert parse_quadratic_surface("x³ + y - z = 0") is None
    assert parse_quadratic_surface("Trong bãi có 58 xe tải") is None


def test_a_speed_unit_is_never_a_rational_denominator() -> None:
    assert parse_rational_domain(
        "Lan đi 40 km với vận tốc 10 km/h. Hỏi chuyến đi kéo dài bao lâu?"
    ) is None
    domain = parse_rational_domain(
        "Điều kiện xác định của phương trình 2 + 1/(x-3) = 5/(x+3) là gì?"
    )
    assert domain is not None
    assert domain.denominators == ((1.0, -3.0), (1.0, 3.0))
    assert parse_rational_domain(
        "Tìm hai nghiệm rồi đối chiếu x₁+x₂=-b/a, x₁x₂=c/a cho x²+2x-8=0"
    ) is None


@pytest.mark.asyncio
async def test_x_squared_plus_5y_minus_z_reaches_a_curved_3d_scene() -> None:
    model = (await _analyzer().analyze_text("x^2 + 5y - z = 0", 9)).questions[0].semantic_model
    assert model.problem_type == "quadratic_surface_three_variables"
    assert model.relations[0].type == "quadratic_surface"
    assert model.relations[0].parameters["output_symbol"] == "z"
    assert model.unknowns[0].kind == "quadratic_surface"
    # Only printed coefficients are givens; sampled points remain renderer
    # state and therefore cannot leak in as an AI-supplied answer.
    assert [item.value for item in model.quantities] == [1.0, 5.0, -1.0, 0.0]
    plan = MathLabFoundationService().plan(model)
    assert plan.decisions[0].visualization.value == "geometry_3d"
    assert plan.visual_plan.status == "ready"
    assert len(plan.pedagogy.reveal_steps) == 5
