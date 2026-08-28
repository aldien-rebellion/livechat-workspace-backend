from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.models.telemetry import Telemetry
from app.schemas.telemetry import TelemetryCreate, TelemetryResponse

router = APIRouter()

@router.post("/", response_model=TelemetryResponse, status_code=status.HTTP_201_CREATED)
async def create_telemetry(
    telemetry_in: TelemetryCreate,
    db: AsyncSession = Depends(get_db)
):
    db_obj = Telemetry(**telemetry_in.model_dump())
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj
