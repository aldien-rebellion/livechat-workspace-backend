import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

from app.schemas.user import UserResponse


class ChannelCreate(BaseModel):
    name: str
    topic: Optional[str] = None
    channel_type: str = "PUBLIC"


class DirectMessageCreate(BaseModel):
    target_user_id: uuid.UUID


class ChannelMemberAdd(BaseModel):
    user_id: uuid.UUID


class ChannelMemberResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    channel_id: uuid.UUID
    user_id: uuid.UUID
    joined_at: datetime
    last_read_at: Optional[datetime] = None
    user: Optional[UserResponse] = None


class ChannelResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    workspace_id: Optional[uuid.UUID] = None
    name: Optional[str] = None
    topic: Optional[str] = None
    channel_type: str
    created_at: datetime


class MessageCreate(BaseModel):
    content: str
    parent_id: Optional[uuid.UUID] = None
    message_type: str = "text"
    file_url: Optional[str] = None


class MessageUpdate(BaseModel):
    content: str


class MessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    channel_id: uuid.UUID
    user_id: uuid.UUID
    parent_id: Optional[uuid.UUID] = None
    content: str
    message_type: str
    file_url: Optional[str] = None
    is_edited: bool
    is_deleted: bool
    created_at: datetime
    updated_at: datetime
    user: Optional[UserResponse] = None
