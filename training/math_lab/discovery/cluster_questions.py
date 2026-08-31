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
from training.math_lab.discovery.fingerprint import semantic_fingerprint, semantic_signature


def cluster(records: list[dict]) -> list[dict]:
    groups: dict[str, list[dict]] = defaultdict(list)
    for record in records:
        groups[semantic_fingerprint(record)].append(record)
    return [
        {
            "fingerprint": fingerprint,
            "frequency": len(items),
            "semantic_signature": semantic_signature(items[0]),
            "known_families": sorted({str(item["family"]) for item in items if item.get("family")}),
            "example_ids": [str(item.get("id", "")) for item in items[:5]],
        }
        for fingerprint, items in sorted(groups.items())
    ]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    args = parser.parse_args()
    print(json.dumps(cluster(read_jsonl(args.input)), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
