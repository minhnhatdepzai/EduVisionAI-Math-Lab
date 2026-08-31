from datetime import datetime, timezone
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from app.core.config import Settings
from app.dependencies import Storage, TeacherUser, get_app_settings
from app.schemas.math_lab import (
    MathDocumentAnalysis,
    MathLabCapabilities,
    MathLabFeedbackCreate,
    MathLabFeedbackReceipt,
    MathLabHistoryCreate,
    MathLabHistoryEntry,
    MathLabHistoryList,
    MathLabPlanRequest,
    MathLabPlanResponse,
    MathTextAnalysisRequest,
)
from app.services.math_lab import MathAnalysisError, MathLabFoundationService, MathProblemAnalyzer
from app.services.math_lab.analyzer import ACCEPTED_IMAGE_TYPES


router = APIRouter(prefix="/math-lab", tags=["math-lab"])
foundation = MathLabFoundationService()


def _analyzer(settings: Settings) -> MathProblemAnalyzer:
    return MathProblemAnalyzer(settings)


def _image_type(payload: bytes) -> str | None:
    if payload.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if payload.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if len(payload) >= 12 and payload[:4] == b"RIFF" and payload[8:12] == b"WEBP":
        return "image/webp"
    return None


def _analysis_http_error(exc: MathAnalysisError) -> HTTPException:
    return HTTPException(exc.status_code, exc.message)


@router.get("/capabilities", response_model=MathLabCapabilities)
async def math_lab_capabilities(
    _user: TeacherUser,
    settings: Settings = Depends(get_app_settings),
) -> MathLabCapabilities:
    return await _analyzer(settings).capabilities()


@router.post("/analyze/text", response_model=MathDocumentAnalysis)
async def analyze_math_text(
    payload: MathTextAnalysisRequest,
    _user: TeacherUser,
    settings: Settings = Depends(get_app_settings),
) -> MathDocumentAnalysis:
    try:
        return await _analyzer(settings).analyze_text(payload.text, payload.grade_hint)
    except MathAnalysisError as exc:
        raise _analysis_http_error(exc) from exc


@router.post("/analyze/image", response_model=MathDocumentAnalysis)
async def analyze_math_image(
    _user: TeacherUser,
    file: Annotated[UploadFile, File(...)],
    grade_hint: Annotated[int | None, Form(ge=1, le=9)] = None,
    settings: Settings = Depends(get_app_settings),
) -> MathDocumentAnalysis:
    payload = await file.read(settings.math_lab_max_image_bytes + 1)
    if not payload:
        raise HTTPException(422, "Ảnh đề toán rỗng")
    if len(payload) > settings.math_lab_max_image_bytes:
        raise HTTPException(413, "Ảnh đề toán vượt quá dung lượng cho phép")
    detected_type = _image_type(payload)
    if detected_type not in ACCEPTED_IMAGE_TYPES:
        raise HTTPException(415, "Chỉ hỗ trợ ảnh JPEG, PNG hoặc WEBP hợp lệ")
    try:
        return await _analyzer(settings).analyze_image(payload, detected_type, grade_hint)
    except MathAnalysisError as exc:
        raise _analysis_http_error(exc) from exc


@router.post("/plan", response_model=MathLabPlanResponse)
async def plan_math_scene(
    payload: MathLabPlanRequest,
    _user: TeacherUser,
) -> MathLabPlanResponse:
    """Validate a semantic model and produce a deterministic renderer-neutral plan.

    Provider output reaches this endpoint after structured validation.
    Planning stays deterministic and vendor-neutral; teacher feedback is
    collected after the resulting simulation instead of blocking the flow.
    """

    return foundation.plan(
        payload.semantic_model,
        payload.requested_visualizations,
    )


@router.get("/history", response_model=MathLabHistoryList)
async def list_math_lab_history(
    user: TeacherUser,
    storage: Storage,
) -> MathLabHistoryList:
    items = await storage.list_math_lab_history(str(user.id))
    return MathLabHistoryList(items=items)


@router.post("/history", response_model=MathLabHistoryList, status_code=201)
async def save_math_lab_history(
    payload: MathLabHistoryCreate,
    user: TeacherUser,
    storage: Storage,
) -> MathLabHistoryList:
    model = payload.semantic_model
    entry = MathLabHistoryEntry(
        id=uuid4(),
        created_at=datetime.now(timezone.utc),
        source_type=payload.source_type,
        source_text=model.source_text,
        grade=model.grade,
        domain=model.domain,
        problem_type=model.problem_type,
        semantic_model=model,
    )
    items = await storage.append_math_lab_history(
        str(user.id), entry.model_dump(mode="json")
    )
    return MathLabHistoryList(items=items)


@router.post("/feedback", response_model=MathLabFeedbackReceipt, status_code=201)
async def submit_math_lab_feedback(
    payload: MathLabFeedbackCreate,
    user: TeacherUser,
    storage: Storage,
) -> MathLabFeedbackReceipt:
    record = await storage.create_record(
        "math-lab-feedback",
        {
            "user_id": str(user.id),
            "history_id": str(payload.history_id) if payload.history_id else None,
            "rating": payload.rating,
            "category": payload.category,
            "comment": payload.comment,
            "expected_correction": payload.expected_correction,
            "source_text": payload.semantic_model.source_text,
            "grade": payload.semantic_model.grade,
            "problem_type": payload.semantic_model.problem_type,
            "semantic_model": payload.semantic_model.model_dump(mode="json"),
            "scene": payload.scene.model_dump(mode="json"),
            "status": "pending_review",
            # A human review/approval job may switch this to true. Raw user
            # feedback must never become online training data automatically.
            "training_eligible": False,
        },
    )
    return MathLabFeedbackReceipt(
        id=record["id"],
        status="pending_review",
        created_at=record["created_at"],
        message="Đã lưu góp ý để đội ngũ duyệt trước khi đưa vào bộ dữ liệu cải thiện AI.",
    )
