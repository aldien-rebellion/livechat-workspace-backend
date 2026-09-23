import uuid
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.message import Message
from app.models.user import User
from app.routes.deps import get_current_active_user
from app.schemas.channel import MessageResponse, MessageUpdate
from app.services.channel_service import ChannelService
from app.services.read_receipt_service import ReadReceiptService

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


@router.post(
    "/{message_id}/read",
    status_code=status.HTTP_200_OK,
)
async def mark_message_read(
    message_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Message).where(Message.id == message_id)
    res = await db.execute(stmt)
    message = res.scalars().first()
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found",
        )

    return await ReadReceiptService.mark_messages_read(
        db=db,
        channel_id=message.channel_id,
        user_id=current_user.id,
        message_ids=[message_id],
    )


@router.get(
    "/{message_id}/readers",
    response_model=List[Dict[str, Any]],
    status_code=status.HTTP_200_OK,
)
async def get_message_readers(
    message_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    return await ReadReceiptService.get_message_readers(db=db, message_id=message_id)
