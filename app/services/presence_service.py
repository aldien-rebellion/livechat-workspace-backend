import logging
import uuid
from datetime import datetime, timezone
from typing import List, Optional

import redis.asyncio as aioredis

from app.config.redis import redis_client

logger = logging.getLogger(__name__)


class PresenceService:
    def __init__(self, client: Optional[aioredis.Redis] = None, ttl: int = 60):
        self.redis: aioredis.Redis = client or redis_client
        self.ttl = ttl

    async def mark_online(
        self, user_id: uuid.UUID, workspace_id: Optional[uuid.UUID] = None
    ) -> bool:
        key = f"presence:user:{user_id}"
        was_offline = await self.redis.get(key) is None

        # Set sliding TTL for user presence
        await self.redis.set(key, "online", ex=self.ttl)

        meta_key = f"presence:user:{user_id}:meta"
        now_iso = datetime.now(timezone.utc).isoformat()
        await self.redis.hset(
            meta_key, mapping={"last_seen": now_iso, "status": "online"}
        )

        if workspace_id:
            ws_set = f"presence:workspace:{workspace_id}:online"
            await self.redis.sadd(ws_set, str(user_id))

        return was_offline

    async def heartbeat(
        self, user_id: uuid.UUID, workspace_id: Optional[uuid.UUID] = None
    ) -> None:
        key = f"presence:user:{user_id}"
        await self.redis.set(key, "online", ex=self.ttl)
        if workspace_id:
            ws_set = f"presence:workspace:{workspace_id}:online"
            await self.redis.sadd(ws_set, str(user_id))

    async def mark_offline(
        self, user_id: uuid.UUID, workspace_id: Optional[uuid.UUID] = None
    ) -> None:
        key = f"presence:user:{user_id}"
        await self.redis.delete(key)

        meta_key = f"presence:user:{user_id}:meta"
        now_iso = datetime.now(timezone.utc).isoformat()
        await self.redis.hset(
            meta_key, mapping={"last_seen": now_iso, "status": "offline"}
        )

        if workspace_id:
            ws_set = f"presence:workspace:{workspace_id}:online"
            await self.redis.srem(ws_set, str(user_id))

    async def is_user_online(self, user_id: uuid.UUID) -> bool:
        key = f"presence:user:{user_id}"
        val = await self.redis.get(key)
        return val is not None

    async def get_online_users(self, workspace_id: uuid.UUID) -> List[str]:
        ws_set = f"presence:workspace:{workspace_id}:online"
        members = await self.redis.smembers(ws_set)
        online_users = []
        expired_users = []

        for uid_str in members:
            key = f"presence:user:{uid_str}"
            if await self.redis.get(key) is not None:
                online_users.append(uid_str)
            else:
                expired_users.append(uid_str)

        if expired_users:
            await self.redis.srem(ws_set, *expired_users)

        return online_users


presence_service = PresenceService()
