from __future__ import annotations

import hashlib
import json
from typing import Any


def _role(item: dict[str, Any]) -> str:
    return str(item.get("role") or item.get("kind") or "unknown")


def semantic_signature(record: dict[str, Any]) -> dict[str, Any]:
    """Return a context/number-independent mathematical structure.

    Exact names, values, labels and wording are deliberately excluded. Two
    renamed/re-numbered problems cluster together only when their operator,
    roles, relationships, unknown and constraints agree.
    """

    quantities = sorted(
        (
            _role(item),
            str(item.get("unit") or "one"),
        )
        for item in record.get("quantities", [])
        if isinstance(item, dict)
    )
    relationships = sorted(
        (
            str(item.get("type") or "unknown"),
            tuple(sorted(str(key) for key in (item.get("participants") or {}))),
        )
        for item in record.get("relationships", record.get("relations", []))
        if isinstance(item, dict)
    )
    unknowns = sorted(
        (
            _role(item),
            str(item.get("kind") or "unknown"),
            str(item.get("unit") or "one"),
        )
        for item in record.get("unknowns", [])
        if isinstance(item, dict)
    )
    constraints = sorted(
        str(item.get("type") or "unknown")
        for item in record.get("constraints", [])
        if isinstance(item, dict)
    )
    operators = record.get("operators") or record.get("operation_sequence") or []
    if isinstance(operators, str):
        operators = [operators]
    return {
        "grade_band": record.get("grade_band"),
        "domain": record.get("domain"),
        "operators": [str(item) for item in operators],
        "quantity_roles": quantities,
        "relationships": relationships,
        "unknowns": unknowns,
        "constraints": constraints,
        "sequence_structure": record.get("sequence_structure"),
    }


def semantic_fingerprint(record: dict[str, Any]) -> str:
    encoded = json.dumps(
        semantic_signature(record),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()
