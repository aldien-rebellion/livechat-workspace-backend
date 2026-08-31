import redis.asyncio as aioredis

from src.config.settings import settings

# Global async Redis client
redis_client: aioredis.Redis = aioredis.from_url(
    settings.REDIS_URL,
    decode_responses=True,
)


async def get_redis() -> aioredis.Redis:
    """FastAPI dependency for obtaining a Redis client instance."""
    return redis_client


def get_device_status_key(device_id: str) -> str:
    """Format standard Redis cache key for device latest status."""
    return f"device:{device_id}:latest_status"
