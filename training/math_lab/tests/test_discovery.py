from __future__ import annotations

from training.math_lab.discovery.audit_family_saturation import saturation_report
from training.math_lab.discovery.contracts import SourceManifestRecord
from training.math_lab.discovery.classify_families import classify
from training.math_lab.discovery.discover_new_families import candidates
from training.math_lab.discovery.extract_questions import extract
from training.math_lab.discovery.fingerprint import semantic_fingerprint
from training.math_lab.autolearn import STAGES
from training.math_lab.benchmarks.run_model_league import league


def sample(value: int, name: str) -> dict:
    return {
        "id": name,
        "grade_band": "5-6",
        "domain": "ratio",
        "operators": ["fraction_of", "remaining_of", "fraction_of"],
        "quantities": [
            {"role": "total", "value": value, "unit": "kg", "label": name},
            {"role": "numerator", "value": 2, "unit": "one"},
            {"role": "denominator", "value": 5, "unit": "one"},
        ],
        "relationships": [{
            "type": "remaining_of",
            "participants": {"whole": "q1", "part": "q2"},
        }],
        "unknowns": [{"role": "result", "kind": "mass", "unit": "kg"}],
        "constraints": [],
        "sequence_structure": "whole_then_remainder_becomes_whole",
    }


def test_fingerprint_ignores_numbers_names_and_context() -> None:
    assert semantic_fingerprint(sample(160, "gạo")) == semantic_fingerprint(sample(240, "sách"))


def test_unknown_cluster_becomes_candidate_only_after_frequency_gate() -> None:
    records = [sample(100 + index, f"sample-{index}") for index in range(5)]
    assert candidates(records, 5)[0]["frequency"] == 5
    assert candidates(records, 6) == []


def test_saturation_requires_three_full_batches() -> None:
    records = [
        {"grade": 1, "batch_id": batch, "is_new_family": False}
        for batch in ("001", "002", "003")
        for _ in range(500)
    ]
    report = saturation_report(records, threshold=0.005, minimum_batch=500, consecutive=3)
    assert report["grades"]["1"]["saturated"] is True
    assert report["grades"]["2"]["saturated"] is False


def test_manifest_forbids_unlicensed_training() -> None:
    try:
        SourceManifestRecord.from_dict({
            "url": "https://example.com/exam",
            "domain": "example.com",
            "grade": 1,
            "exam_type": "semester",
            "school": "",
            "year": "2026",
            "book_series": "",
            "retrieved_at": "2026-08-27T00:00:00Z",
            "content_hash": "",
            "robots_checked": True,
            "license_status": "UNKNOWN",
            "usage": "TRAIN_ALLOWED",
        })
    except ValueError as exc:
        assert "explicit license" in str(exc)
    else:
        raise AssertionError("unlicensed source was allowed into training")


def manifest_record(usage: str, license_status: str = "CC-BY-4.0") -> dict:
    return {
        "url": "https://example.com/exam",
        "domain": "example.com",
        "grade": 4,
        "exam_type": "semester",
        "school": "Example",
        "year": "2026",
        "book_series": "",
        "retrieved_at": "2026-08-27T00:00:00Z",
        "content_hash": "a" * 64,
        "robots_checked": True,
        "robots_allowed": True,
        "license_status": license_status,
        "usage": usage,
    }


def test_question_extraction_requires_train_or_eval_policy() -> None:
    document = [{
        "source_url": "https://example.com/exam",
        "questions": [{"text": "  Tính   1 + 2  ", "question_number": "1"}],
    }]
    records = extract(document, [manifest_record("TRAIN_ALLOWED")])
    assert records[0]["normalized_text"] == "Tính 1 + 2"
    assert records[0]["training_eligible"] is True

    try:
        extract(document, [manifest_record("TAXONOMY_ONLY", "UNKNOWN")])
    except ValueError as exc:
        assert "forbids question-text extraction" in str(exc)
    else:
        raise AssertionError("taxonomy-only source text was extracted")


def test_classifier_never_forces_unknown_into_nearest_family() -> None:
    known_record = {**sample(160, "known"), "family": "ratio_total_parts"}
    unknown_record = {**sample(240, "unknown"), "family": "new_relation_family"}
    result = classify(
        [known_record, unknown_record],
        {"families": [{"id": "ratio_total_parts"}]},
    )
    assert result[0]["family_status"] == "KNOWN_FAMILY"
    assert result[1]["family_status"] == "UNKNOWN_CLUSTER"
    assert result[1]["catalog_family"] is None


def test_autolearn_cycle_stops_training_before_preference_stages() -> None:
    assert STAGES.index("TRAIN_SFT") < STAGES.index("EVALUATE")
    assert STAGES.index("EVALUATE") < STAGES.index("TRAIN_DPO_OR_GRPO_IF_ELIGIBLE")
    assert STAGES[-1] == "REPORT"


def test_model_league_rejects_incomplete_smoke_candidate() -> None:
    report = league({
        "candidates": [{
            "id": "smoke",
            "eligible": False,
            "metrics": {"eval_loss": 0.1},
            "reason": "pipeline only",
        }]
    })
    assert report["winner"] is None
    assert report["production_change_allowed"] is False
    assert report["rejected"][0]["id"] == "smoke"
