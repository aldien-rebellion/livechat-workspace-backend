import uuid
from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.channel import Channel, ChannelMember
from app.models.message import Message
from app.models.workspace import WorkspaceMember


class ChannelService:
    @classmethod
    async def create_channel(
        cls,
        db: AsyncSession,
        workspace_id: uuid.UUID,
        name: str,
        topic: Optional[str],
        channel_type: str,
        creator_id: uuid.UUID,
    ) -> Channel:
        # Check workspace membership
        ws_stmt = select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == creator_id,
        )
        ws_res = await db.execute(ws_stmt)
        if not ws_res.scalars().first():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Must be a workspace member to create channels",
            )

        channel = Channel(
            workspace_id=workspace_id,
            name=name,
            topic=topic,
            channel_type=channel_type.upper(),
        )
        db.add(channel)
        await db.flush()

        # Add creator as member
        creator_member = ChannelMember(channel_id=channel.id, user_id=creator_id)
        db.add(creator_member)

        # If PUBLIC, add all workspace members to channel
        if channel.channel_type == "PUBLIC":
            all_ws_members_stmt = select(WorkspaceMember.user_id).where(
                WorkspaceMember.workspace_id == workspace_id,
                WorkspaceMember.user_id != creator_id,
            )
            res = await db.execute(all_ws_members_stmt)
            for other_uid in res.scalars().all():
                db.add(ChannelMember(channel_id=channel.id, user_id=other_uid))

        await db.commit()
        await db.refresh(channel)
        return channel

    @classmethod
    async def list_workspace_channels(
        cls, db: AsyncSession, workspace_id: uuid.UUID, user_id: uuid.UUID
    ) -> List[Channel]:
        # Return public channels OR private channels where user is member
        stmt = (
            select(Channel)
            .outerjoin(
                ChannelMember,
                and_(
                    Channel.id == ChannelMember.channel_id,
                    ChannelMember.user_id == user_id,
                ),
            )
            .where(
                Channel.workspace_id == workspace_id,
                (Channel.channel_type == "PUBLIC") | (ChannelMember.user_id == user_id),
            )
            .distinct()
            .order_by(Channel.created_at.asc())
        )
        res = await db.execute(stmt)
        return list(res.scalars().all())

    @classmethod
    async def get_or_create_dm(
        cls, db: AsyncSession, user1_id: uuid.UUID, user2_id: uuid.UUID
    ) -> Channel:
        if user1_id == user2_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot create a direct message with yourself",
            )

        # Search for existing 1-on-1 DM channel
        # A DM channel has channel_type == 'DIRECT_MESSAGE' and has exactly both members
        subq = (
            select(ChannelMember.channel_id)
            .join(Channel, Channel.id == ChannelMember.channel_id)
            .where(
                Channel.channel_type == "DIRECT_MESSAGE",
                ChannelMember.user_id.in_([user1_id, user2_id]),
            )
            .group_by(ChannelMember.channel_id)
            .having(func.count(ChannelMember.user_id) == 2)
        )
        res = await db.execute(subq)
        existing_channel_id = res.scalars().first()

        if existing_channel_id:
            stmt = select(Channel).where(Channel.id == existing_channel_id)
            res = await db.execute(stmt)
            return res.scalars().first()

        # Create new DM channel
        u1_part = min(str(user1_id), str(user2_id))[:8]
        u2_part = max(str(user1_id), str(user2_id))[:8]
        dm_channel = Channel(
            workspace_id=None,
            name=f"dm-{u1_part}-{u2_part}",
            topic="Direct Message",
            channel_type="DIRECT_MESSAGE",
        )
        db.add(dm_channel)
        await db.flush()

        db.add(ChannelMember(channel_id=dm_channel.id, user_id=user1_id))
        db.add(ChannelMember(channel_id=dm_channel.id, user_id=user2_id))

        await db.commit()
        await db.refresh(dm_channel)
        return dm_channel

    @classmethod
    async def get_channel(
        cls, db: AsyncSession, channel_id: uuid.UUID
    ) -> Optional[Channel]:
        stmt = select(Channel).where(Channel.id == channel_id)
        res = await db.execute(stmt)
        return res.scalars().first()

    @classmethod
    async def is_member(
        cls, db: AsyncSession, channel_id: uuid.UUID, user_id: uuid.UUID
    ) -> bool:
        stmt = select(ChannelMember).where(
            ChannelMember.channel_id == channel_id,
            ChannelMember.user_id == user_id,
        )
        res = await db.execute(stmt)
        return res.scalars().first() is not None

    @classmethod
    async def add_member(
        cls, db: AsyncSession, channel_id: uuid.UUID, user_id: uuid.UUID
    ) -> ChannelMember:
        channel = await cls.get_channel(db, channel_id)
        if not channel:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Channel not found",
            )
        stmt = (
            select(ChannelMember)
            .where(
                ChannelMember.channel_id == channel_id,
                ChannelMember.user_id == user_id,
            )
            .options(selectinload(ChannelMember.user))
        )
        res = await db.execute(stmt)
        existing = res.scalars().first()
        if existing:
            return existing

        member = ChannelMember(channel_id=channel_id, user_id=user_id)
        db.add(member)
        await db.commit()

        res = await db.execute(stmt)
        return res.scalars().first()

    @classmethod
    async def get_messages(
        cls,
        db: AsyncSession,
        channel_id: uuid.UUID,
        user_id: uuid.UUID,
        before_id: Optional[uuid.UUID] = None,
        limit: int = 50,
    ) -> List[Message]:
        if not await cls.is_member(db, channel_id, user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Must be a channel member to view messages",
            )

        query = (
            select(Message)
            .options(selectinload(Message.user))
            .where(Message.channel_id == channel_id)
        )

        if before_id:
            cursor_stmt = select(Message).where(Message.id == before_id)
            cursor_res = await db.execute(cursor_stmt)
            cursor_msg = cursor_res.scalars().first()
            if cursor_msg:
                query = query.where(Message.created_at < cursor_msg.created_at)

        query = query.order_by(Message.created_at.desc()).limit(limit)
        res = await db.execute(query)
        messages = list(res.scalars().all())
        # Return in ascending order for chat window rendering
        messages.reverse()
        return messages

    @classmethod
    async def create_message(
        cls,
        db: AsyncSession,
        channel_id: uuid.UUID,
        user_id: uuid.UUID,
        content: str,
        parent_id: Optional[uuid.UUID] = None,
        message_type: str = "text",
        file_url: Optional[str] = None,
    ) -> Message:
        if not await cls.is_member(db, channel_id, user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Must be a channel member to send messages",
            )

        message = Message(
            channel_id=channel_id,
            user_id=user_id,
            parent_id=parent_id,
            content=content,
            message_type=message_type,
            file_url=file_url,
        )
        db.add(message)
        await db.commit()
        await db.refresh(message)
        # Load user relationship
        msg_stmt = (
            select(Message)
            .options(selectinload(Message.user))
            .where(Message.id == message.id)
        )
        msg_res = await db.execute(msg_stmt)
        return msg_res.scalars().first()

    @classmethod
    async def update_message(
        cls,
        db: AsyncSession,
        message_id: uuid.UUID,
        user_id: uuid.UUID,
        content: str,
    ) -> Message:
        stmt = (
            select(Message)
            .options(selectinload(Message.user))
            .where(Message.id == message_id)
        )
        res = await db.execute(stmt)
        message = res.scalars().first()
        if not message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Message not found",
            )
        if message.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot edit messages authored by another user",
            )
        if message.is_deleted:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot edit a deleted message",
            )

        message.content = content
        message.is_edited = True
        await db.commit()
        await db.refresh(message)
        return message

    @classmethod
    async def delete_message(
        cls,
        db: AsyncSession,
        message_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> Message:
        stmt = (
            select(Message)
            .options(selectinload(Message.user))
            .where(Message.id == message_id)
        )
        res = await db.execute(stmt)
        message = res.scalars().first()
        if not message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Message not found",
            )
        if message.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot delete messages authored by another user",
            )

        message.is_deleted = True
        message.content = "This message was deleted."
        await db.commit()
        await db.refresh(message)
        return message
