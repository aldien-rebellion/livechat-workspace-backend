import asyncio
import json
import logging
import uuid
from typing import Optional

import redis.asyncio as aioredis

from app.config.redis import redis_client
from app.services.connection_manager import ConnectionManager, connection_manager

logger = logging.getLogger(__name__)


class RedisPubSubManager:
    def __init__(self, client: Optional[aioredis.Redis] = None):
        self.redis: aioredis.Redis = client or redis_client
        self._listener_task: Optional[asyncio.Task] = None
        self._pubsub: Optional[aioredis.client.PubSub] = None
        self._running: bool = False

    async def publish_to_channel(self, channel_id: uuid.UUID, event_dict: dict) -> None:
        channel_key = f"pubsub:channel:{channel_id}"
        payload_str = json.dumps(event_dict)
        await self.redis.publish(channel_key, payload_str)

    async def start_listener(
        self, conn_mgr: Optional[ConnectionManager] = None
    ) -> None:
        if self._running:
            return
        self._running = True
        self._pubsub = self.redis.pubsub()
        await self._pubsub.psubscribe("pubsub:channel:*")
        mgr = conn_mgr or connection_manager
        self._listener_task = asyncio.create_task(self._listen_loop(mgr))
        logger.info("Redis Pub/Sub listener started on pattern 'pubsub:channel:*'")

    async def _listen_loop(self, conn_mgr: ConnectionManager) -> None:
        try:
            while self._running and self._pubsub:
                message = await self._pubsub.get_message(
                    ignore_subscribe_messages=True, timeout=1.0
                )
                if message and message.get("type") == "pmessage":
                    try:
                        channel_pattern_name = message["channel"]
                        channel_id_str = channel_pattern_name.split(":")[-1]
                        channel_uuid = uuid.UUID(channel_id_str)
                        data = json.loads(message["data"])
                        await conn_mgr.broadcast_to_channel(channel_uuid, data)
                    except Exception as ex:
                        logger.error(f"Error handling Redis Pub/Sub message: {ex}")
                await asyncio.sleep(0.01)
        except asyncio.CancelledError:
            logger.info("Redis Pub/Sub listener loop cancelled")
        except Exception as e:
            logger.error(f"Redis Pub/Sub listener loop encountered error: {e}")
        finally:
            self._running = False

    async def stop_listener(self) -> None:
        self._running = False
        if self._listener_task and not self._listener_task.done():
            self._listener_task.cancel()
            try:
                await self._listener_task
            except asyncio.CancelledError:
                pass
        if self._pubsub:
            await self._pubsub.punsubscribe("pubsub:channel:*")
            if hasattr(self._pubsub, "aclose"):
                await self._pubsub.aclose()
            else:
                await self._pubsub.close()
            self._pubsub = None
        logger.info("Redis Pub/Sub listener stopped")


redis_pubsub_manager = RedisPubSubManager()
