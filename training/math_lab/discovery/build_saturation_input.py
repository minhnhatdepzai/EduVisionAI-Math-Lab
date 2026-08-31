#!/usr/bin/env python3
"""Turn the observed Math Lab corpus into a saturation-audit input.

The saturation question is "have we stopped meeting families we cannot name?",
and it can only be answered against questions the lab has actually seen. Two
sources qualify today: the deterministic grade 1-9 corpus, and the acceptance
matrix, which carries the hand-written regression stems.

A question counts as a **new family** when its semantic family is absent from
the reviewed catalog. That is the honest signal: a corpus that keeps producing
unclassified families is not saturated, however large it is. This does not
claim national exam coverage -- it measures only the corpus named above, and
`--minimum-batch` keeps a thin grade from being declared saturated by default.

Usage:
    python training/math_lab/discovery/build_saturation_input.py
    python training/math_lab/discovery/audit_family_saturation.py \
        training/math_lab/data/generated/observed_questions.jsonl \
        --minimum-batch 40
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CATALOG = ROOT / "training/math_lab/catalogs/grade_1_9_exam_families.json"
MATRIX = ROOT / "training/math_lab/benchmarks/grade_1_9_acceptance.json"
GENERATED = ROOT / "training/math_lab/data/generated"
DEFAULT_OUTPUT = GENERATED / "observed_questions.jsonl"

#: Families the catalog records under a different id than the dataset uses.
#: Keeping the aliases explicit stops a rename from being reported as a
#: newly discovered family. Only genuine renames belong here -- mapping two
#: different families onto one another would hide a real gap.
CATALOG_ALIASES = {
    "addition": "concrete_addition_word_problem",
    "addition_basic": "concrete_addition_word_problem",
    "subtraction": "concrete_subtraction_word_problem",
    "subtraction_basic": "concrete_subtraction_word_problem",
    "multiplication_grouping": "multiplication_equal_groups",
    "multiplication_basic": "multiplication_equal_groups",
    "division_grouping": "division_equal_groups",
    "division_basic": "division_equal_groups",
    "distance_speed_time": "single_leg_motion",
    "mixed_rational_expression": "mixed_rational_arithmetic_percent",
    "triangle_centroid_median_proof": "triangle_congruence_centroid_proof",
    "multi_step_arithmetic_subtract_then_add": "multi_step_arithmetic_word",
    "cone_volume": "cylinder_cone_sphere_volume",
    "cylinder_volume": "cylinder_cone_sphere_volume",
    "sphere_volume": "cylinder_cone_sphere_volume",
    "rhombus_area_properties": "rhombus_parallelogram_area_properties",
    "parallelogram_area_properties": "rhombus_parallelogram_area_properties",
    "right_triangle_hypotenuse": "right_triangle_hypotenuse",
    "linear_equation_two_variables_graph": "linear_equation_two_variables_graph",
    "linear_system_two_variables_graph": "linear_system_two_variables_graph",
    "linear_equation_three_variables_plane": "linear_equation_three_variables_plane",
    "linear_identity": "linear_degenerate_statement",
    "linear_contradiction": "linear_degenerate_statement",
}

#: Named, renderer-backed families that sit outside the exam-derived catalog.
#: They are classified -- the lab knows what they are and how to draw them --
#: but they are not evidence of exam coverage, so they are listed separately
#: instead of being folded into a catalog family they do not belong to.
GENERATED_ONLY_FAMILIES = frozenset({
    "binomial_expansion",
    "coordinate_plot",
    "ratio_from_known_value",
    "rectangle_area",
    "right_triangle_hypotenuse",
    "right_triangle_solution",
    "distance_time_direct_proportion",
    "parenthesized_addition_multiplication",
    "parenthesized_subtraction_multiplication",
    "linear_equation_two_variables_graph",
    "linear_system_two_variables_graph",
    "linear_equation_three_variables_plane",
    "linear_degenerate_statement",
})


def catalog_family_ids() -> set[str]:
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    known = {family["id"] for family in catalog["families"]}
    known.update(
        family["dataset_family"]
        for family in catalog["families"]
        if family.get("dataset_family")
    )
    known.update(GENERATED_ONLY_FAMILIES)
    return known


def normalize(family: str) -> str:
    if family in CATALOG_ALIASES:
        return CATALOG_ALIASES[family]
    # Operation-specific variants such as decimal_arithmetic_division belong to
    # the family that generated them.
    for suffix in ("_addition", "_subtraction", "_multiplication", "_division",
                   "_ordering", "_rounding"):
        if family.endswith(suffix):
            return family[: -len(suffix)]
    return family


def records() -> list[dict]:
    known = catalog_family_ids()
    seen_families: set[str] = set()
    rows: list[dict] = []

    def add(question_id: str, grade: int, family: str, batch_id: str, source: str) -> None:
        canonical = normalize(family)
        classified = canonical in known or family in known
        is_new = canonical not in seen_families and not classified
        seen_families.add(canonical)
        rows.append({
            "question_id": question_id,
            "grade": int(grade),
            "batch_id": batch_id,
            "family": canonical,
            "raw_family": family,
            "classified": classified,
            "is_new_family": is_new,
            "source": source,
        })

    for split in ("train", "validation", "test"):
        path = GENERATED / f"math_scene_{split}.jsonl"
        if not path.exists():
            continue
        with path.open(encoding="utf-8") as stream:
            for index, line in enumerate(stream):
                record = json.loads(line)
                if not record["id"].endswith("-text"):
                    continue
                question = json.loads(record["conversations"][1]["value"])["questions"][0]
                add(
                    record["id"],
                    question["grade"],
                    question["problem_type"],
                    f"{split}-g{question['grade']}",
                    "generated_corpus",
                )
                del index

    if MATRIX.exists():
        matrix = json.loads(MATRIX.read_text(encoding="utf-8"))
        for case in matrix["cases"]:
            if case.get("generated"):
                continue
            add(
                case["id"],
                case["grade"],
                case.get("expected_problem_type") or case["family"],
                f"acceptance-g{case['grade']}",
                "acceptance_matrix",
            )
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    rows = records()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as stream:
        for row in rows:
            stream.write(json.dumps(row, ensure_ascii=False) + "\n")
    unclassified = sorted({row["family"] for row in rows if not row["classified"]})
    print(json.dumps({
        "questions": len(rows),
        "families": len({row["family"] for row in rows}),
        "unclassified_families": unclassified,
        "output": str(args.output.relative_to(ROOT)),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
