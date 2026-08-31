#!/usr/bin/env python3
"""Report only fully quality-gated Math Lab model challengers."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
DEFAULT_LEDGER = ROOT / "training/math_lab/benchmarks/model_ledger.json"
REQUIRED_METRICS = {
    "schema_validity",
    "ocr_accuracy",
    "semantic_role_accuracy",
    "visual_intent_accuracy",
    "unknown_leakage",
    "p95_latency_seconds",
    "peak_vram_mib",
}


def league(ledger: dict) -> dict:
    accepted = []
    rejected = []
    for candidate in ledger.get("candidates", []):
        metrics = candidate.get("metrics") or {}
        missing = sorted(REQUIRED_METRICS - set(metrics))
        if not candidate.get("eligible") or missing:
            rejected.append({
                "id": candidate.get("id"),
                "missing_metrics": missing,
                "reason": candidate.get("reason") or "not eligible",
            })
            continue
        gates = (
            metrics["schema_validity"] == 1
            and metrics["unknown_leakage"] == 0
            and metrics["semantic_role_accuracy"] >= 0.99
            and metrics["visual_intent_accuracy"] >= 0.98
        )
        if not gates:
            rejected.append({"id": candidate["id"], "missing_metrics": [], "reason": "quality gate failed"})
            continue
        accepted.append(candidate)
    accepted.sort(
        key=lambda item: (
            item["metrics"]["semantic_role_accuracy"],
            item["metrics"]["visual_intent_accuracy"],
            -item["metrics"]["p95_latency_seconds"],
        ),
        reverse=True,
    )
    return {
        "winner": accepted[0]["id"] if accepted else None,
        "production_change_allowed": bool(accepted),
        "leaderboard": accepted,
        "rejected": rejected,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ledger", type=Path, default=DEFAULT_LEDGER)
    args = parser.parse_args()
    print(json.dumps(league(json.loads(args.ledger.read_text(encoding="utf-8"))), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
