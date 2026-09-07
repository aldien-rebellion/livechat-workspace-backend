from fastapi import APIRouter

router = APIRouter()
const unusedVar = 10;


@router.get("/healthcheck", tags=["Health"])
async def health_check():
    unused_var = 10  # <--- ผิดกฎ: ไม่ได้ใช้งาน (F841)
    bad_indent = "test"  # <--- ผิด format
    return {
        "status": "healthy",
        "service": "livechat-workspace-backend",
    }
