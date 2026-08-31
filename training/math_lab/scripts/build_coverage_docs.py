#!/usr/bin/env python3
"""Generate honest coverage tables from the reviewed grade 1-9 catalog."""

from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
CATALOG = ROOT / "training/math_lab/catalogs/grade_1_9_exam_families.json"
GRADE_DOC = ROOT / "docs/math-lab/GRADE_1_9_COVERAGE.md"
VISUAL_DOC = ROOT / "docs/math-lab/VISUAL_COVERAGE_MATRIX.md"


def percent(value: int, total: int) -> str:
    return f"{100 * value / total:.1f}%" if total else "0.0%"


def main() -> None:
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    families = catalog["families"]
    grade_rows = []
    for grade in range(1, 10):
        current = [item for item in families if grade in item["grades"]]
        statuses = Counter(item["status"] for item in current)
        exact = statuses["implemented_sft"]
        reach = exact + statuses["renderer_ready"] + statuses["partial"]
        p0 = [
            item["id"] for item in current
            if item["priority"] == "P0" and item["status"] != "implemented_sft"
        ]
        grade_rows.append(
            f"| {grade} | {len(current)} | {exact} | {statuses['partial']} | "
            f"{statuses['missing']} | {percent(exact, len(current))} | "
            f"{percent(reach, len(current))} | {', '.join(f'`{item}`' for item in p0) or '—'} |"
        )
    detail_rows = [
        "| " + " | ".join([
            "`" + item["id"] + "`",
            ", ".join(str(grade) for grade in item["grades"]),
            item["domain"],
            item["status"],
            "`" + item["current_renderer"] + "`" if item["current_renderer"] else "—",
            item["gap"] or "—",
        ]) + " |"
        for item in families
    ]
    exact_total = sum(item["status"] == "implemented_sft" for item in families)
    partial_total = sum(item["status"] == "partial" for item in families)
    missing_total = sum(item["status"] == "missing" for item in families)
    grade_doc = f"""# Grade 1–9 coverage

Generated from `training/math_lab/catalogs/grade_1_9_exam_families.json` by
`training/math_lab/scripts/build_coverage_docs.py` on the catalog date
**{catalog['checked_at']}**.

This is an observed-family baseline, not proof that every Vietnamese exam type
has been discovered. Exact coverage is {exact_total}/{len(families)}
({percent(exact_total, len(families))}); {partial_total} families are partial
and {missing_total} are missing. The separate saturation audit must pass before
any broad coverage claim is made.

| Grade | Observed families | Exact | Partial | Missing | Exact coverage | Renderer reach incl. partial | P0 gaps |
|---:|---:|---:|---:|---:|---:|---:|---|
{chr(10).join(grade_rows)}

## Family matrix

| Family | Grades | Domain | Status | Current renderer | Material gap |
|---|---|---|---|---|---|
{chr(10).join(detail_rows)}

Status meanings come from the catalog. `implemented_sft` requires both an exact
generated semantic family and a structurally appropriate renderer; a related
fallback is only `partial`.
"""
    GRADE_DOC.write_text(grade_doc, encoding="utf-8")

    registry_size = len(
        re.findall(
            r'"([a-z_]+)"',
            (ROOT / "frontend/src/features/math-lab/schemas/mathLabSchema.js")
            .read_text(encoding="utf-8")
            .split("export const VISUALIZATION_IDS = Object.freeze([")[1]
            .split("]);")[0],
        )
    )
    renderer_rows: dict[str, list[dict]] = defaultdict(list)
    for item in families:
        renderer_rows[item["current_renderer"] or "missing"].append(item)
    visual_lines = []
    for renderer, items in sorted(renderer_rows.items()):
        counts = Counter(item["status"] for item in items)
        visual_lines.append(
            f"| `{renderer}` | {len(items)} | {counts['implemented_sft']} | "
            f"{counts['renderer_ready']} | {counts['partial']} | {counts['missing']} | "
            + ", ".join(f"`{item['id']}`" for item in items) + " |"
        )
    visual_doc = f"""# Visual coverage matrix

Generated from catalog version `{catalog.get('catalog_version', 'unversioned')}`
by `training/math_lab/scripts/build_coverage_docs.py`.
The frontend registry contains {registry_size} IDs including `unsupported`;
registry presence alone is not counted as family readiness.

| Renderer | Observed families | Exact SFT | Renderer-only | Partial | Missing | Families |
|---|---:|---:|---:|---:|---:|---|
{chr(10).join(visual_lines)}

`missing` groups families with no truthful current renderer. Quality gates are
per family and per difficulty band; a renderer passing one family does not
automatically validate all families routed to it.
"""
    VISUAL_DOC.write_text(visual_doc, encoding="utf-8")


if __name__ == "__main__":
    main()
