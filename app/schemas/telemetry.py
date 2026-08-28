from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime

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
