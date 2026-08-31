#!/usr/bin/env python3
"""Build an immutable, content-addressed descriptor for the current dataset."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
OUTPUT = ROOT / "training/math_lab/dataset_version.json"
INPUTS = {
    "generated_manifest": ROOT / "training/math_lab/data/generated/manifest.json",
    "source_manifest": ROOT / "training/math_lab/sources/source_manifest.jsonl",
    "family_catalog": ROOT / "training/math_lab/catalogs/grade_1_9_exam_families.json",
    "semantic_prompt": ROOT / "training/math_lab/prompts/math_scene_analyzer_system.txt",
    "generator": ROOT / "training/math_lab/scripts/prepare_sft.py",
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def contamination_scan(manifest: dict) -> dict:
    seen: dict[str, str] = {}
    overlaps: list[dict[str, str]] = []
    unique_by_split: dict[str, int] = {}
    data_root = ROOT / "training/math_lab/data/generated"
    for split, metadata in manifest["splits"].items():
        stems: set[str] = set()
        with (data_root / metadata["path"]).open(encoding="utf-8") as stream:
            for line in stream:
                record = json.loads(line)
                target = json.loads(record["conversations"][1]["value"])
                for question in target["questions"]:
                    stems.add(question["stem"])
        unique_by_split[split] = len(stems)
        for stem in stems:
            previous = seen.setdefault(stem, split)
            if previous != split:
                overlaps.append({"stem_hash": hashlib.sha256(stem.encode()).hexdigest(), "left": previous, "right": split})
    return {
        "status": "passed" if not overlaps else "failed",
        "duplicate_stems_across_splits": len(overlaps),
        "unique_stems_by_split": unique_by_split,
        "command": "python training/math_lab/scripts/audit_sft.py",
        "required": "zero duplicate stems across train, validation and test",
    }


def main() -> None:
    hashes = {name: digest(path) for name, path in INPUTS.items()}
    combined = hashlib.sha256(
        json.dumps(hashes, sort_keys=True).encode("utf-8")
    ).hexdigest()
    manifest = json.loads(INPUTS["generated_manifest"].read_text(encoding="utf-8"))
    source_records = [
        json.loads(line)
        for line in INPUTS["source_manifest"].read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    descriptor = {
        "schema_version": "1.0",
        "dataset_id": f"mathlab-semantic-{combined[:16]}",
        "content_digest": combined,
        "input_hashes": hashes,
        "seed": manifest["seed"],
        "families": manifest["families"],
        "splits": manifest["splits"],
        "modalities": manifest["modalities"],
        "web_source_usage": dict(Counter(item["usage"] for item in source_records)),
        "web_records_in_training": sum(item["usage"] == "TRAIN_ALLOWED" for item in source_records),
        "contamination_gate": contamination_scan(manifest),
    }
    OUTPUT.write_text(json.dumps(descriptor, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"dataset_id": descriptor["dataset_id"], "output": str(OUTPUT.relative_to(ROOT))}))


if __name__ == "__main__":
    main()
