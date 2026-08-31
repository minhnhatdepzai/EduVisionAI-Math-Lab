#!/usr/bin/env python3
"""Separate exact catalog matches from structurally unknown clusters.

The classifier intentionally does not force a nearest known family.  A record
without an exact reviewed family ID remains ``UNKNOWN_CLUSTER`` and is grouped
by a context-independent semantic fingerprint for later review.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from training.math_lab.discovery.contracts import read_jsonl, write_jsonl
from training.math_lab.discovery.fingerprint import semantic_fingerprint, semantic_signature


def classify(records: list[dict], catalog: dict) -> list[dict]:
    known = {str(item["id"]) for item in catalog.get("families", [])}
    output: list[dict] = []
    for record in records:
        family = str(record.get("family") or record.get("problem_type") or "")
        exact = family in known
        enriched = dict(record)
        enriched.update({
            "family_status": "KNOWN_FAMILY" if exact else "UNKNOWN_CLUSTER",
            "catalog_family": family if exact else None,
            "semantic_fingerprint": semantic_fingerprint(record),
            "semantic_signature": semantic_signature(record),
        })
        output.append(enriched)
    return output


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument(
        "--catalog",
        type=Path,
        default=ROOT / "training/math_lab/catalogs/grade_1_9_exam_families.json",
    )
    args = parser.parse_args()
    catalog = json.loads(args.catalog.read_text(encoding="utf-8"))
    write_jsonl(args.output, classify(read_jsonl(args.input), catalog))


if __name__ == "__main__":
    main()
