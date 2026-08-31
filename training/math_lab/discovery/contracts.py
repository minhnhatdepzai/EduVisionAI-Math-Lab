from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urlparse


USAGE_POLICIES = {
    "TRAIN_ALLOWED",
    "EVAL_ALLOWED",
    "TAXONOMY_ONLY",
    "METADATA_ONLY",
    "UNKNOWN",
    "FORBIDDEN",
}
SHA256 = re.compile(r"^[0-9a-f]{64}$")


@dataclass(frozen=True, slots=True)
class SourceManifestRecord:
    url: str
    domain: str
    grade: int | None
    exam_type: str
    school: str
    year: str
    book_series: str
    retrieved_at: str
    content_hash: str
    robots_checked: bool
    license_status: str
    usage: str
    question_count: int = 0
    families_discovered: list[str] = field(default_factory=list)
    robots_allowed: bool | None = None
    notes: str = ""

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "SourceManifestRecord":
        record = cls(**value)
        parsed = urlparse(record.url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError(f"Invalid source URL: {record.url}")
        if record.domain != parsed.netloc.lower():
            raise ValueError(f"Manifest domain does not match URL: {record.url}")
        if record.grade is not None and not 1 <= record.grade <= 9:
            raise ValueError("grade must be null or an integer from 1 to 9")
        if record.usage not in USAGE_POLICIES:
            raise ValueError(f"Unsupported usage policy: {record.usage}")
        if record.content_hash and not SHA256.fullmatch(record.content_hash):
            raise ValueError("content_hash must be an empty string or lowercase SHA-256")
        if record.question_count < 0:
            raise ValueError("question_count cannot be negative")
        if not record.robots_checked and record.robots_allowed is not None:
            raise ValueError("robots_allowed requires robots_checked=true")
        if record.usage == "TRAIN_ALLOWED" and record.license_status.upper() in {"", "UNKNOWN"}:
            raise ValueError("TRAIN_ALLOWED requires an explicit license status")
        return record

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    if not path.exists():
        return records
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"{path}:{line_number}: invalid JSON") from exc
        if not isinstance(value, dict):
            raise ValueError(f"{path}:{line_number}: record must be an object")
        records.append(value)
    return records


def write_jsonl(path: Path, records: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rendered = "".join(json.dumps(item, ensure_ascii=False, sort_keys=True) + "\n" for item in records)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(rendered, encoding="utf-8")
    temporary.replace(path)
