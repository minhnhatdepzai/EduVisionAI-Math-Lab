#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from training.math_lab.discovery.cluster_questions import cluster
from training.math_lab.discovery.contracts import read_jsonl


def candidates(records: list[dict], minimum_frequency: int) -> list[dict]:
    return [
        {
            "candidate_family": f"candidate_{item['fingerprint'][:12]}",
            "semantic_signature": item["semantic_signature"],
            "nearest_families": [],
            "frequency": item["frequency"],
            "examples": item["example_ids"],
            "status": "UNKNOWN_CLUSTER",
        }
        for item in cluster(records)
        if not item["known_families"] and item["frequency"] >= minimum_frequency
    ]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("--minimum-frequency", type=int, default=5)
    args = parser.parse_args()
    print(json.dumps(candidates(read_jsonl(args.input), args.minimum_frequency), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
