from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.api.dependencies import (
    get_math_lab_history_repository,
    require_internal_api_key,
)
from app.databases.redis.math_lab_history_repository import MathLabHistoryRepository
from app.schemas.math_lab import MathLabHistoryEntry, MathLabHistoryList


router = APIRouter(
    prefix="/v1/math-lab",
    tags=["math-lab-storage"],
    dependencies=[Depends(require_internal_api_key)],
)


@router.get("/users/{user_id}/history", response_model=MathLabHistoryList)
async def list_math_lab_history(
    user_id: UUID,
    repository: MathLabHistoryRepository = Depends(get_math_lab_history_repository),
) -> MathLabHistoryList:
    return MathLabHistoryList(items=await repository.list(user_id))


@router.post(
    "/users/{user_id}/history",
    response_model=MathLabHistoryList,
    status_code=status.HTTP_201_CREATED,
)
async def append_math_lab_history(
    user_id: UUID,
    body: MathLabHistoryEntry,
    repository: MathLabHistoryRepository = Depends(get_math_lab_history_repository),
) -> MathLabHistoryList:
    items = await repository.append(user_id, body.model_dump(mode="json"))
    return MathLabHistoryList(items=items)
