#!/usr/bin/env python3
"""Build the versioned grade 1-9 Math Lab acceptance matrix.

The matrix is the executable form of the coverage claim. Every case records
what a correct pipeline must produce -- semantic roles, unknown roles, the
renderer that family deserves, and the visual/step invariants a scene must
satisfy -- so a regression shows up as a failing case rather than as a
percentage nobody recomputed.

Expectations are written here, not read back from the engine. A case that
simply echoed the current decision could never fail.

Usage:
    python training/math_lab/benchmarks/build_acceptance_matrix.py
"""

from __future__ import annotations

import json
import random
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "training/math_lab/scripts"))

CATALOG = ROOT / "training/math_lab/catalogs/grade_1_9_exam_families.json"
MANIFEST = ROOT / "training/math_lab/data/generated/manifest.json"
OUTPUT = ROOT / "training/math_lab/benchmarks/grade_1_9_acceptance.json"

MATRIX_VERSION = "math-lab-acceptance-v3"

#: Cases whose semantics must come out of the deterministic text grammar with
#: no vision model involved. ``expected_renderer`` of ``clarification`` means
#: the lab must abstain with a calm Vietnamese message instead of drawing.
TEXT_CASES: list[dict[str, Any]] = [
    # -- grade 1-2 arithmetic -------------------------------------------------
    {
        "id": "g1-addition-symbolic",
        "grade": 1,
        "family": "addition_basic",
        "stem": "4+3=?",
        "expected_problem_type": "addition_basic",
        "expected_semantic_roles": ["count_initial", "count_change"],
        "expected_unknown_roles": ["result"],
        "expected_renderer": "object_group",
        "expected_visual_invariants": ["parts_conserved", "operands_visible"],
        "expected_step_invariants": ["observe", "transform", "conclude"],
        "tags": ["p0", "symbolic"],
    },
    {
        "id": "g1-addition-word",
        "grade": 1,
        "family": "addition_basic",
        "stem": "Lan có 5 quả táo, mẹ cho thêm 3 quả. Hỏi Lan có tất cả bao nhiêu quả táo?",
        "expected_problem_type": "addition_basic",
        "expected_semantic_roles": ["count_initial", "count_change"],
        "expected_unknown_roles": ["result"],
        "expected_renderer": "object_group",
        "expected_visual_invariants": ["parts_conserved", "operands_visible"],
        "expected_step_invariants": ["observe", "transform", "conclude"],
        "tags": ["p0", "accented", "word_problem"],
    },
    {
        "id": "g1-subtraction-truck-yard",
        "grade": 1,
        "family": "subtraction_basic",
        "stem": "Trong bãi có 58 chiếc xe tải. Có 38 chiếc xe rời bãi. Hỏi xe tải còn lại trong bãi là bao nhiêu?",
        "expected_problem_type": "subtraction_basic",
        "expected_semantic_roles": ["count_initial", "count_change"],
        "expected_unknown_roles": ["result"],
        "expected_renderer": "object_group",
        "expected_visual_invariants": ["parts_conserved", "removed_part_marked"],
        "expected_step_invariants": ["observe", "transform", "conclude"],
        "tags": ["p0", "accented", "word_problem", "regression"],
    },
    {
        "id": "g2-multiplication-word-unaccented",
        "grade": 2,
        "family": "multiplication_basic",
        "stem": "2 nhân 4 bằng mấy?",
        "expected_problem_type": "multiplication_basic",
        "expected_semantic_roles": ["count_initial", "count_change"],
        "expected_unknown_roles": ["result"],
        "expected_renderer": "grouping",
        "expected_visual_invariants": ["groups_times_size_equals_total"],
        "expected_step_invariants": ["observe", "transform", "conclude"],
        "tags": ["p0", "accented"],
    },
    {
        "id": "g2-division-equal-share",
        "grade": 2,
        "family": "division_basic",
        "stem": "Có 24 cái kẹo chia đều cho 6 bạn. Mỗi bạn được bao nhiêu cái kẹo?",
        "expected_problem_type": "division_basic",
        "expected_semantic_roles": ["count_initial", "count_change"],
        "expected_unknown_roles": ["result"],
        "expected_renderer": "grouping",
        "expected_visual_invariants": ["groups_times_size_equals_total"],
        "expected_step_invariants": ["observe", "transform", "conclude"],
        "tags": ["accented", "word_problem"],
    },
    {
        "id": "g3-parenthesized-multiplication",
        "grade": 3,
        "family": "parenthesized_addition_multiplication",
        "stem": "(1+1)×2",
        "expected_problem_type": "parenthesized_addition_multiplication",
        "expected_semantic_roles": ["count_initial", "count_change", "coefficient"],
        "expected_unknown_roles": ["result"],
        "expected_renderer": "grouping",
        "expected_visual_invariants": ["parentheses_resolved_first", "groups_times_size_equals_total"],
        "expected_step_invariants": ["observe", "transform", "conclude"],
        "tags": ["p0", "symbolic", "regression"],
    },
    {
        "id": "g3-parenthesized-multiplication-unaccented",
        "grade": 3,
        "family": "parenthesized_addition_multiplication",
        "stem": "( 1 + 1 ) x 2 bang may?",
        "expected_problem_type": "parenthesized_addition_multiplication",
        "expected_semantic_roles": ["count_initial", "count_change", "coefficient"],
        "expected_unknown_roles": ["result"],
        "expected_renderer": "grouping",
        "expected_visual_invariants": ["parentheses_resolved_first", "groups_times_size_equals_total"],
        "expected_step_invariants": ["observe", "transform", "conclude"],
        "tags": ["p0", "unaccented", "ocr", "regression"],
    },
    # -- fractions and ratio --------------------------------------------------
    {
        "id": "g4-fraction-addition",
        "grade": 4,
        "family": "fraction_addition",
        "stem": "Tính 1/2 + 1/4 bằng bao nhiêu?",
        "expected_problem_type": "fraction_addition",
        "expected_semantic_roles": [
            "numerator", "denominator", "addend_numerator", "addend_denominator",
        ],
        "expected_unknown_roles": ["result"],
        "expected_renderer": "fraction",
        "expected_visual_invariants": ["common_whole_preserved", "partition_counts_valid"],
        "expected_step_invariants": ["observe", "transform", "conclude"],
        "tags": ["p0", "accented"],
    },
    {
        "id": "g4-fraction-addition-typed-phan",
        "grade": 4,
        "family": "fraction_addition",
        "stem": "ba phần năm cộng một phần năm",
        "expected_problem_type": "fraction_addition",
        "expected_semantic_roles": [
            "numerator", "denominator", "addend_numerator", "addend_denominator",
        ],
        "expected_unknown_roles": ["result"],
        "expected_renderer": "fraction",
        "expected_visual_invariants": ["common_whole_preserved", "partition_counts_valid"],
        "expected_step_invariants": ["observe", "transform", "conclude"],
        "tags": ["grade4", "keyboard_alias", "accented", "regression"],
    },
    {
        "id": "g4-rectangle-area",
        "grade": 4,
        "family": "rectangle_area",
        "stem": "Một hình chữ nhật dài 8 cm, rộng 5 cm. Tính diện tích hình chữ nhật.",
        "expected_problem_type": "rectangle_area",
        "expected_semantic_roles": ["length", "width"],
        "expected_unknown_roles": ["result"],
        "expected_renderer": "geometry_2d",
        "expected_visual_invariants": ["dimensions_labelled", "area_partitioned"],
        "expected_step_invariants": ["observe", "transform", "conclude"],
        "tags": ["accented", "word_problem"],
    },
    {
        "id": "g5-distance-time-direct-proportion",
        "grade": 5,
        "family": "distance_time_direct_proportion",
        "stem": "Một ô tô đi trong 5 giờ được 225 km. Ô tô đó đi trong 8 giờ được quãng đường là bao nhiêu",
        "expected_problem_type": "distance_time_direct_proportion",
        "expected_semantic_roles": ["duration", "distance", "duration"],
        "expected_unknown_roles": ["result"],
        "expected_renderer": "bar_model",
        "expected_visual_invariants": ["equal_blocks", "unit_rate_visible"],
        "expected_step_invariants": ["observe", "transform", "conclude", "check"],
        "tags": ["p0", "accented", "word_problem", "regression"],
    },
    {
        "id": "g5-distance-time-unseen-numbers",
        "grade": 5,
        "family": "distance_time_direct_proportion",
        "stem": "Một xe máy đi trong 4 giờ được 180 km. Xe đó đi trong 7 giờ được quãng đường là bao nhiêu",
        "expected_problem_type": "distance_time_direct_proportion",
        "expected_semantic_roles": ["duration", "distance", "duration"],
        "expected_unknown_roles": ["result"],
        "expected_renderer": "bar_model",
        "expected_visual_invariants": ["equal_blocks", "unit_rate_visible"],
        "expected_step_invariants": ["observe", "transform", "conclude", "check"],
        "tags": ["accented", "unseen_numbers"],
    },
    {
        "id": "g5-work-rate-variable-people",
        "grade": 5,
        "family": "work_rate_with_variable_people",
        "stem": (
            "Một tổ gồm 8 người dự định làm xong một con đường trong 6 ngày, "
            "sau đó tổ được bổ sung thêm 4 người. Hỏi công việc hoàn thành trong "
            "bao nhiêu ngày, biết sức làm việc của mỗi người như nhau?"
        ),
        "expected_problem_type": "work_rate_with_variable_people",
        "expected_semantic_roles": ["count_initial", "duration", "count_change"],
        "expected_unknown_roles": ["result"],
        "expected_renderer": "bar_model",
        "expected_visual_invariants": ["worker_days_conserved"],
        "expected_step_invariants": ["observe", "transform", "conclude", "check"],
        "tags": ["p0", "accented", "word_problem", "regression"],
    },
    {
        "id": "g6-sequential-fraction-remainder-quantity",
        "grade": 6,
        "family": "sequential_fraction_remainder_quantity",
        "stem": (
            "Một khu đất rộng 10 dam² 80 m². Người ta dùng 2/5 diện tích khu đất để làm nhà, "
            "sau đó dùng tiếp 1/3 phần còn lại để trồng hoa. Hỏi diện tích phần đất cuối cùng là bao nhiêu mét vuông?"
        ),
        "expected_problem_type": "sequential_fraction_remainder_quantity",
        "expected_semantic_roles": [
            "area", "area", "numerator", "denominator",
            "addend_numerator", "addend_denominator",
        ],
        "expected_unknown_roles": ["result"],
        "expected_renderer": "bar_model",
        "expected_visual_invariants": ["remainder_repartitioned", "total_conserved"],
        "expected_step_invariants": ["observe", "transform", "conclude", "check"],
        "tags": ["p0", "accented", "word_problem", "regression"],
    },
    # -- the P0 linear family -------------------------------------------------
    {
        "id": "g7-linear-expression-tiles",
        "grade": 7,
        "family": "polynomial_evaluate_reorder",
        "stem": "2x+1",
        "expected_problem_type": "polynomial_evaluate_reorder",
        "expected_semantic_roles": ["coefficient", "exponent", "coefficient", "exponent"],
        "expected_unknown_roles": ["result"],
        "expected_renderer": "algebra_tiles",
        "expected_visual_invariants": ["degree_preserved", "no_equation_solved"],
        "expected_step_invariants": ["observe", "transform", "conclude"],
        "tags": ["p0", "symbolic"],
    },
    {
        "id": "g8-linear-equation-balance",
        "grade": 8,
        "family": "linear_equation",
        "stem": "2x+3=9",
        "expected_problem_type": "linear_equation",
        "expected_semantic_roles": ["coefficient", "constant", "result"],
        "expected_unknown_roles": ["variable"],
        "expected_renderer": "balance",
        "expected_visual_invariants": ["same_operation_both_sides"],
        "expected_step_invariants": ["observe", "transform", "conclude", "check"],
        "tags": ["p0", "symbolic"],
    },
    {
        "id": "g8-linear-equation-variable-both-sides",
        "grade": 8,
        "family": "linear_equation",
        "stem": "5x = 2x + 9",
        "expected_problem_type": "linear_equation",
        "expected_semantic_roles": ["coefficient", "constant", "result"],
        "expected_unknown_roles": ["variable"],
        "expected_renderer": "balance",
        "expected_visual_invariants": ["same_operation_both_sides"],
        "expected_step_invariants": ["observe", "transform", "conclude", "check"],
        "tags": ["p0", "symbolic", "boundary"],
    },
    {
        "id": "g8-compound-linear-equation",
        "grade": 8,
        "family": "compound_linear_equation",
        "stem": "3(x+2)-5=2x+7",
        "expected_problem_type": "compound_linear_equation",
        "expected_semantic_roles": ["coefficient", "constant", "result"],
        "expected_unknown_roles": ["variable"],
        "expected_renderer": "balance",
        "expected_visual_invariants": ["brackets_expanded", "same_operation_both_sides"],
        "expected_step_invariants": ["observe", "transform", "conclude", "check"],
        "tags": ["symbolic", "grade8"],
    },
    {
        "id": "g8-compound-linear-equation-vietnamese",
        "grade": 8,
        "family": "compound_linear_equation",
        "stem": "Tìm x biết 5(x + 2) - 10 = x + 32.",
        "expected_problem_type": "compound_linear_equation",
        "expected_semantic_roles": ["coefficient", "constant", "result"],
        "expected_unknown_roles": ["variable"],
        "expected_renderer": "balance",
        "expected_visual_invariants": ["brackets_expanded", "same_operation_both_sides"],
        "expected_step_invariants": ["observe", "transform", "conclude", "check"],
        "tags": ["accented", "grade8"],
    },
    {
        "id": "adv-missing-number-blank",
        "grade": 2,
        "family": "missing_number_equation",
        "stem": "Điền số thích hợp: ? + 6 = 12.",
        # No deterministic grammar owns a fill-in-the-blank question. What must
        # hold is that the linear parser does not claim it either: reading it
        # as "6 = 12" produced a contradiction card for a grade-2 exercise.
        "expected_deterministic": False,
        "expected_problem_type": None,
        "expected_semantic_roles": [],
        "expected_unknown_roles": [],
        "expected_renderer": "provider",
        "expected_visual_invariants": ["blank_kept_in_role"],
        "expected_step_invariants": ["observe", "transform", "conclude"],
        "tags": ["adversarial", "near_family"],
    },
    {
        "id": "g8-two-variable-line",
        "grade": 8,
        "family": "linear_equation_two_variables_graph",
        "stem": "2x+y=1",
        "expected_problem_type": "linear_equation_two_variables_graph",
        "expected_semantic_roles": ["coefficient", "constant"],
        "expected_unknown_roles": ["result"],
        "expected_renderer": "coordinate_graph",
        "expected_visual_invariants": ["points_satisfy_equation", "equal_axis_scale"],
        "expected_step_invariants": ["observe", "transform", "conclude"],
        "tags": ["p0", "symbolic"],
    },
    {
        "id": "g8-two-variable-line-y-first",
        "grade": 8,
        "family": "linear_equation_two_variables_graph",
        "stem": "y=2x+1",
        "expected_problem_type": "linear_equation_two_variables_graph",
        "expected_semantic_roles": ["coefficient", "constant"],
        "expected_unknown_roles": ["result"],
        "expected_renderer": "coordinate_graph",
        "expected_visual_invariants": ["points_satisfy_equation", "equal_axis_scale"],
        "expected_step_invariants": ["observe", "transform", "conclude"],
        "tags": ["p0", "symbolic", "reordered"],
    },
    {
        "id": "g8-two-variable-line-vietnamese-prefix",
        "grade": 8,
        "family": "linear_equation_two_variables_graph",
        "stem": "Vẽ đồ thị hàm số y = 2x + 1",
        "expected_problem_type": "linear_equation_two_variables_graph",
        "expected_semantic_roles": ["coefficient", "constant"],
        "expected_unknown_roles": ["result"],
        "expected_renderer": "coordinate_graph",
        "expected_visual_invariants": ["points_satisfy_equation", "equal_axis_scale"],
        "expected_step_invariants": ["observe", "transform", "conclude"],
        "tags": ["p0", "accented"],
    },
    {
        "id": "g9-plane-through-origin",
        "grade": 9,
        "family": "linear_equation_three_variables_plane",
        "stem": "3x+y=z",
        "expected_problem_type": "linear_equation_three_variables_plane",
        "expected_semantic_roles": ["coefficient", "coefficient", "coefficient", "constant"],
        "expected_unknown_roles": ["result"],
        "expected_renderer": "geometry_3d",
        "expected_visual_invariants": [
            "canonical_form_shown",
            "plane_through_origin",
            "normal_vector_visible",
            "sample_points_satisfy_equation",
            "no_unique_solution_claimed",
        ],
        "expected_step_invariants": ["observe", "transform", "conclude", "check"],
        "tags": ["p0", "symbolic", "regression"],
    },
    {
        "id": "g9-plane-through-origin-spaced",
        "grade": 9,
        "family": "linear_equation_three_variables_plane",
        "stem": "3x + y = z",
        "expected_problem_type": "linear_equation_three_variables_plane",
        "expected_semantic_roles": ["coefficient", "coefficient", "coefficient", "constant"],
        "expected_unknown_roles": ["result"],
        "expected_renderer": "geometry_3d",
        "expected_visual_invariants": [
            "canonical_form_shown", "plane_through_origin", "normal_vector_visible",
        ],
        "expected_step_invariants": ["observe", "transform", "conclude", "check"],
        "tags": ["p0", "symbolic", "spacing"],
    },
    {
        "id": "g9-plane-through-origin-implicit-coefficient",
        "grade": 9,
        "family": "linear_equation_three_variables_plane",
        "stem": "x+y=z",
        "expected_problem_type": "linear_equation_three_variables_plane",
        "expected_semantic_roles": ["coefficient", "coefficient", "coefficient", "constant"],
        "expected_unknown_roles": ["result"],
        "expected_renderer": "geometry_3d",
        "expected_visual_invariants": ["plane_through_origin", "normal_vector_visible"],
        "expected_step_invariants": ["observe", "transform", "conclude", "check"],
        "tags": ["p0", "symbolic", "boundary"],
    },
    {
        "id": "g9-plane-offset",
        "grade": 9,
        "family": "linear_equation_three_variables_plane",
        "stem": "3x+y+z=6",
        "expected_problem_type": "linear_equation_three_variables_plane",
        "expected_semantic_roles": ["coefficient", "coefficient", "coefficient", "constant"],
        "expected_unknown_roles": ["result"],
        "expected_renderer": "geometry_3d",
        "expected_visual_invariants": ["sample_points_satisfy_equation", "normal_vector_visible"],
        "expected_step_invariants": ["observe", "transform", "conclude", "check"],
        "tags": ["p0", "symbolic"],
    },
    {
        "id": "g9-plane-negative-coefficients",
        "grade": 9,
        "family": "linear_equation_three_variables_plane",
        "stem": "-2x+4y-z=8",
        "expected_problem_type": "linear_equation_three_variables_plane",
        "expected_semantic_roles": ["coefficient", "coefficient", "coefficient", "constant"],
        "expected_unknown_roles": ["result"],
        "expected_renderer": "geometry_3d",
        "expected_visual_invariants": ["sample_points_satisfy_equation", "normal_vector_visible"],
        "expected_step_invariants": ["observe", "transform", "conclude", "check"],
        "tags": ["p0", "symbolic", "signs"],
    },
    {
        "id": "g9-system-intersecting",
        "grade": 9,
        "family": "linear_system_two_variables_graph",
        "stem": "x+y=3; x-y=1",
        "expected_problem_type": "linear_system_two_variables_graph",
        "expected_semantic_roles": [
            "coefficient", "coefficient", "constant", "coefficient", "coefficient", "constant",
        ],
        "expected_unknown_roles": ["variable", "variable"],
        "expected_renderer": "coordinate_graph",
        "expected_visual_invariants": ["two_lines_drawn", "intersection_marked"],
        "expected_step_invariants": ["observe", "transform", "conclude", "check"],
        "tags": ["p0", "symbolic"],
    },
    {
        "id": "g9-system-coincident",
        "grade": 9,
        "family": "linear_system_two_variables_graph",
        "stem": "2x+y=5 và 4x+2y=10",
        "expected_problem_type": "linear_system_two_variables_graph",
        "expected_semantic_roles": [
            "coefficient", "coefficient", "constant", "coefficient", "coefficient", "constant",
        ],
        "expected_unknown_roles": ["result"],
        "expected_renderer": "coordinate_graph",
        "expected_visual_invariants": ["two_lines_drawn", "coincident_state_named"],
        "expected_step_invariants": ["observe", "transform", "conclude"],
        "tags": ["p0", "symbolic", "boundary"],
    },
    {
        "id": "g9-system-parallel",
        "grade": 9,
        "family": "linear_system_two_variables_graph",
        "stem": "2x+y=5 và 4x+2y=3",
        "expected_problem_type": "linear_system_two_variables_graph",
        "expected_semantic_roles": [
            "coefficient", "coefficient", "constant", "coefficient", "coefficient", "constant",
        ],
        "expected_unknown_roles": ["result"],
        "expected_renderer": "coordinate_graph",
        "expected_visual_invariants": ["two_lines_drawn", "parallel_state_named"],
        "expected_step_invariants": ["observe", "transform", "conclude"],
        "tags": ["p0", "symbolic", "boundary"],
    },
    {
        "id": "g9-right-triangle-solution",
        "grade": 9,
        "family": "right_triangle_solution",
        "stem": "Hãy giải tam giác ABC vuông tại A. Biết AB = 5 cm, BC = 13 cm. (Góc làm tròn đến phút).",
        "expected_problem_type": "right_triangle_solution",
        "expected_semantic_roles": ["length", "height"],
        "expected_unknown_roles": ["result", "angle", "angle"],
        "expected_renderer": "geometry_2d",
        "expected_visual_invariants": [
            "right_angle_marked",
            "given_sides_labelled",
            "third_side_from_pythagoras",
            "acute_angles_complementary",
        ],
        "expected_step_invariants": ["observe", "transform", "conclude", "check"],
        "tags": ["p0", "accented", "regression", "grade9"],
    },
    {
        "id": "g9-right-triangle-solution-reordered",
        "grade": 9,
        "family": "right_triangle_solution",
        "stem": "Cho tam giác MNP vuông tại N có MN = 6 dm, MP = 10 dm. Giải tam giác MNP.",
        "expected_problem_type": "right_triangle_solution",
        "expected_semantic_roles": ["length", "height"],
        "expected_unknown_roles": ["result", "angle", "angle"],
        "expected_renderer": "geometry_2d",
        "expected_visual_invariants": ["right_angle_marked", "third_side_from_pythagoras"],
        "expected_step_invariants": ["observe", "transform", "conclude", "check"],
        "tags": ["accented", "reordered", "grade9"],
    },
    {
        "id": "g9-right-triangle-side-and-angle",
        "grade": 9,
        "family": "right_triangle_solution",
        "stem": "Cho tam giác ABC vuông tại A có AB = 5 cm và góc B = 40 độ. Giải tam giác ABC.",
        "expected_problem_type": "right_triangle_solution",
        "expected_semantic_roles": ["length", "angle"],
        "expected_unknown_roles": ["result", "result", "angle"],
        "expected_renderer": "geometry_2d",
        "expected_visual_invariants": [
            "right_angle_marked",
            "sides_from_trigonometric_ratios",
            "acute_angles_complementary",
        ],
        "expected_step_invariants": ["observe", "transform", "conclude", "check"],
        "tags": ["accented", "grade9", "trigonometry"],
    },
    {
        "id": "g9-right-triangle-hypotenuse",
        "grade": 9,
        "family": "right_triangle_hypotenuse",
        "stem": "Tam giác ABC vuông tại A, AB = 3 cm, AC = 4 cm. Tính độ dài BC.",
        "expected_problem_type": "right_triangle_hypotenuse",
        "expected_semantic_roles": ["length", "height"],
        "expected_unknown_roles": ["result"],
        "expected_renderer": "geometry_2d",
        "expected_visual_invariants": ["right_angle_marked", "legs_labelled"],
        "expected_step_invariants": ["observe", "transform", "conclude"],
        "tags": ["p0", "accented", "word_problem"],
    },
    {
        "id": "g9-quadratic-equation-plain",
        "grade": 9,
        "family": "quadratic_equation_vieta",
        "stem": "6x^2 - 5x - 1 = 0",
        "expected_problem_type": "quadratic_equation",
        "expected_semantic_roles": ["coefficient", "coefficient", "constant"],
        "expected_unknown_roles": ["result"],
        "expected_renderer": "coordinate_graph",
        "expected_visual_invariants": ["coefficients_visible", "roots_match_x_intercepts"],
        "expected_step_invariants": ["observe", "transform", "conclude", "check"],
        "tags": ["grade9", "quadratic", "symbolic", "regression"],
    },
    {
        "id": "g9-cubic-equation-three-real-roots",
        "grade": 9,
        "family": "cubic_equation",
        "stem": "x^3 - 6x^2 + 11x - 6 = 0",
        "expected_problem_type": "cubic_equation",
        "expected_semantic_roles": ["coefficient", "coefficient", "coefficient", "constant"],
        "expected_unknown_roles": ["result"],
        "expected_renderer": "coordinate_graph",
        "expected_visual_invariants": ["coefficients_visible", "all_real_roots_match_x_intercepts"],
        "expected_step_invariants": ["observe", "transform", "conclude", "check"],
        "tags": ["grade9", "cubic", "symbolic", "regression"],
    },
    {
        "id": "g8-fractional-linear-equation",
        "grade": 8,
        "family": "fractional_linear_equation",
        "stem": "(2x-1)/3=(x+2)/5",
        "expected_problem_type": "fractional_linear_equation",
        "expected_semantic_roles": ["coefficient", "constant", "result"],
        "expected_unknown_roles": ["variable"],
        "expected_renderer": "balance",
        "expected_visual_invariants": ["common_denominator_visible", "equivalent_stages_visible"],
        "expected_step_invariants": ["observe", "transform", "conclude", "check"],
        "tags": ["grade8", "fractional", "symbolic", "regression"],
    },
    {
        "id": "g8-absolute-value-two-roots",
        "grade": 8,
        "family": "absolute_value_equation",
        "stem": "|2x-3|=5",
        "expected_problem_type": "absolute_value_equation",
        "expected_semantic_roles": ["coefficient", "constant", "constant"],
        "expected_unknown_roles": ["variable"],
        "expected_renderer": "solution_set",
        "expected_visual_invariants": ["two_branches_visible", "accepted_roots_solid"],
        "expected_step_invariants": ["observe", "transform", "conclude", "check"],
        "tags": ["grade8", "absolute_value", "symbolic", "regression"],
    },
    {
        "id": "g9-biquadratic-four-roots",
        "grade": 9,
        "family": "biquadratic_equation",
        "stem": "x^4-5x^2+4=0",
        "expected_problem_type": "biquadratic_equation",
        "expected_semantic_roles": ["coefficient", "coefficient", "constant"],
        "expected_unknown_roles": ["variable"],
        "expected_renderer": "solution_set",
        "expected_visual_invariants": ["substitution_t_visible", "symmetric_roots_marked"],
        "expected_step_invariants": ["observe", "transform", "conclude", "check"],
        "tags": ["grade9", "biquadratic", "symbolic", "regression"],
    },
    {
        "id": "g9-radical-extraneous-root",
        "grade": 9,
        "family": "radical_equation",
        "stem": "sqrt(x+1)=x-1",
        "expected_problem_type": "radical_equation",
        "expected_semantic_roles": ["coefficient", "constant", "coefficient", "constant"],
        "expected_unknown_roles": ["variable"],
        "expected_renderer": "solution_set",
        "expected_visual_invariants": ["domain_visible", "extraneous_root_crossed_out"],
        "expected_step_invariants": ["observe", "transform", "conclude", "check"],
        "tags": ["grade9", "radical", "symbolic", "regression"],
    },
    {
        "id": "g9-rational-equation-roots-and-domain",
        "grade": 9,
        "family": "rational_equation",
        "stem": "1/x+1/(x+1)=1",
        "expected_problem_type": "rational_equation",
        "expected_semantic_roles": ["coefficient", "coefficient", "constant"],
        "expected_unknown_roles": ["variable"],
        "expected_renderer": "solution_set",
        "expected_visual_invariants": ["forbidden_values_hollow", "accepted_roots_solid"],
        "expected_step_invariants": ["observe", "transform", "conclude", "check"],
        "tags": ["grade9", "rational", "symbolic", "regression"],
    },
    # -- ordinary-keyboard Vietnamese aliases -------------------------------
    {
        "id": "g9-cubic-equation-typed-mu-bang",
        "grade": 9,
        "family": "cubic_equation",
        "stem": "6x mũ 3 + 4x mũ 2 - 5x - 1 bằng 0",
        "expected_problem_type": "cubic_equation",
        "expected_semantic_roles": ["coefficient", "coefficient", "coefficient", "constant"],
        "expected_unknown_roles": ["result"],
        "expected_renderer": "coordinate_graph",
        "expected_visual_invariants": ["coefficients_visible", "all_real_roots_match_x_intercepts"],
        "expected_step_invariants": ["observe", "transform", "conclude", "check"],
        "tags": ["grade9", "keyboard_alias", "accented", "regression"],
    },
    {
        "id": "g8-fractional-linear-typed-phan",
        "grade": 8,
        "family": "fractional_linear_equation",
        "stem": "x phần 3 cộng x phần 2 bằng 10",
        "expected_problem_type": "fractional_linear_equation",
        "expected_semantic_roles": ["coefficient", "constant", "result"],
        "expected_unknown_roles": ["variable"],
        "expected_renderer": "balance",
        "expected_visual_invariants": ["common_denominator_visible", "equivalent_stages_visible"],
        "expected_step_invariants": ["observe", "transform", "conclude", "check"],
        "tags": ["grade8", "keyboard_alias", "accented", "regression"],
    },
    {
        "id": "g8-absolute-value-typed-words",
        "grade": 8,
        "family": "absolute_value_equation",
        "stem": "giá trị tuyệt đối của (2x trừ 3) bằng 5",
        "expected_problem_type": "absolute_value_equation",
        "expected_semantic_roles": ["coefficient", "constant", "constant"],
        "expected_unknown_roles": ["variable"],
        "expected_renderer": "solution_set",
        "expected_visual_invariants": ["two_branches_visible", "accepted_roots_solid"],
        "expected_step_invariants": ["observe", "transform", "conclude", "check"],
        "tags": ["grade8", "keyboard_alias", "accented", "regression"],
    },
    {
        "id": "g9-biquadratic-typed-mu",
        "grade": 9,
        "family": "biquadratic_equation",
        "stem": "x mũ 4 trừ 5x mũ 2 cộng 4 bằng 0",
        "expected_problem_type": "biquadratic_equation",
        "expected_semantic_roles": ["coefficient", "coefficient", "constant"],
        "expected_unknown_roles": ["variable"],
        "expected_renderer": "solution_set",
        "expected_visual_invariants": ["substitution_t_visible", "symmetric_roots_marked"],
        "expected_step_invariants": ["observe", "transform", "conclude", "check"],
        "tags": ["grade9", "keyboard_alias", "accented", "regression"],
    },
    {
        "id": "g9-radical-typed-can-bac-hai",
        "grade": 9,
        "family": "radical_equation",
        "stem": "căn bậc hai của (x cộng 1) bằng x trừ 1",
        "expected_problem_type": "radical_equation",
        "expected_semantic_roles": ["coefficient", "constant", "coefficient", "constant"],
        "expected_unknown_roles": ["variable"],
        "expected_renderer": "solution_set",
        "expected_visual_invariants": ["domain_visible", "extraneous_root_crossed_out"],
        "expected_step_invariants": ["observe", "transform", "conclude", "check"],
        "tags": ["grade9", "keyboard_alias", "accented", "regression"],
    },
    {
        "id": "g9-rational-typed-phan",
        "grade": 9,
        "family": "rational_equation",
        "stem": "một phần x cộng một phần (x cộng 1) bằng 1",
        "expected_problem_type": "rational_equation",
        "expected_semantic_roles": ["coefficient", "coefficient", "constant"],
        "expected_unknown_roles": ["variable"],
        "expected_renderer": "solution_set",
        "expected_visual_invariants": ["forbidden_values_hollow", "accepted_roots_solid"],
        "expected_step_invariants": ["observe", "transform", "conclude", "check"],
        "tags": ["grade9", "keyboard_alias", "accented", "regression"],
    },
    {
        "id": "g9-linear-inequality-number-line",
        "grade": 9,
        "family": "linear_inequality_one_variable",
        "stem": "Giải bất phương trình 5 - 2x <= 1",
        "expected_problem_type": "linear_inequality_one_variable",
        "expected_semantic_roles": ["coefficient", "constant"],
        "expected_unknown_roles": ["variable"],
        "expected_renderer": "solution_set",
        "expected_visual_invariants": ["boundary_marked", "inequality_direction_visible"],
        "expected_step_invariants": ["observe", "transform", "conclude", "check"],
        "tags": ["grade9", "inequality", "regression"],
    },
    {
        "id": "g9-product-equation-roots",
        "grade": 9,
        "family": "product_equation_roots",
        "stem": "Tổng các nghiệm của phương trình (x - 3)(x + 8) = 0",
        "expected_problem_type": "product_equation_roots",
        "expected_semantic_roles": ["coefficient", "constant", "coefficient", "constant"],
        "expected_unknown_roles": ["variable"],
        "expected_renderer": "solution_set",
        "expected_visual_invariants": ["both_roots_marked", "sum_derived"],
        "expected_step_invariants": ["observe", "transform", "conclude", "check"],
        "tags": ["grade9", "product", "regression"],
    },
    {
        "id": "g9-rational-domain-exclusions",
        "grade": 9,
        "family": "rational_equation_domain",
        "stem": "Điều kiện xác định của phương trình 2 + 1/(x-3) = 5/(x+3) là gì?",
        "expected_problem_type": "rational_equation_domain",
        "expected_semantic_roles": ["coefficient", "constant", "coefficient", "constant"],
        "expected_unknown_roles": ["variable"],
        "expected_renderer": "solution_set",
        "expected_visual_invariants": ["excluded_points_hollow", "denominators_visible"],
        "expected_step_invariants": ["observe", "transform", "conclude", "check"],
        "tags": ["grade9", "rational", "regression"],
    },
    {
        "id": "g9-angle-of-depression-lighthouse",
        "grade": 9,
        "family": "angle_of_depression_distance",
        "stem": "Một người ở đài hải đăng cao 149 m nhìn thấy tàu với góc nghiêng xuống đất là 27°. Hỏi tàu cách chân hải đăng là bao nhiêu mét?",
        "expected_problem_type": "angle_of_depression_distance",
        "expected_semantic_roles": ["height", "angle"],
        "expected_unknown_roles": ["result"],
        "expected_renderer": "geometry_2d",
        "expected_visual_invariants": ["horizontal_parallel_visible", "line_of_sight_visible"],
        "expected_step_invariants": ["observe", "transform", "conclude", "check"],
        "tags": ["grade9", "trigonometry", "word_problem"],
    },
    {
        "id": "g9-oblique-triangle-altitude",
        "grade": 9,
        "family": "oblique_triangle_altitude_solution",
        "stem": "Cho tam giác ABC có đường cao AH = 5 cm, góc B = 70°, góc C = 35°. Tính độ dài các cạnh của tam giác ABC.",
        "expected_problem_type": "oblique_triangle_altitude_solution",
        "expected_semantic_roles": ["height", "angle", "angle"],
        "expected_unknown_roles": ["result", "result", "result"],
        "expected_renderer": "geometry_2d",
        "expected_visual_invariants": ["altitude_splits_two_right_triangles", "all_sides_derived"],
        "expected_step_invariants": ["observe", "transform", "conclude", "check"],
        "tags": ["grade9", "trigonometry", "geometry"],
    },
    {
        "id": "g9-parallelogram-perpendicular-diagonal",
        "grade": 9,
        "family": "parallelogram_perpendicular_diagonal_area",
        "stem": "Cho hình bình hành ABCD có AC ⟂ AD và AD = 3,5; góc D = 50°. Tính diện tích hình bình hành.",
        "expected_problem_type": "parallelogram_perpendicular_diagonal_area",
        "expected_semantic_roles": ["count_initial", "angle"],
        "expected_unknown_roles": ["result"],
        "expected_renderer": "geometry_2d",
        "expected_visual_invariants": ["perpendicular_diagonal_visible", "area_height_visible"],
        "expected_step_invariants": ["observe", "transform", "conclude", "check"],
        "tags": ["grade9", "trigonometry", "geometry"],
    },
    {
        "id": "g9-quadratic-surface-xyz",
        "grade": 9,
        "family": "quadratic_surface_three_variables",
        "stem": "x^2 + 5y - z = 0",
        "expected_problem_type": "quadratic_surface_three_variables",
        "expected_semantic_roles": ["coefficient", "coefficient", "coefficient", "constant"],
        "expected_unknown_roles": ["result"],
        "expected_renderer": "geometry_3d",
        "expected_visual_invariants": ["curved_surface_not_plane", "sample_points_satisfy_equation"],
        "expected_step_invariants": ["observe", "transform", "conclude", "check"],
        "tags": ["grade9", "geometry3d", "nonlinear", "regression"],
    },
    # -- adversarial near-family and degenerate input -------------------------
    {
        "id": "adv-linear-identity",
        "grade": 8,
        "family": "linear_identity",
        "stem": "x=x",
        "expected_problem_type": "linear_identity",
        "expected_semantic_roles": [],
        "expected_unknown_roles": ["result"],
        "expected_renderer": "clarification",
        "expected_visual_invariants": ["vietnamese_clarification", "no_internal_vocabulary"],
        "expected_step_invariants": [],
        "tags": ["adversarial", "degenerate"],
    },
    {
        "id": "adv-linear-contradiction",
        "grade": 8,
        "family": "linear_contradiction",
        "stem": "x+1=x+2",
        "expected_problem_type": "linear_contradiction",
        "expected_semantic_roles": [],
        "expected_unknown_roles": ["result"],
        "expected_renderer": "clarification",
        "expected_visual_invariants": ["vietnamese_clarification", "no_internal_vocabulary"],
        "expected_step_invariants": [],
        "tags": ["adversarial", "degenerate"],
    },
]


def case_rng(family: str, split: str) -> random.Random:
    """Deterministic per-case generator seed, shared with the matrix runner."""

    return random.Random(f"math-lab-acceptance:{family}:{split}")


def generated_cases() -> list[dict[str, Any]]:
    """One case per generated family and split, in both modalities.

    The deterministic grammars cover only the families a teacher can type as a
    bare expression. Everything else is perceived by the vision model, so the
    matrix exercises those families from their reference semantics instead:
    the plan, renderer and steps must still be correct. These cases are labelled
    ``semantic_reference`` rather than ``image``: they prove the deterministic
    half of the pipeline, while perception is measured by ``audit_sft.py`` --
    which does open every generated image -- and by the real-browser gate.
    """

    import prepare_sft as generator  # noqa: PLC0415 - optional heavy import
    from audit_sft import EXPECTED_VISUAL  # noqa: PLC0415

    if not MANIFEST.exists():
        return []
    families = json.loads(MANIFEST.read_text(encoding="utf-8"))["families"]
    cases: list[dict[str, Any]] = []
    for family in families:
        for split in ("train", "validation", "test"):
            # Seed per case, not per run: a shared sequence would make the case
            # depend on how many families were generated before it.
            stem, payload = generator.build_case(family, 1, case_rng(family, split), split)
            question = payload["questions"][0]
            problem_type = question["problem_type"]
            expected = EXPECTED_VISUAL.get(problem_type)
            if expected is None:
                raise SystemExit(
                    f"{family}/{split} produced {problem_type!r}, which has no "
                    "expected renderer in audit_sft.EXPECTED_VISUAL"
                )
            cases.append({
                "id": f"gen-{family}-{split}",
                "grade": question["grade"],
                "family": family,
                "stem": stem,
                "split": split,
                "generated": True,
                "expected_problem_type": problem_type,
                "expected_semantic_roles": [item["role"] for item in question["quantities"]],
                "expected_unknown_roles": [item["role"] for item in question["unknowns"]],
                "expected_renderer": expected,
                "expected_visual_invariants": ["operands_visible", "steps_change_state"],
                "expected_step_invariants": ["observe", "transform", "conclude"],
                "tags": ["generated", f"grade{question['grade']}"],
                "modality": "semantic_reference",
                "source": "generated_semantics",
            })
    return cases


def main() -> None:
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    families = {family["id"]: family for family in catalog["families"]}

    cases: list[dict[str, Any]] = []
    for case in TEXT_CASES:
        cases.append({**case, "modality": "text", "source": "deterministic_text_grammar"})
    cases.extend(generated_cases())

    matrix = {
        "schema_version": "1.0",
        "matrix_version": MATRIX_VERSION,
        "catalog_version": catalog["catalog_version"],
        "locale": "vi-VN",
        "scope": (
            "Executable Math Lab acceptance cases for Vietnamese grades 1-9. Each case "
            "must pass the analyzer, plan, renderer and visible-browser layers."
        ),
        "catalog_families": sorted(families),
        "cases": cases,
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(matrix, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {len(cases)} cases to {OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
