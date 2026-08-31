#!/usr/bin/env python3
"""Audit generated SFT data against runtime schema and renderer decisions."""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
MASTER_BE = ROOT / "master_be"
DATA_ROOT = ROOT / "training/math_lab/data/generated"
sys.path.insert(0, str(MASTER_BE))

from app.core.config import Settings  # noqa: E402
from app.services.math_lab.analyzer import MathProblemAnalyzer, ProviderDocument  # noqa: E402
from app.services.math_lab.foundation import MathLabFoundationService  # noqa: E402


EXPECTED_VISUAL = {
    "addition": "object_group",
    "subtraction": "object_group",
    # The word-problem grammar relabels these to the "_basic" family it owns.
    "addition_basic": "object_group",
    "subtraction_basic": "object_group",
    "multiplication_grouping": "grouping",
    "division_grouping": "grouping",
    "multiplication_basic": "grouping",
    "division_basic": "grouping",
    "fraction_addition": "fraction",
    "fraction_subtraction": "fraction",
    "fraction_multiplication": "fraction",
    "fraction_equivalence": "fraction",
    "fraction_power": "power_model",
    "ratio_from_known_value": "bar_model",
    "sequential_fraction_remainder_ratio": "bar_model",
    "sequential_fraction_remainder_quantity": "bar_model",
    "work_rate_with_variable_people": "bar_model",
    "linear_equation": "balance",
    "compound_linear_equation": "balance",
    "mixed_rational_expression": "expression_tree",
    "discount_tax_percentage": "percent_grid",
    "two_item_discount_system": "percent_grid",
    "multi_segment_equal_distance_motion": "motion_path",
    "time_calendar_duration": "calendar",
    "algebraic_expression_modeling": "algebra_tiles",
    "triangle_centroid_median_proof": "geometry_2d",
    "triangle_similarity_metric_relation": "geometry_2d",
    "word_equation_rectangle": "balance",
    "right_triangle_solution": "geometry_2d",
    "right_triangle_hypotenuse": "geometry_2d",
    "linear_function": "coordinate_graph",
    "coordinate_plot": "coordinate_graph",
    "rectangle_area": "geometry_2d",
    "rectangle_perimeter": "geometry_2d",
    "cuboid_volume": "geometry_3d",
    "binomial_expansion": "bar_model",
    "distance_speed_time": "motion_path",
    "place_value_read_write": "place_value",
    "decimal_read_write": "place_value",
    "column_arithmetic_regrouping_addition": "column_algorithm",
    "column_arithmetic_regrouping_subtraction": "column_algorithm",
    "decimal_arithmetic_addition": "column_algorithm",
    "decimal_arithmetic_subtraction": "column_algorithm",
    "column_arithmetic_regrouping_multiplication": "column_algorithm",
    "column_arithmetic_regrouping_division": "column_algorithm",
    "decimal_arithmetic_multiplication": "column_algorithm",
    "decimal_arithmetic_division": "column_algorithm",
    "measurement_conversion_comparison": "unit_scale",
    "picture_bar_chart_reading": "data_chart",
    "fraction_division": "fraction",
    "quadratic_function_graph": "coordinate_graph",
    "statistics_probability_from_chart": "data_chart",
    "triangle_area": "geometry_2d",
    "number_ordering_rounding_ordering": "number_compare",
    "number_ordering_rounding_rounding": "number_compare",
    "signed_decimal_fraction_ordering": "number_compare",
    "circle_radius_diameter": "geometry_2d",
    "rhombus_area_properties": "geometry_2d",
    "parallelogram_area_properties": "geometry_2d",
    "ray_segment_midpoint": "geometry_2d",
    "angle_bisector": "geometry_2d",
    "quadratic_equation_vieta": "coordinate_graph",
    "experimental_probability": "probability_simulator",
    "cylinder_volume": "geometry_3d",
    "cone_volume": "geometry_3d",
    "sphere_volume": "geometry_3d",
    "percentage_part_whole": "percent_grid",
    "polynomial_evaluate_reorder": "algebra_tiles",
    "polynomial_add_subtract_addition": "algebra_tiles",
    "polynomial_add_subtract_subtraction": "algebra_tiles",
    "missing_number_equation": "part_whole",
    "shape_recognition_counting_pattern": "shape_pattern",
    "ratio_total_parts": "bar_model",
    "proportional_system_two_variables": "bar_model",
    "arithmetic_mean": "bar_model",
    "multi_step_arithmetic_subtract_then_add": "bar_model",
    "map_scale": "unit_scale",
    "circle_area": "circle_model",
    "circle_tangent_cyclic_proof": "circle_model",
    "divisibility_common_multiple": "factor_lattice",
    "linear_inequality_one_variable": "solution_set",
    "product_equation_roots": "solution_set",
    "rational_equation_domain": "solution_set",
    "angle_of_depression_distance": "geometry_2d",
    "oblique_triangle_altitude_solution": "geometry_2d",
    "parallelogram_perpendicular_diagonal_area": "geometry_2d",
    "quadratic_surface_three_variables": "geometry_3d",
}


def main() -> None:
    analyzer = MathProblemAnalyzer(Settings())
    foundation = MathLabFoundationService()
    seen_across_splits: dict[str, str] = {}
    report: dict[str, dict] = {}
    for split in ("train", "validation", "test"):
        path = DATA_ROOT / f"math_scene_{split}.jsonl"
        counter: Counter[str] = Counter()
        pair_targets: dict[str, str] = {}
        stems_in_split: set[str] = set()
        with path.open(encoding="utf-8") as stream:
            for line_number, line in enumerate(stream, 1):
                record = json.loads(line)
                target_text = record["conversations"][1]["value"]
                draft = ProviderDocument.model_validate_json(target_text)
                question = draft.questions[0]
                stem = question.stem
                problem_type = question.problem_type
                counter[problem_type] += 1

                base_id, modality = record["id"].rsplit("-", 1)
                previous = pair_targets.setdefault(base_id, target_text)
                if previous != target_text:
                    raise AssertionError(f"Text/image targets differ for {base_id}")
                if modality == "image":
                    image_path = DATA_ROOT / record["image"]
                    if not image_path.is_file() or image_path.stat().st_size == 0:
                        raise AssertionError(f"Missing image at line {line_number}: {image_path}")

                unknown_roles = {item.role for item in question.unknowns}
                leaked = [item.role.value for item in question.quantities if item.role in unknown_roles]
                if leaked:
                    raise AssertionError(f"Unknown leaked into quantities at line {line_number}: {leaked}")

                finalized = analyzer._finalize(draft, "text", None).questions[0].semantic_model
                plan = foundation.plan(finalized)
                actual = plan.decisions[0].visualization.value
                expected = EXPECTED_VISUAL[problem_type]
                if actual != expected:
                    raise AssertionError(
                        f"Renderer mismatch at line {line_number}: {problem_type} -> {actual}, expected {expected}"
                    )
                stems_in_split.add(stem)

        for stem in stems_in_split:
            previous_split = seen_across_splits.setdefault(stem, split)
            if previous_split != split:
                raise AssertionError(f"Stem leakage between {previous_split} and {split}: {stem}")
        expected_records = len(pair_targets) * 2
        if sum(counter.values()) != expected_records:
            raise AssertionError(f"Incomplete modality pairs in {split}")
        report[split] = {
            "records": sum(counter.values()),
            "semantic_cases": len(pair_targets),
            "families": dict(sorted(counter.items())),
            "schema_validity": 1.0,
            "unknown_leakage": 0,
            "renderer_decision_accuracy": 1.0,
        }
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
