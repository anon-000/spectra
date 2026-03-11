import uuid
from datetime import datetime

from pydantic import BaseModel

from schemas.common import SpectraBase


class FindingResponse(SpectraBase):
    id: uuid.UUID
    scan_id: uuid.UUID
    repo_id: uuid.UUID
    tool: str
    rule_id: str
    file_path: str
    line_start: int | None = None
    line_end: int | None = None
    snippet: str | None = None
    severity: str
    category: str
    title: str
    description: str | None = None
    fingerprint: str
    ai_severity: str | None = None
    ai_explanation: str | None = None
    ai_suggested_fix: str | None = None
    confidence: float | None = None
    ai_verdict: str | None = None
    status: str
    first_seen: datetime
    last_seen: datetime
    pr_number: int | None = None
    commit_sha: str | None = None
    package_name: str | None = None
    package_version: str | None = None
    cve_id: str | None = None
    cwe_id: str | None = None
    auto_fix_status: str | None = None
    auto_fix_pr_url: str | None = None
    auto_fix_pr_number: int | None = None
    auto_fix_error: str | None = None
    created_at: datetime
    updated_at: datetime


class FindingUpdate(BaseModel):
    status: str  # open, resolved, suppressed, false_positive


class BulkFindingUpdate(BaseModel):
    finding_ids: list[uuid.UUID]
    status: str


class FindingEventResponse(SpectraBase):
    id: uuid.UUID
    finding_id: uuid.UUID
    actor_id: uuid.UUID | None = None
    action: str
    old_value: str | None = None
    new_value: str | None = None
    comment: str | None = None
    created_at: datetime
