import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

from app.schemas.user import UserResponse


class WorkspaceCreate(BaseModel):
    name: str
    slug: Optional[str] = None


class WorkspaceMemberAdd(BaseModel):
    user_id: uuid.UUID
    role: str = "member"


class WorkspaceMemberResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    workspace_id: uuid.UUID
    user_id: uuid.UUID
    role: str
    joined_at: datetime
    user: Optional[UserResponse] = None


class WorkspaceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    slug: str
    owner_id: uuid.UUID
    created_at: datetime
