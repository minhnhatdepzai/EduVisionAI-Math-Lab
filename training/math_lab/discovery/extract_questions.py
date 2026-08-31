#!/usr/bin/env python3
"""Extract questions only from local, explicitly permitted source artifacts.

This command never downloads a page and never treats TAXONOMY_ONLY metadata as
training text.  A crawler or a human must first register the source in
``source_manifest.jsonl`` and provide a local JSONL artifact whose ownership is
known.  Every emitted record keeps the source policy so later jobs cannot lose
its provenance.
"""

from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from training.math_lab.discovery.contracts import (
    SourceManifestRecord,
    read_jsonl,
    write_jsonl,
)
from training.math_lab.discovery.normalize_questions import normalize_text


EXTRACTABLE_USAGE = {"TRAIN_ALLOWED", "EVAL_ALLOWED"}


def extract(
    documents: list[dict],
    manifest_records: list[dict],
) -> list[dict]:
    manifest = {
        record.url: record
        for record in (SourceManifestRecord.from_dict(item) for item in manifest_records)
    }
    output: list[dict] = []
    for document in documents:
        source_url = str(document.get("source_url") or "")
        source = manifest.get(source_url)
        if source is None:
            raise ValueError(f"Source is absent from source_manifest: {source_url}")
        if source.usage not in EXTRACTABLE_USAGE:
            raise ValueError(
                f"Source policy {source.usage} forbids question-text extraction: {source_url}"
            )
        questions = document.get("questions")
        if not isinstance(questions, list) or not questions:
            raise ValueError(f"Local artifact has no questions array: {source_url}")
        for index, question in enumerate(questions, 1):
            if not isinstance(question, dict):
                raise ValueError(f"Question {index} must be an object: {source_url}")
            text = normalize_text(str(question.get("text") or ""))
            if not text:
                raise ValueError(f"Question {index} has empty text: {source_url}")
            record_id = hashlib.sha256(
                f"{source.content_hash}:{index}:{text}".encode("utf-8")
            ).hexdigest()
            output.append({
                "id": record_id,
                "source_url": source.url,
                "source_content_hash": source.content_hash,
                "source_usage": source.usage,
                "license_status": source.license_status,
                "training_eligible": source.usage == "TRAIN_ALLOWED",
                "grade": question.get("grade", source.grade),
                "question_number": str(question.get("question_number") or index),
                "normalized_text": text,
                "answer": question.get("answer"),
                "choices": question.get("choices") or [],
            })
    return output


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Split a permitted local artifact; this command does not crawl the web"
    )
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument(
        "--manifest",
        type=Path,
        default=ROOT / "training/math_lab/sources/source_manifest.jsonl",
    )
    args = parser.parse_args()
    write_jsonl(args.output, extract(read_jsonl(args.input), read_jsonl(args.manifest)))


if __name__ == "__main__":
    main()
