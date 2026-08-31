#!/usr/bin/env python3
"""Validate and summarize grade 1-9 exam-family coverage.

This audit deliberately treats a related or fallback renderer as partial, not
implemented.  A family is counted as implemented only when the catalog points
to an exact generated SFT family and a structurally appropriate renderer.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CATALOG = ROOT / "training/math_lab/catalogs/grade_1_9_exam_families.json"
DEFAULT_MANIFEST = ROOT / "training/math_lab/data/generated/manifest.json"
VALID_STATUSES = {"implemented_sft", "renderer_ready", "partial", "missing"}
VALID_PRIORITIES = {"P0", "P1", "P2"}


def percentage(numerator: int, denominator: int) -> float:
    return round(numerator / denominator, 4) if denominator else 0.0


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--catalog", type=Path, default=DEFAULT_CATALOG)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    catalog = json.loads(args.catalog.read_text(encoding="utf-8"))
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    generated_families = set(manifest.get("families", []))
    sources = {source["id"]: source for source in catalog["sources"]}
    families = catalog["families"]

    errors: list[str] = []
    family_ids: set[str] = set()
    exact_dataset_families: set[str] = set()
    for family in families:
        family_id = family.get("id")
        if family_id in family_ids:
            errors.append(f"Duplicate family id: {family_id}")
        family_ids.add(family_id)

        status = family.get("status")
        if status not in VALID_STATUSES:
            errors.append(f"{family_id}: invalid status {status!r}")
        if family.get("priority") not in VALID_PRIORITIES:
            errors.append(f"{family_id}: invalid priority {family.get('priority')!r}")

        grades = family.get("grades", [])
        if not grades or any(not isinstance(grade, int) or grade < 1 or grade > 9 for grade in grades):
            errors.append(f"{family_id}: grades must be unique integers from 1 to 9")
        if len(grades) != len(set(grades)):
            errors.append(f"{family_id}: duplicate grade")

        observed_sources = family.get("observed_in", [])
        if not observed_sources:
            errors.append(f"{family_id}: no exam evidence")
        unknown_sources = set(observed_sources) - set(sources)
        if unknown_sources:
            errors.append(f"{family_id}: unknown sources {sorted(unknown_sources)}")
        covered_grades = {
            grade
            for source_id in observed_sources
            if source_id in sources
            for grade in sources[source_id].get("grades", [])
        }
        uncovered = set(grades) - covered_grades
        if uncovered:
            errors.append(f"{family_id}: no cited source covers grades {sorted(uncovered)}")

        renderer = family.get("current_renderer")
        dataset_family = family.get("dataset_family")
        gap = family.get("gap")
        if status == "implemented_sft":
            if not renderer or not dataset_family:
                errors.append(f"{family_id}: implemented family needs renderer and dataset_family")
            elif dataset_family not in generated_families:
                errors.append(f"{family_id}: generated manifest is missing {dataset_family}")
            else:
                exact_dataset_families.add(dataset_family)
            if gap is not None:
                errors.append(f"{family_id}: implemented family must not carry a gap")
        elif status == "renderer_ready":
            if not renderer or dataset_family is not None:
                errors.append(f"{family_id}: renderer_ready needs renderer and no dataset_family")
            if not gap:
                errors.append(f"{family_id}: renderer_ready needs an SFT gap explanation")
        elif status == "partial":
            if not renderer or dataset_family is not None or not gap:
                errors.append(f"{family_id}: partial needs renderer, gap and no exact dataset_family")
        elif status == "missing":
            if renderer is not None or dataset_family is not None or not gap:
                errors.append(f"{family_id}: missing needs a gap and no renderer/dataset_family")

    source_grades = {
        grade
        for source in sources.values()
        if source.get("kind") in {"public_school_exam", "public_school_exam_and_matrix", "user_provided_exam_image"}
        for grade in source.get("grades", [])
    }
    if source_grades != set(range(1, 10)):
        errors.append(f"Exam evidence must cover grades 1-9; got {sorted(source_grades)}")

    status_counts = Counter(family["status"] for family in families)
    grade_report: dict[str, dict] = {}
    for grade in range(1, 10):
        grade_families = [family for family in families if grade in family["grades"]]
        grade_counts = Counter(family["status"] for family in grade_families)
        implemented = grade_counts["implemented_sft"]
        ready = grade_counts["renderer_ready"]
        partial = grade_counts["partial"]
        total = len(grade_families)
        grade_report[str(grade)] = {
            "families": total,
            "implemented_sft": implemented,
            "renderer_ready": ready,
            "partial": partial,
            "missing": grade_counts["missing"],
            "exact_coverage": percentage(implemented, total),
            "renderer_reach_including_partial": percentage(implemented + ready + partial, total),
            "p0_gaps": [
                family["id"]
                for family in grade_families
                if family["priority"] == "P0" and family["status"] != "implemented_sft"
            ],
        }

    total = len(families)
    implemented = status_counts["implemented_sft"]
    ready = status_counts["renderer_ready"]
    partial = status_counts["partial"]
    report = {
        "catalog": args.catalog.relative_to(ROOT).as_posix(),
        "checked_at": catalog["checked_at"],
        "valid": not errors,
        "errors": errors,
        "summary": {
            "exam_families": total,
            "implemented_sft": implemented,
            "renderer_ready": ready,
            "partial": partial,
            "missing": status_counts["missing"],
            "exact_coverage": percentage(implemented, total),
            "renderer_reach_including_partial": percentage(implemented + ready + partial, total),
            "generated_families": len(generated_families),
            "generated_exam_families": len(exact_dataset_families),
            "generated_additional_families": sorted(generated_families - exact_dataset_families),
        },
        "by_grade": grade_report,
    }
    rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
