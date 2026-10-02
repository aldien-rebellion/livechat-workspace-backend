from pydantic import BaseModel


class FileUploadResponse(BaseModel):
    file_id: str
    filename: str
    content_type: str
    size: int
    url: str
