import json

import redis.asyncio as aioredis
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.redis import get_device_status_key, get_redis
from app.db.session import get_db
from app.models.telemetry import Telemetry
from app.schemas.device import DeviceStatusResponse

router = APIRouter()


@router.get(
    "/{device_id}/status",
    response_model=DeviceStatusResponse,
    status_code=status.HTTP_200_OK,
)
async def get_device_status(
    device_id: str,
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
):
    """
    Retrieve the latest status of a device using the Cache-Aside Pattern.
    - Checks Redis first (Cache Hit).
    - If not found (Cache Miss), queries the latest record from PostgreSQL,
      caches it into Redis, and returns the result.
    """
    cache_key = get_device_status_key(device_id)

    # 1. Try to fetch from Redis (Cache Hit)
    cached_data = await redis.get(cache_key)
    if cached_data:
        return json.loads(cached_data)

    # 2. Fetch latest telemetry from PostgreSQL (Cache Miss)
    stmt = (
        select(Telemetry)
        .where(Telemetry.device_id == device_id)
        .order_by(Telemetry.timestamp.desc())
        .limit(1)
    )
    result = await db.execute(stmt)
    latest_telemetry = result.scalars().first()

    if not latest_telemetry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device status not found for device_id: {device_id}",
        )

    # 3. Store in Redis for future requests (Cache-Aside)
    response_data = DeviceStatusResponse.model_validate(latest_telemetry)
    await redis.set(cache_key, response_data.model_dump_json())

    return response_data
