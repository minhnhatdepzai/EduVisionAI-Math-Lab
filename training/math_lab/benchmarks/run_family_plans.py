#!/usr/bin/env python3
"""Plan every generated SFT family and report the renderer it actually reaches.

The SFT generator is the one place that already knows a schema-valid
``ProviderDocument`` for each family. Feeding those documents through the real
normalizer, decision engine and pedagogy planner answers the question the
coverage table only claims: does this family reach an exact renderer, or does
it quietly fall back to ``unsupported``?

Usage:
    python training/math_lab/benchmarks/run_family_plans.py
    python training/math_lab/benchmarks/run_family_plans.py --family circle_area
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "master_be"))
sys.path.insert(0, str(ROOT / "training/math_lab/scripts"))

import prepare_sft as generator  # noqa: E402
from app.core.config import Settings  # noqa: E402
from app.services.math_lab.analyzer import MathProblemAnalyzer, ProviderDocument  # noqa: E402
from app.services.math_lab.foundation import MathLabFoundationService  # noqa: E402

DEFAULT_REPORT = ROOT / "training/math_lab/benchmarks/family_plan_report.json"


def family_list() -> list[str]:
    manifest = ROOT / "training/math_lab/data/generated/manifest.json"
    if manifest.exists():
        stored = json.loads(manifest.read_text(encoding="utf-8")).get("families")
        if stored:
            return list(stored)
    return []


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--family", action="append", dest="families")
    parser.add_argument("--samples", type=int, default=3)
    parser.add_argument("--seed", type=int, default=260826)
    parser.add_argument("--output", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()

    families = args.families or family_list()
    if not families:
        raise SystemExit("No families to plan; run prepare_sft.py first.")

    analyzer = MathProblemAnalyzer(Settings())
    foundation = MathLabFoundationService()
    rng = random.Random(args.seed)

    results: list[dict] = []
    splits = ("train", "validation", "test")
    for family in families:
        renderers: dict[str, int] = {}
        statuses: dict[str, int] = {}
        problem_types: dict[str, int] = {}
        per_split: dict[str, set[str]] = {split: set() for split in splits}
        failures: list[str] = []
        planned = 0
        for split in splits:
            for index in range(args.samples):
                try:
                    _stem, payload = generator.build_case(family, index + 1, rng, split)
                    document = ProviderDocument.model_validate(payload)
                    analysis = analyzer._finalize(document, "text", None)
                    model = analysis.questions[0].semantic_model
                    plan = foundation.plan(model)
                except Exception as exc:  # noqa: BLE001 - the failure is the report
                    failures.append(f"{type(exc).__name__}: {exc}")
                    continue
                planned += 1
                renderer = plan.decisions[0].visualization.value
                renderers[renderer] = renderers.get(renderer, 0) + 1
                problem_types[model.problem_type] = problem_types.get(model.problem_type, 0) + 1
                per_split[split].add(model.problem_type)
                statuses[plan.visual_plan.status] = statuses.get(plan.visual_plan.status, 0) + 1
                if len(plan.pedagogy.reveal_steps) < 3:
                    failures.append(f"{family}: only {len(plan.pedagogy.reveal_steps)} reveal steps")
        # A generator family may deliberately emit several problem types, but
        # the choice must come from the case index -- never from the split.
        # A split-dependent difference means the wording of one phrasing was
        # claimed by a different grammar, which is how a two-step word problem
        # silently became a plain subtraction.
        distinct = {frozenset(values) for values in per_split.values() if values}
        if len(distinct) > 1:
            failures.append(
                f"{family}: problem types depend on the split: "
                + "; ".join(f"{split}={sorted(values)}" for split, values in per_split.items())
            )
        exact = (
            "unsupported" not in renderers
            and not failures
            and statuses.get("ready", 0) == planned
            and planned == args.samples * len(splits)
        )
        results.append({
            "family": family,
            "renderers": renderers,
            "problem_types": problem_types,
            "plan_status": statuses,
            "failures": failures,
            "exact": exact,
        })

    exact_count = sum(1 for item in results if item["exact"])
    report = {
        "families": len(results),
        "exact": exact_count,
        "not_exact": [item["family"] for item in results if not item["exact"]],
        "results": results,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{exact_count}/{len(results)} generated families reach an exact ready renderer")
    for item in results:
        if not item["exact"]:
            print(f"  {item['family']}: renderers={item['renderers']} status={item['plan_status']} {item['failures'][:1]}")


if __name__ == "__main__":
    main()
