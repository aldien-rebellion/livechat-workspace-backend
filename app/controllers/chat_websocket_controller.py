import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect, status
from jose import JWTError
from sqlalchemy import select

from app.config.metrics import chat_messages_published_total
from app.db.session import AsyncSessionLocal
from app.models.channel import Channel
from app.models.user import User
from app.services.channel_service import ChannelService
from app.services.connection_manager import connection_manager
from app.services.presence_service import presence_service
from app.services.read_receipt_service import ReadReceiptService
from app.services.redis_pubsub import redis_pubsub_manager
from app.services.security import decode_token

logger = logging.getLogger(__name__)
router = APIRouter()


async def authenticate_ws_user(
    websocket: WebSocket, token_query: Optional[str] = None
) -> Optional[User]:
    token = token_query
    if not token:
        auth_header = websocket.headers.get("authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]

    if not token:
        return None

    try:
        payload = decode_token(token)
        user_id = payload.get("sub")
        token_type = payload.get("type", "access")
        if not user_id or token_type != "access":
            return None
        user_uuid = uuid.UUID(user_id)
    except (JWTError, ValueError):
        return None

    async with AsyncSessionLocal() as db:
        stmt = select(User).where(User.id == user_uuid)
        res = await db.execute(stmt)
        user = res.scalars().first()
        if user and user.is_active:
            return user
    return None


@router.websocket("/ws/channels/{channel_id}")
async def websocket_channel_endpoint(
    websocket: WebSocket,
    channel_id: uuid.UUID,
    token: Optional[str] = Query(None),
):
    user = await authenticate_ws_user(websocket, token_query=token)
    if not user:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    # Check channel and membership
    workspace_id = None
    async with AsyncSessionLocal() as db:
        channel_stmt = select(Channel).where(Channel.id == channel_id)
        c_res = await db.execute(channel_stmt)
        channel = c_res.scalars().first()
        if not channel:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
        workspace_id = channel.workspace_id

        is_member = await ChannelService.is_member(db, channel_id, user.id)
        if not is_member:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

    await connection_manager.connect(websocket, channel_id, user.id)

    # Update online presence
    was_offline = await presence_service.mark_online(user.id, workspace_id)
    if was_offline:
        presence_payload = {
            "event": "presence:update",
            "data": {
                "user_id": str(user.id),
                "status": "online",
                "last_seen": datetime.now(timezone.utc).isoformat(),
            },
        }
        await redis_pubsub_manager.publish_to_channel(channel_id, presence_payload)

    try:
        while True:
            data = await websocket.receive_json()
            event = data.get("event")
            event_data = data.get("data", {})

            if event == "message:send":
                content = event_data.get("content")
                if not content:
                    await websocket.send_json(
                        {
                            "event": "error",
                            "data": {"message": "Content cannot be empty"},
                        }
                    )
                    continue

                parent_id_raw = event_data.get("parent_id")
                parent_id = uuid.UUID(parent_id_raw) if parent_id_raw else None
                message_type = event_data.get("message_type", "text")
                file_url = event_data.get("file_url")

                # 1. Persist to PostgreSQL first
                async with AsyncSessionLocal() as db:
                    msg = await ChannelService.create_message(
                        db=db,
                        channel_id=channel_id,
                        user_id=user.id,
                        content=content,
                        parent_id=parent_id,
                        message_type=message_type,
                        file_url=file_url,
                    )
                chat_messages_published_total.labels(message_type=message_type).inc()

                # 2. Publish to Redis Pub/Sub for cross-instance broadcast
                broadcast_payload = {
                    "event": "message:broadcast",
                    "data": {
                        "id": str(msg.id),
                        "channel_id": str(channel_id),
                        "user": {
                            "id": str(user.id),
                            "username": user.username,
                            "avatar_url": user.avatar_url,
                        },
                        "content": msg.content,
                        "parent_id": (str(msg.parent_id) if msg.parent_id else None),
                        "message_type": msg.message_type,
                        "file_url": msg.file_url,
                        "created_at": msg.created_at.isoformat(),
                    },
                }
                # 2. Send ACK to sender first
                await websocket.send_json(
                    {
                        "event": "message:ack",
                        "data": {"id": str(msg.id), "status": "sent"},
                    }
                )

                # 3. Local broadcast + Redis Pub/Sub broadcast
                await connection_manager.broadcast_to_channel(
                    channel_id, broadcast_payload
                )
                await redis_pubsub_manager.publish_to_channel(
                    channel_id, broadcast_payload
                )

            elif event == "message:read":
                raw_ids = event_data.get("message_ids", [])
                message_ids = [uuid.UUID(m) for m in raw_ids if m]
                if message_ids:
                    async with AsyncSessionLocal() as db:
                        await ReadReceiptService.mark_messages_read(
                            db=db,
                            channel_id=channel_id,
                            user_id=user.id,
                            message_ids=message_ids,
                        )

            elif event == "typing:start":
                typing_payload = {
                    "event": "typing:start",
                    "data": {
                        "channel_id": str(channel_id),
                        "user_id": str(user.id),
                        "username": user.username,
                    },
                }
                await connection_manager.broadcast_to_channel(
                    channel_id, typing_payload
                )
                await redis_pubsub_manager.publish_to_channel(
                    channel_id, typing_payload
                )

            elif event == "presence:ping":
                await presence_service.heartbeat(user.id, workspace_id)
                await websocket.send_json({"event": "presence:pong"})

    except WebSocketDisconnect:
        await connection_manager.disconnect(websocket, channel_id, user.id)
        # Check if still active in any channel
        if not await presence_service.is_user_online(user.id):
            await presence_service.mark_offline(user.id, workspace_id)
            presence_payload = {
                "event": "presence:update",
                "data": {
                    "user_id": str(user.id),
                    "status": "offline",
                    "last_seen": datetime.now(timezone.utc).isoformat(),
                },
            }
            await redis_pubsub_manager.publish_to_channel(channel_id, presence_payload)
    except Exception as e:
        logger.error(f"WebSocket error for user {user.id} on {channel_id}: {e}")
        await connection_manager.disconnect(websocket, channel_id, user.id)
