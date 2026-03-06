import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class SpectraBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class IdTimestampMixin(BaseModel):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class PaginatedResponse(BaseModel):
    items: list
    total: int
    page: int
    page_size: int


class MessageResponse(BaseModel):
    message: str
