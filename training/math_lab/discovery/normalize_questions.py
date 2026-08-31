#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from training.math_lab.discovery.contracts import read_jsonl, write_jsonl


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.replace("–", "−").replace("—", "−")).strip()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    records = read_jsonl(args.input)
    for record in records:
        source = str(record.get("normalized_text") or record.get("problem_text") or record.get("text") or "")
        record["normalized_text"] = normalize_text(source)
    write_jsonl(args.output, records)


if __name__ == "__main__":
    main()
