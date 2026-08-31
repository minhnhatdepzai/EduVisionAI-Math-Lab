#!/usr/bin/env python3
"""Run the versioned grade 1-9 Math Lab acceptance matrix.

Reports totals by grade, family, modality and failure layer. A case passes the
layers this runner owns -- ``analyzer`` and ``plan`` -- only when the semantic
roles, unknown roles, renderer decision and step count all match what the
matrix declares. The ``renderer`` layer is asserted by the frontend suite
against the same file, and the ``browser`` layer by the real HTTPS session.

The vision model is deliberately refused: any case reaching it means the
deterministic grammar stopped claiming an input it used to own.

Usage:
    python training/math_lab/benchmarks/run_acceptance_matrix.py
    python training/math_lab/benchmarks/run_acceptance_matrix.py --output report.json
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "master_be"))
sys.path.insert(0, str(ROOT / "training/math_lab/scripts"))

MATRIX = ROOT / "training/math_lab/benchmarks/grade_1_9_acceptance.json"
DEFAULT_REPORT = ROOT / "training/math_lab/benchmarks/acceptance_report.json"

import random  # noqa: E402

import prepare_sft as generator  # noqa: E402
from app.core.config import Settings  # noqa: E402
from app.services.math_lab.analyzer import MathProblemAnalyzer, ProviderDocument  # noqa: E402
from app.services.math_lab.foundation import MathLabFoundationService  # noqa: E402

GENERATED_DATA = ROOT / "training/math_lab/data/generated"

INTERNAL_VOCABULARY = ("renderer", "schema", "semantic", "payload", "backend", "unsupported")


class RefusingProvider:
    """Fails loudly if a matrix case needs the vision model to be understood."""

    name = "acceptance-matrix"
    model = "no-vision"

    async def available(self) -> bool:
        return False

    async def analyze_text(self, _text, _grade_hint):
        raise AssertionError("matrix case fell through to the vision model")

    async def analyze_image(self, _image, _media_type, _grade_hint):
        raise AssertionError("matrix case fell through to the vision model")


async def run_case(case: dict[str, Any]) -> dict[str, Any]:
    """Return the outcome of one case, naming the layer that failed."""

    analyzer = MathProblemAnalyzer(Settings(), provider=RefusingProvider())
    failures: list[str] = []
    layer = None
    if case.get("expected_deterministic") is False:
        # An adversarial case: no deterministic grammar may claim this stem.
        # Perception for it is measured by the SFT audit and the browser gate.
        draft = MathProblemAnalyzer._deterministic_text_draft(case["stem"], case["grade"])
        claimed = None if draft is None else draft.questions[0].problem_type
        return {
            "id": case["id"],
            "grade": case["grade"],
            "family": case["family"],
            "modality": case["modality"],
            "passed": draft is None,
            "failure_layer": None if draft is None else "analyzer",
            "failures": [] if draft is None else [
                f"a deterministic grammar wrongly claimed this stem as {claimed!r}"
            ],
        }
    try:
        if case.get("generated"):
            # Reference semantics for a family the vision model perceives.
            rng = random.Random(f"math-lab-acceptance:{case['family']}:{case['split']}")
            _stem, payload = generator.build_case(case["family"], 1, rng, case["split"])
            result = analyzer._finalize(ProviderDocument.model_validate(payload), "text", None)
        else:
            result = await analyzer.analyze_text(case["stem"], case["grade"])
        model = result.questions[0].semantic_model
    except Exception as exc:  # noqa: BLE001 - the failure layer is the report
        return {
            "id": case["id"],
            "grade": case["grade"],
            "family": case["family"],
            "modality": case["modality"],
            "passed": False,
            "failure_layer": "analyzer",
            "failures": [f"{type(exc).__name__}: {exc}"],
        }

    layer = "analyzer"
    if model.problem_type != case["expected_problem_type"]:
        failures.append(
            f"problem_type {model.problem_type!r} != {case['expected_problem_type']!r}"
        )
    roles = [item.role.value for item in model.quantities if item.role]
    if sorted(roles) != sorted(case["expected_semantic_roles"]):
        failures.append(f"semantic roles {roles} != {case['expected_semantic_roles']}")
    unknown_roles = [item.role.value for item in model.unknowns if item.role]
    if sorted(unknown_roles) != sorted(case["expected_unknown_roles"]):
        failures.append(f"unknown roles {unknown_roles} != {case['expected_unknown_roles']}")
    if case["expected_semantic_roles"] and not model.quantities:
        failures.append("required quantities are empty")

    if not failures:
        layer = "plan"
        try:
            plan = MathLabFoundationService().plan(model)
        except Exception as exc:  # noqa: BLE001
            failures.append(f"plan raised {type(exc).__name__}: {exc}")
            plan = None
        if plan is not None:
            decided = plan.decisions[0].visualization.value
            expected = case["expected_renderer"]
            if expected == "clarification":
                # Abstaining is the expected product behaviour here, but the
                # sentence a teacher reads must stay Vietnamese and plain.
                if decided != "unsupported":
                    failures.append(f"expected an abstention, decided {decided!r}")
                lowered = plan.decisions[0].reason.lower()
                leaked = [word for word in INTERNAL_VOCABULARY if word in lowered]
                if leaked:
                    failures.append(f"clarification leaks internal vocabulary {leaked}")
            else:
                if decided != expected:
                    failures.append(f"renderer {decided!r} != {expected!r}")
                if plan.visual_plan.status != "ready":
                    failures.append(f"visual plan status {plan.visual_plan.status!r} != 'ready'")
                steps = plan.pedagogy.reveal_steps
                if len(steps) < 3 or len(steps) > 6:
                    failures.append(f"{len(steps)} reveal steps, expected 3-6")
                if len({step.id for step in steps}) != len(steps):
                    failures.append("reveal steps repeat an id instead of changing state")

    return {
        "id": case["id"],
        "grade": case["grade"],
        "family": case["family"],
        "modality": case["modality"],
        "passed": not failures,
        "failure_layer": None if not failures else layer,
        "failures": failures,
    }


async def main_async(matrix_path: Path, report_path: Path | None) -> int:
    matrix = json.loads(matrix_path.read_text(encoding="utf-8"))
    outcomes = [await run_case(case) for case in matrix["cases"]]

    by_grade: dict[str, Counter] = defaultdict(Counter)
    by_family: dict[str, Counter] = defaultdict(Counter)
    by_modality: dict[str, Counter] = defaultdict(Counter)
    by_layer: Counter = Counter()
    for outcome in outcomes:
        bucket = "passed" if outcome["passed"] else "failed"
        by_grade[str(outcome["grade"])][bucket] += 1
        by_family[outcome["family"]][bucket] += 1
        by_modality[outcome["modality"]][bucket] += 1
        if not outcome["passed"]:
            by_layer[outcome["failure_layer"] or "unknown"] += 1

    passed = sum(1 for outcome in outcomes if outcome["passed"])
    report = {
        "matrix_version": matrix["matrix_version"],
        "catalog_version": matrix["catalog_version"],
        "total": len(outcomes),
        "passed": passed,
        "failed": len(outcomes) - passed,
        "by_grade": {grade: dict(counts) for grade, counts in sorted(by_grade.items())},
        "by_family": {family: dict(counts) for family, counts in sorted(by_family.items())},
        "by_modality": {modality: dict(counts) for modality, counts in sorted(by_modality.items())},
        "failures_by_layer": dict(by_layer),
        "cases": outcomes,
    }
    rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if report_path:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(rendered, encoding="utf-8")

    print(f"matrix {matrix['matrix_version']}: {passed}/{len(outcomes)} passed")
    for outcome in outcomes:
        if not outcome["passed"]:
            print(f"  FAIL [{outcome['failure_layer']}] {outcome['id']}")
            for failure in outcome["failures"]:
                print(f"        {failure}")
    return 0 if passed == len(outcomes) else 1


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--matrix", type=Path, default=MATRIX)
    parser.add_argument("--output", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()
    raise SystemExit(asyncio.run(main_async(args.matrix, args.output)))


if __name__ == "__main__":
    main()
