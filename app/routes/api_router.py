from fastapi import APIRouter

from app.controllers import (
    auth_controller,
    channel_controller,
    chat_websocket_controller,
    devices_controller,
    file_controller,
    health_controller,
    message_controller,
    telemetry_controller,
    workspace_controller,
)

api_router = APIRouter()
api_router.include_router(health_controller.router, prefix="", tags=["Health"])
api_router.include_router(
    chat_websocket_controller.router, prefix="", tags=["WebSocket"]
)
api_router.include_router(auth_controller.router, prefix="/auth", tags=["Auth"])
api_router.include_router(
    workspaces_router := workspace_controller.router,
    prefix="/workspaces",
    tags=["Workspaces"],
)
api_router.include_router(
    channels_router := channel_controller.router,
    prefix="/channels",
    tags=["Channels"],
)
api_router.include_router(
    messages_router := message_controller.router,
    prefix="/messages",
    tags=["Messages"],
)
api_router.include_router(
    files_router := file_controller.router,
    prefix="/files",
    tags=["Files"],
)
api_router.include_router(
    telemetry_controller.router, prefix="/telemetry", tags=["Telemetry"]
)
api_router.include_router(
    devices_controller.router, prefix="/devices", tags=["Devices"]
)
