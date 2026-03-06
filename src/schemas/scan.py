import uuid
from datetime import datetime

from pydantic import BaseModel

from schemas.common import SpectraBase


class ScanResponse(SpectraBase):
    id: uuid.UUID
    repo_id: uuid.UUID
    pr_number: int | None = None
    commit_sha: str
    branch: str | None = None
    trigger: str
    status: str
    error_message: str | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None
    findings_count: int
    critical_count: int
    high_count: int
    created_at: datetime
    updated_at: datetime


class ManualScanRequest(BaseModel):
    repo_id: uuid.UUID
    commit_sha: str
    branch: str = "main"
