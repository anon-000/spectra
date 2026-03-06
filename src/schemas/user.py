import uuid
from datetime import datetime

from schemas.common import SpectraBase


class UserResponse(SpectraBase):
    id: uuid.UUID
    github_id: int
    github_login: str
    email: str | None = None
    avatar_url: str | None = None
    org_id: uuid.UUID | None = None
    created_at: datetime
    updated_at: datetime


class TokenResponse(SpectraBase):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
