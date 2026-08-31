"""Temporary, per-teacher Math Lab history backed by a capped Redis list."""

from __future__ import annotations

import json
from typing import Any
from uuid import UUID

from redis.asyncio import Redis


class MathLabHistoryRepository:
    """Keep the five newest completed simulations and discard the oldest.

    LPUSH + LTRIM run in one Redis transaction, so a sixth write can never
    expose more than five entries to another request.
    """

    limit = 5

    def __init__(self, redis: Redis, *, ttl_seconds: int) -> None:
        self.redis = redis
        self.ttl_seconds = ttl_seconds

    @staticmethod
    def key(user_id: UUID | str) -> str:
        return f"eduvision:math-lab:history:{user_id}"

    async def append(self, user_id: UUID | str, entry: dict[str, Any]) -> list[dict[str, Any]]:
        key = self.key(user_id)
        encoded = json.dumps(entry, ensure_ascii=False, separators=(",", ":"))
        async with self.redis.pipeline(transaction=True) as transaction:
            transaction.lpush(key, encoded)
            transaction.ltrim(key, 0, self.limit - 1)
            transaction.expire(key, self.ttl_seconds)
            await transaction.execute()
        return await self.list(user_id)

    async def list(self, user_id: UUID | str) -> list[dict[str, Any]]:
        values = await self.redis.lrange(self.key(user_id), 0, self.limit - 1)
        return [json.loads(value) for value in values]
