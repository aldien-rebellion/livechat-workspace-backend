import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.user import User
from app.routes.deps import get_current_active_user
from app.schemas.channel import (
    ChannelMemberAdd,
    ChannelMemberResponse,
    ChannelResponse,
    DirectMessageCreate,
    MessageCreate,
    MessageResponse,
)
from app.services.channel_service import ChannelService

router = APIRouter()


@router.post(
    "/direct",
    response_model=ChannelResponse,
    status_code=status.HTTP_200_OK,
)
async def get_or_create_direct_message(
    dm_in: DirectMessageCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    return await ChannelService.get_or_create_dm(
        db=db,
        user1_id=current_user.id,
        user2_id=dm_in.target_user_id,
    )


@router.post(
    "/{channel_id}/members",
    response_model=ChannelMemberResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_channel_member(
    channel_id: uuid.UUID,
    member_in: ChannelMemberAdd,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    return await ChannelService.add_member(
        db=db,
        channel_id=channel_id,
        user_id=member_in.user_id,
    )


@router.get(
    "/{channel_id}/messages",
    response_model=List[MessageResponse],
)
async def list_channel_messages(
    channel_id: uuid.UUID,
    before_id: Optional[uuid.UUID] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    return await ChannelService.get_messages(
        db=db,
        channel_id=channel_id,
        user_id=current_user.id,
        before_id=before_id,
        limit=limit,
    )


@router.post(
    "/{channel_id}/messages",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
)
async def send_message_rest(
    channel_id: uuid.UUID,
    msg_in: MessageCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    return await ChannelService.create_message(
        db=db,
        channel_id=channel_id,
        user_id=current_user.id,
        content=msg_in.content,
        parent_id=msg_in.parent_id,
        message_type=msg_in.message_type,
        file_url=msg_in.file_url,
    )
