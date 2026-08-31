#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from training.math_lab.discovery.contracts import SourceManifestRecord, read_jsonl


DEFAULT_MANIFEST = ROOT / "training/math_lab/sources/source_manifest.jsonl"


def audit_manifest(path: Path) -> dict:
    raw = read_jsonl(path)
    records = [SourceManifestRecord.from_dict(item) for item in raw]
    urls = [item.url for item in records]
    if len(urls) != len(set(urls)):
        raise ValueError("source_manifest contains duplicate URLs")
    return {
        "manifest": path.relative_to(ROOT).as_posix(),
        "records": len(records),
        "domains": dict(Counter(item.domain for item in records)),
        "usage": dict(Counter(item.usage for item in records)),
        "grades": dict(Counter(str(item.grade) for item in records if item.grade is not None)),
        "robots_disallowed": sum(item.robots_allowed is False for item in records),
        "train_allowed": sum(item.usage == "TRAIN_ALLOWED" for item in records),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    args = parser.parse_args()
    print(json.dumps(audit_manifest(args.manifest), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
