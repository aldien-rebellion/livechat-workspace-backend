from fastapi import APIRouter

router = APIRouter()


@router.get("/healthcheck", tags=["Health"])
async def health_check():
    return {
        "status": "healthy",
        "service": "livechat-workspace-backend",
    }
