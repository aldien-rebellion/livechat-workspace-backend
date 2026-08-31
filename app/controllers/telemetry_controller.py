import redis.asyncio as aioredis
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.redis import get_device_status_key, get_redis
from app.db.session import get_db
from app.models.telemetry import Telemetry
from app.schemas.telemetry import TelemetryCreate, TelemetryResponse

router = APIRouter()


@router.post("/", response_model=TelemetryResponse, status_code=status.HTTP_201_CREATED)
async def create_telemetry(
    telemetry_in: TelemetryCreate,
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
):
    db_obj = Telemetry(**telemetry_in.model_dump())
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)

    # Update latest status in Redis cache
    telemetry_response = TelemetryResponse.model_validate(db_obj)
    cache_key = get_device_status_key(db_obj.device_id)
    await redis.set(cache_key, telemetry_response.model_dump_json())

    return db_obj
