from fastapi import APIRouter

from app.controllers import devices_controller, health_controller, telemetry_controller

api_router = APIRouter()
api_router.include_router(health_controller.router, prefix="", tags=["Health"])
api_router.include_router(
    telemetry_controller.router, prefix="/telemetry", tags=["Telemetry"]
)
api_router.include_router(
    devices_controller.router, prefix="/devices", tags=["Devices"]
)
