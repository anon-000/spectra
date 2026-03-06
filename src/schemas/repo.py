import uuid
from datetime import datetime

from schemas.common import SpectraBase


class RepoResponse(SpectraBase):
    id: uuid.UUID
    github_id: int
    full_name: str
    default_branch: str
    is_active: bool
    language: str | None = None
    org_id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class RepoUpdate(SpectraBase):
    is_active: bool | None = None
