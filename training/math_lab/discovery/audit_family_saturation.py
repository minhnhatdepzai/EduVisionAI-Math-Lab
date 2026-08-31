#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from training.math_lab.discovery.contracts import read_jsonl


def saturation_report(records: list[dict], threshold: float, minimum_batch: int, consecutive: int) -> dict:
    batches: dict[tuple[int, str], list[dict]] = defaultdict(list)
    for item in records:
        grade = int(item["grade"])
        if not 1 <= grade <= 9:
            raise ValueError("grade must be from 1 to 9")
        batches[(grade, str(item["batch_id"]))].append(item)
    by_grade: dict[str, dict] = {}
    for grade in range(1, 10):
        grade_batches = []
        for (candidate_grade, batch_id), items in sorted(batches.items(), key=lambda pair: pair[0][1]):
            if candidate_grade != grade:
                continue
            new_count = sum(bool(item.get("is_new_family")) for item in items)
            grade_batches.append({
                "batch_id": batch_id,
                "questions": len(items),
                "new_families": new_count,
                "new_family_rate": new_count / len(items),
                "qualifies": len(items) >= minimum_batch and new_count / len(items) < threshold,
            })
        streak = 0
        for batch in grade_batches:
            streak = streak + 1 if batch["qualifies"] else 0
        by_grade[str(grade)] = {
            "saturated": streak >= consecutive,
            "qualifying_streak": streak,
            "batches": grade_batches,
        }
    return {
        "threshold": threshold,
        "minimum_batch": minimum_batch,
        "consecutive_batches": consecutive,
        "grades": by_grade,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("--threshold", type=float, default=0.005)
    parser.add_argument("--minimum-batch", type=int, default=500)
    parser.add_argument("--consecutive", type=int, default=3)
    args = parser.parse_args()
    print(json.dumps(
        saturation_report(read_jsonl(args.input), args.threshold, args.minimum_batch, args.consecutive),
        ensure_ascii=False,
        indent=2,
    ))


if __name__ == "__main__":
    main()
