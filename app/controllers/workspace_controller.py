import uuid
from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.user import User
from app.routes.deps import get_current_active_user
from app.schemas.channel import ChannelCreate, ChannelResponse
from app.schemas.workspace import (
    WorkspaceCreate,
    WorkspaceMemberAdd,
    WorkspaceMemberResponse,
    WorkspaceResponse,
)
from app.services.channel_service import ChannelService
from app.services.workspace_service import WorkspaceService

router = APIRouter()


@router.post(
    "",
    response_model=WorkspaceResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_workspace(
    ws_in: WorkspaceCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    return await WorkspaceService.create_workspace(
        db=db,
        name=ws_in.name,
        slug=ws_in.slug,
        owner_id=current_user.id,
    )


@router.get("", response_model=List[WorkspaceResponse])
async def list_workspaces(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    return await WorkspaceService.list_user_workspaces(db=db, user_id=current_user.id)


@router.post(
    "/{workspace_id}/channels",
    response_model=ChannelResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_workspace_channel(
    workspace_id: uuid.UUID,
    channel_in: ChannelCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    return await ChannelService.create_channel(
        db=db,
        workspace_id=workspace_id,
        name=channel_in.name,
        topic=channel_in.topic,
        channel_type=channel_in.channel_type,
        creator_id=current_user.id,
    )


@router.get(
    "/{workspace_id}/channels",
    response_model=List[ChannelResponse],
)
async def list_workspace_channels(
    workspace_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    return await ChannelService.list_workspace_channels(
        db=db, workspace_id=workspace_id, user_id=current_user.id
    )


@router.post(
    "/{workspace_id}/members",
    response_model=WorkspaceMemberResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_workspace_member(
    workspace_id: uuid.UUID,
    member_in: WorkspaceMemberAdd,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    return await WorkspaceService.add_member(
        db=db,
        workspace_id=workspace_id,
        user_id=member_in.user_id,
        role=member_in.role,
    )
