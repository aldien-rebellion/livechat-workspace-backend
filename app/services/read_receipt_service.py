import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.channel import ChannelMember
from app.models.message import Message
from app.models.message_read import MessageRead
from app.services.channel_service import ChannelService
from app.services.redis_pubsub import redis_pubsub_manager


class ReadReceiptService:
    @classmethod
    async def mark_messages_read(
        cls,
        db: AsyncSession,
        channel_id: uuid.UUID,
        user_id: uuid.UUID,
        message_ids: List[uuid.UUID],
    ) -> Dict[str, Any]:
        if not await ChannelService.is_member(db, channel_id, user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Must be a channel member to mark messages as read",
            )

        now = datetime.now(timezone.utc)
        marked_ids: List[str] = []

        for msg_id in message_ids:
            stmt = (
                insert(MessageRead)
                .values(message_id=msg_id, user_id=user_id, read_at=now)
                .on_conflict_do_nothing(index_elements=["message_id", "user_id"])
            )
            await db.execute(stmt)
            marked_ids.append(str(msg_id))

        # Update last_read_at on channel member
        member_stmt = select(ChannelMember).where(
            ChannelMember.channel_id == channel_id,
            ChannelMember.user_id == user_id,
        )
        res = await db.execute(member_stmt)
        member = res.scalars().first()
        if member:
            member.last_read_at = now

        await db.commit()

        # Broadcast read receipt to channel
        payload = {
            "event": "message:read_update",
            "data": {
                "message_ids": marked_ids,
                "channel_id": str(channel_id),
                "read_by": {
                    "user_id": str(user_id),
                    "read_at": now.isoformat(),
                },
            },
        }
        from app.services.connection_manager import connection_manager

        await connection_manager.broadcast_to_channel(channel_id, payload)
        await redis_pubsub_manager.publish_to_channel(channel_id, payload)

        return {
            "marked_count": len(marked_ids),
            "message_ids": marked_ids,
            "read_at": now.isoformat(),
        }

    @classmethod
    async def get_message_readers(
        cls, db: AsyncSession, message_id: uuid.UUID
    ) -> List[Dict[str, Any]]:
        # Verify message exists
        msg_stmt = select(Message).where(Message.id == message_id)
        msg_res = await db.execute(msg_stmt)
        if not msg_res.scalars().first():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Message not found",
            )

        stmt = (
            select(MessageRead)
            .options(selectinload(MessageRead.user))
            .where(MessageRead.message_id == message_id)
            .order_by(MessageRead.read_at.asc())
        )
        res = await db.execute(stmt)
        reads = res.scalars().all()

        readers = []
        for r in reads:
            readers.append(
                {
                    "user_id": str(r.user_id),
                    "username": r.user.username if r.user else None,
                    "avatar_url": r.user.avatar_url if r.user else None,
                    "read_at": r.read_at.isoformat(),
                }
            )
        return readers
