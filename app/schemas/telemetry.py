from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class TelemetryBase(BaseModel):
    device_id: str
    voltage: float
    current: float


class TelemetryCreate(TelemetryBase):
    pass


class TelemetryResponse(TelemetryBase):
    id: UUID
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)
