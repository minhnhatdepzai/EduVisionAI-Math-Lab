"""Resumable, fail-closed Math Lab improvement cycle.

Run with ``python -m training.math_lab.autolearn run``.  The cycle records
evidence for every stage and stops at the first failed gate.  It never promotes
an adapter or starts preference/RL training without the required reviewed data.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_STATE = ROOT / "training/math_lab/cache/autolearn-state.json"
GENERATED = ROOT / "training/math_lab/data/generated"
STAGES = [
    "DISCOVER",
    "CLASSIFY",
    "GENERATE",
    "VERIFY",
    "BUILD_DATASET",
    "TRAIN_SFT",
    "EVALUATE",
    "MINE_FAILURES",
    "BUILD_PREFERENCES",
    "TRAIN_DPO_OR_GRPO_IF_ELIGIBLE",
    "REEVALUATE",
    "CANARY_DECISION",
    "REPORT",
]
FINGERPRINT_INPUTS = (
    ROOT / "training/math_lab/data/generated/manifest.json",
    ROOT / "training/math_lab/sources/source_manifest.jsonl",
    ROOT / "training/math_lab/catalogs/grade_1_9_exam_families.json",
    ROOT / "training/math_lab/prompts/math_scene_analyzer_system.txt",
    ROOT / "training/math_lab/scripts/prepare_sft.py",
)


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def cycle_fingerprint() -> str:
    digest = hashlib.sha256()
    for path in FINGERPRINT_INPUTS:
        digest.update(path.relative_to(ROOT).as_posix().encode("utf-8"))
        digest.update(hashlib.sha256(path.read_bytes()).digest())
    return digest.hexdigest()


def run_json(command: list[str]) -> dict[str, Any]:
    completed = subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    if completed.returncode:
        raise RuntimeError(completed.stdout[-4000:])
    try:
        return json.loads(completed.stdout)
    except json.JSONDecodeError:
        return {"output_tail": completed.stdout[-2000:]}


def load_state(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"schema_version": "1.0", "created_at": now(), "stages": {}}
    return json.loads(path.read_text(encoding="utf-8"))


def save_state(path: Path, state: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    state["updated_at"] = now()
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def execute_stage(stage: str, regenerate: bool, allow_training: bool) -> dict[str, Any]:
    python = sys.executable
    if stage == "DISCOVER":
        report = run_json([python, "training/math_lab/discovery/discover_sources.py"])
        return {"status": "passed", "evidence": report}
    if stage == "CLASSIFY":
        report = run_json([python, "training/math_lab/scripts/audit_exam_coverage.py"])
        if not report.get("valid"):
            raise RuntimeError(json.dumps(report.get("errors"), ensure_ascii=False))
        return {"status": "passed", "evidence": report["summary"]}
    if stage == "GENERATE":
        if regenerate:
            run_json([python, "training/math_lab/scripts/prepare_sft.py"])
        manifest = json.loads((GENERATED / "manifest.json").read_text(encoding="utf-8"))
        missing = [
            item["path"] for item in manifest["splits"].values()
            if not (GENERATED / item["path"]).is_file()
        ]
        if missing:
            raise RuntimeError(f"Missing generated splits: {missing}")
        return {"status": "passed", "evidence": manifest["splits"], "regenerated": regenerate}
    if stage == "VERIFY":
        report = run_json([python, "training/math_lab/scripts/audit_sft.py"])
        summary = {
            split: {
                "records": values["records"],
                "schema_validity": values["schema_validity"],
                "unknown_leakage": values["unknown_leakage"],
                "renderer_decision_accuracy": values["renderer_decision_accuracy"],
            }
            for split, values in report.items()
        }
        return {"status": "passed", "evidence": summary}
    if stage == "BUILD_DATASET":
        report = run_json([python, "training/math_lab/scripts/build_dataset_version.py"])
        return {"status": "passed", "evidence": report}
    if stage == "TRAIN_SFT":
        training_python = ROOT / "training/math_lab/.venv/bin/python"
        executable = str(training_python if training_python.exists() else Path(python))
        report = run_json([executable, "training/math_lab/scripts/train_qlora.py", "--dry-run"])
        if report["free_vram_mib"] < report["required_free_vram_mib"]:
            return {
                "status": "blocked",
                "reason": "insufficient_free_vram",
                "evidence": report,
            }
        if not allow_training:
            return {
                "status": "blocked",
                "reason": "resource_gate_passed_but_training_flag_not_set",
                "evidence": report,
            }
        result = run_json([executable, "training/math_lab/scripts/train_qlora.py"])
        return {"status": "passed", "evidence": result}
    return {
        "status": "blocked",
        "reason": "requires_a_quality_gated_sft_candidate_and_reviewed_inputs",
    }


def run_cycle(state_path: Path, regenerate: bool, allow_training: bool) -> dict[str, Any]:
    state = load_state(state_path)
    fingerprint = cycle_fingerprint()
    if state.get("input_fingerprint") != fingerprint:
        state = {
            "schema_version": "1.0",
            "created_at": now(),
            "input_fingerprint": fingerprint,
            "stages": {},
        }
    for stage in STAGES:
        previous = state["stages"].get(stage)
        if previous and previous.get("status") == "passed":
            continue
        try:
            result = execute_stage(stage, regenerate, allow_training)
        except Exception as exc:  # noqa: BLE001 - persisted gate evidence
            result = {"status": "failed", "reason": str(exc)}
        result["checked_at"] = now()
        state["stages"][stage] = result
        save_state(state_path, state)
        if result["status"] != "passed":
            break
    return state


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("run", "status"))
    parser.add_argument("--state", type=Path, default=DEFAULT_STATE)
    parser.add_argument("--regenerate", action="store_true")
    parser.add_argument("--allow-training", action="store_true")
    args = parser.parse_args()
    state = (
        run_cycle(args.state, args.regenerate, args.allow_training)
        if args.command == "run"
        else load_state(args.state)
    )
    print(json.dumps(state, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
