from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse

from app.models.user import User
from app.routes.deps import get_current_active_user
from app.schemas.file import FileUploadResponse
from app.services.storage import StorageService, get_storage_service

router = APIRouter()


@router.post(
    "/upload",
    response_model=FileUploadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    storage: StorageService = Depends(get_storage_service),
):
    content = await file.read()
    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty",
        )

    res = await storage.upload_file(
        file_content=content,
        filename=file.filename or "uploaded_file",
        content_type=file.content_type or "application/octet-stream",
    )
    return res


@router.get("/{file_id}")
async def get_file(
    file_id: str,
    storage: StorageService = Depends(get_storage_service),
):
    path = await storage.get_file_path(file_id)
    if not path or not path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found",
        )
    return FileResponse(path)
