import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.user import User
from app.routes.deps import get_current_active_user
from app.schemas.channel import MessageResponse, MessageUpdate
from app.services.channel_service import ChannelService

router = APIRouter()


@router.put(
    "/{message_id}",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
)
async def update_message(
    message_id: uuid.UUID,
    msg_in: MessageUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    return await ChannelService.update_message(
        db=db,
        message_id=message_id,
        user_id=current_user.id,
        content=msg_in.content,
    )


@router.delete(
    "/{message_id}",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
)
async def delete_message(
    message_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    return await ChannelService.delete_message(
        db=db,
        message_id=message_id,
        user_id=current_user.id,
    )
