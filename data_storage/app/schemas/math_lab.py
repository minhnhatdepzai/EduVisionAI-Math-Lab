from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class MathLabHistoryEntry(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    id: UUID
    created_at: datetime
    source_type: Literal["text", "image"]
    source_text: str | None = Field(default=None, max_length=20_000)
    grade: int = Field(ge=1, le=9)
    domain: str = Field(min_length=1, max_length=64)
    problem_type: str = Field(min_length=1, max_length=96)
    semantic_model: dict[str, Any]


class MathLabHistoryList(BaseModel):
    items: list[MathLabHistoryEntry] = Field(max_length=5)
