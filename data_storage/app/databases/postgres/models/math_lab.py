"""Persistent teacher feedback for Math Lab review and future training."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import Boolean, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.databases.postgres.base import Base


class MathLabFeedback(Base):
    __tablename__ = "math_lab_feedback"
    __table_args__ = (
        Index("ix_math_lab_feedback_status_created", "status", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    history_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), default=None, index=True
    )
    rating: Mapped[str] = mapped_column(String(24))
    category: Mapped[str] = mapped_column(String(32))
    comment: Mapped[str | None] = mapped_column(Text, default=None)
    expected_correction: Mapped[str | None] = mapped_column(Text, default=None)
    source_text: Mapped[str | None] = mapped_column(Text, default=None)
    grade: Mapped[int] = mapped_column()
    problem_type: Mapped[str] = mapped_column(String(96))
    semantic_model: Mapped[dict[str, Any]] = mapped_column(JSONB)
    scene: Mapped[dict[str, Any]] = mapped_column(JSONB)
    status: Mapped[str] = mapped_column(String(32), default="pending_review", index=True)
    training_eligible: Mapped[bool] = mapped_column(Boolean, default=False)
