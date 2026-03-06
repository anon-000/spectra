import uuid
from datetime import datetime

from pydantic import BaseModel

from schemas.common import SpectraBase


class PolicyRules(BaseModel):
    fail_on: list[str] = []  # e.g. ["critical", "high"]
    max_critical: int | None = None
    max_high: int | None = None
    block_licenses: list[str] = []


class PolicyCreate(SpectraBase):
    name: str
    rules: PolicyRules


class PolicyUpdate(SpectraBase):
    name: str | None = None
    is_active: bool | None = None
    rules: PolicyRules | None = None


class PolicyResponse(SpectraBase):
    id: uuid.UUID
    org_id: uuid.UUID
    name: str
    is_active: bool
    rules: dict
    created_at: datetime
    updated_at: datetime


class PolicyEvalResult(BaseModel):
    passed: bool
    violations: list[str]
