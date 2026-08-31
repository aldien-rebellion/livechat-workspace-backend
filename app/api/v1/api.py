from fastapi import APIRouter

from app.api.v1.endpoints import devices, health, telemetry

api_router = APIRouter()
api_router.include_router(health.router, prefix="", tags=["Health"])
api_router.include_router(telemetry.router, prefix="/telemetry", tags=["Telemetry"])
api_router.include_router(devices.router, prefix="/devices", tags=["Devices"])
