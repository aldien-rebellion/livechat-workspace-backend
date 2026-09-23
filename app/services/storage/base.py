from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, Optional


class StorageService(ABC):
    @abstractmethod
    async def upload_file(
        self, file_content: bytes, filename: str, content_type: str
    ) -> Dict[str, Any]:
        """Upload file content and return file metadata dictionary."""
        pass

    @abstractmethod
    async def get_file_path(self, file_id: str) -> Optional[Path]:
        """Retrieve local file Path if available."""
        pass

    @abstractmethod
    async def delete_file(self, file_id: str) -> bool:
        """Delete file by file_id."""
        pass
