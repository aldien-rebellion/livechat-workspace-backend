import logging
import uuid
from typing import Dict, Set

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self):
        # channel_id -> { user_id -> set of WebSockets }
        self._channels: Dict[uuid.UUID, Dict[uuid.UUID, Set[WebSocket]]] = {}

    async def connect(
        self, websocket: WebSocket, channel_id: uuid.UUID, user_id: uuid.UUID
    ) -> None:
        await websocket.accept()
        if channel_id not in self._channels:
            self._channels[channel_id] = {}
        if user_id not in self._channels[channel_id]:
            self._channels[channel_id][user_id] = set()
        active_count = len(self._channels[channel_id])
        logger.info(
            f"User {user_id} connected to channel {channel_id} "
            f"(total active in chan: {active_count})"
        )

    async def disconnect(
        self, websocket: WebSocket, channel_id: uuid.UUID, user_id: uuid.UUID
    ) -> None:
        if channel_id in self._channels and user_id in self._channels[channel_id]:
            self._channels[channel_id][user_id].discard(websocket)
            if not self._channels[channel_id][user_id]:
                del self._channels[channel_id][user_id]
            if not self._channels[channel_id]:
                del self._channels[channel_id]
        logger.info(f"User {user_id} disconnected from channel {channel_id}")

    async def broadcast_to_channel(self, channel_id: uuid.UUID, message: dict) -> None:
        if channel_id not in self._channels:
            return

        dead_sockets = []
        user_channels = list(self._channels[channel_id].items())
        for user_id, sockets in user_channels:
            for ws in list(sockets):
                try:
                    await ws.send_json(message)
                except Exception as e:
                    logger.warning(
                        f"Failed to send to user {user_id} on {channel_id}: {e}"
                    )
                    dead_sockets.append((ws, user_id))

        for ws, user_id in dead_sockets:
            await self.disconnect(ws, channel_id, user_id)

    def get_total_connections(self) -> int:
        total = 0
        for user_map in self._channels.values():
            for sockets in user_map.values():
                total += len(sockets)
        return total

    def get_active_users_in_channel(self, channel_id: uuid.UUID) -> Set[uuid.UUID]:
        if channel_id in self._channels:
            return set(self._channels[channel_id].keys())
        return set()


connection_manager = ConnectionManager()
