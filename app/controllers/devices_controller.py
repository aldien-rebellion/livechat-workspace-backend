import json

import redis.asyncio as aioredis
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.redis import get_device_status_key, get_redis
from app.db.session import get_db
from app.models.telemetry import Telemetry
from app.models.user import User
from app.routes.deps import get_current_admin, get_current_user
from app.schemas.device import DeviceStatusResponse

router = APIRouter()


class CommandRequest(BaseModel):
    command: str


@router.get(
    "/{device_id}/status",
    response_model=DeviceStatusResponse,
    status_code=status.HTTP_200_OK,
)
async def get_device_status(
    device_id: str,
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve the latest status of a device using the Cache-Aside Pattern.
    Protected by Auth Middleware (requires any logged-in user).
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


@router.post(
    "/{device_id}/commands",
    status_code=status.HTTP_200_OK,
)
async def send_device_command(
    device_id: str,
    payload: CommandRequest,
    current_admin: User = Depends(get_current_admin),
):
    """
    Send command (e.g., Remote Reset) to Pi Pico.
    Protected by Auth & Role Middleware (requires admin privileges).
    """
    # Simulate sending command to Pi Pico
    if payload.command != "reset":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported command"
        )
    return {
        "message": f"Command '{payload.command}' sent successfully to device {device_id}"
    }
