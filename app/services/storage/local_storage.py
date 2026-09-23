import os
import uuid
from pathlib import Path
from typing import Any, Dict, Optional

from app.config.settings import settings
from app.services.storage.base import StorageService


class LocalStorageService(StorageService):
    def __init__(self, upload_dir: Optional[str] = None):
        self.upload_dir = Path(upload_dir or settings.UPLOAD_DIR)
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    async def upload_file(
        self, file_content: bytes, filename: str, content_type: str
    ) -> Dict[str, Any]:
        ext = Path(filename).suffix
        file_id = f"{uuid.uuid4().hex}{ext}"
        destination = self.upload_dir / file_id

        destination.write_bytes(file_content)
        size = len(file_content)
        url = f"{settings.API_V1_STR}/files/{file_id}"

        return {
            "file_id": file_id,
            "filename": filename,
            "content_type": content_type,
            "size": size,
            "url": url,
        }

    async def get_file_path(self, file_id: str) -> Optional[Path]:
        safe_path = (self.upload_dir / file_id).resolve()
        # Prevent path traversal
        if not str(safe_path).startswith(str(self.upload_dir.resolve())):
            return None
        if safe_path.exists() and safe_path.is_file():
            return safe_path
        return None

    async def delete_file(self, file_id: str) -> bool:
        path = await self.get_file_path(file_id)
        if path and path.exists():
            os.remove(path)
            return True
        return False


_storage_instance: Optional[StorageService] = None


def get_storage_service() -> StorageService:
    global _storage_instance
    if _storage_instance is None:
        _storage_instance = LocalStorageService()
    return _storage_instance
