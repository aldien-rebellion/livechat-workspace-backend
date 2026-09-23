import re
import uuid
from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.channel import Channel, ChannelMember
from app.models.workspace import Workspace, WorkspaceMember


class WorkspaceService:
    @staticmethod
    def slugify(text: str) -> str:
        text = text.lower().strip()
        text = re.sub(r"[^\w\s-]", "", text)
        text = re.sub(r"[\s_-]+", "-", text)
        return text

    @classmethod
    async def create_workspace(
        cls,
        db: AsyncSession,
        name: str,
        owner_id: uuid.UUID,
        slug: Optional[str] = None,
    ) -> Workspace:
        slug = cls.slugify(slug or name)
        if not slug:
            slug = f"workspace-{uuid.uuid4().hex[:6]}"

        stmt = select(Workspace).where(Workspace.slug == slug)
        res = await db.execute(stmt)
        if res.scalars().first():
            slug = f"{slug}-{uuid.uuid4().hex[:4]}"

        workspace = Workspace(name=name, slug=slug, owner_id=owner_id)
        db.add(workspace)
        await db.flush()

        # Add owner as workspace member
        owner_member = WorkspaceMember(
            workspace_id=workspace.id, user_id=owner_id, role="owner"
        )
        db.add(owner_member)

        # Create default #general channel
        general_channel = Channel(
            workspace_id=workspace.id,
            name="general",
            topic="General discussions",
            channel_type="PUBLIC",
        )
        db.add(general_channel)
        await db.flush()

        general_member = ChannelMember(channel_id=general_channel.id, user_id=owner_id)
        db.add(general_member)

        await db.commit()
        await db.refresh(workspace)
        return workspace

    @classmethod
    async def list_user_workspaces(
        cls, db: AsyncSession, user_id: uuid.UUID
    ) -> List[Workspace]:
        stmt = (
            select(Workspace)
            .join(WorkspaceMember, Workspace.id == WorkspaceMember.workspace_id)
            .where(WorkspaceMember.user_id == user_id)
            .order_by(Workspace.created_at.desc())
        )
        res = await db.execute(stmt)
        return list(res.scalars().all())

    @classmethod
    async def get_workspace(
        cls, db: AsyncSession, workspace_id: uuid.UUID
    ) -> Optional[Workspace]:
        stmt = select(Workspace).where(Workspace.id == workspace_id)
        res = await db.execute(stmt)
        return res.scalars().first()

    @classmethod
    async def is_member(
        cls, db: AsyncSession, workspace_id: uuid.UUID, user_id: uuid.UUID
    ) -> bool:
        stmt = select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == user_id,
        )
        res = await db.execute(stmt)
        return res.scalars().first() is not None

    @classmethod
    async def add_member(
        cls,
        db: AsyncSession,
        workspace_id: uuid.UUID,
        user_id: uuid.UUID,
        role: str = "member",
    ) -> WorkspaceMember:
        workspace = await cls.get_workspace(db, workspace_id)
        if not workspace:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workspace not found",
            )

        stmt = (
            select(WorkspaceMember)
            .where(
                WorkspaceMember.workspace_id == workspace_id,
                WorkspaceMember.user_id == user_id,
            )
            .options(selectinload(WorkspaceMember.user))
        )
        res = await db.execute(stmt)
        existing = res.scalars().first()
        if existing:
            return existing

        member = WorkspaceMember(workspace_id=workspace_id, user_id=user_id, role=role)
        db.add(member)

        # Auto-join public channels
        public_stmt = select(Channel).where(
            Channel.workspace_id == workspace_id,
            Channel.channel_type == "PUBLIC",
        )
        pub_res = await db.execute(public_stmt)
        for channel in pub_res.scalars().all():
            db.add(ChannelMember(channel_id=channel.id, user_id=user_id))

        await db.commit()

        # Reload with user relationship eager loaded
        res = await db.execute(stmt)
        return res.scalars().first()
