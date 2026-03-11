import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from arq import create_pool
from arq.connections import RedisSettings

from config import get_settings
from core.exceptions import ForbiddenError, NotFoundError
from db.models.finding import Finding
from db.models.finding_event import FindingEvent
from db.models.repo import Repo
from db.models.user import User
from dependencies import get_current_user, get_db
from schemas.finding import (
    BulkFindingUpdate,
    FindingEventResponse,
    FindingResponse,
    FindingUpdate,
)

router = APIRouter(prefix="/findings", tags=["findings"])

VALID_STATUSES = {"open", "resolved", "suppressed", "false_positive"}


@router.get("", response_model=list[FindingResponse])
async def list_findings(
    repo_id: uuid.UUID | None = Query(None),
    scan_id: uuid.UUID | None = Query(None),
    severity: str | None = Query(None),
    category: str | None = Query(None),
    status: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not user.org_id:
        return []

    stmt = (
        select(Finding)
        .join(Repo, Finding.repo_id == Repo.id)
        .where(Repo.org_id == user.org_id)
    )
    if repo_id:
        stmt = stmt.where(Finding.repo_id == repo_id)
    if scan_id:
        stmt = stmt.where(Finding.scan_id == scan_id)
    if severity:
        stmt = stmt.where(Finding.severity == severity)
    if category:
        stmt = stmt.where(Finding.category == category)
    if status:
        stmt = stmt.where(Finding.status == status)

    stmt = stmt.order_by(Finding.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    return (await db.execute(stmt)).scalars().all()


@router.get("/{finding_id}", response_model=FindingResponse)
async def get_finding(
    finding_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    finding = (await db.execute(select(Finding).where(Finding.id == finding_id))).scalar_one_or_none()
    if not finding:
        raise NotFoundError("Finding", str(finding_id))

    repo = (await db.execute(select(Repo).where(Repo.id == finding.repo_id))).scalar_one()
    if repo.org_id != user.org_id:
        raise ForbiddenError()
    return finding


@router.patch("/{finding_id}", response_model=FindingResponse)
async def update_finding(
    finding_id: uuid.UUID,
    body: FindingUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if body.status not in VALID_STATUSES:
        from core.exceptions import ValidationError
        raise ValidationError(f"Invalid status. Must be one of: {VALID_STATUSES}")

    finding = (await db.execute(select(Finding).where(Finding.id == finding_id))).scalar_one_or_none()
    if not finding:
        raise NotFoundError("Finding", str(finding_id))

    repo = (await db.execute(select(Repo).where(Repo.id == finding.repo_id))).scalar_one()
    if repo.org_id != user.org_id:
        raise ForbiddenError()

    old_status = finding.status
    finding.status = body.status

    event = FindingEvent(
        finding_id=finding.id,
        actor_id=user.id,
        action="status_change",
        old_value=old_status,
        new_value=body.status,
    )
    db.add(event)
    await db.commit()
    await db.refresh(finding)
    return finding


@router.post("/bulk-update", response_model=list[FindingResponse])
async def bulk_update_findings(
    body: BulkFindingUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if body.status not in VALID_STATUSES:
        from core.exceptions import ValidationError
        raise ValidationError(f"Invalid status. Must be one of: {VALID_STATUSES}")

    stmt = select(Finding).where(Finding.id.in_(body.finding_ids))
    findings = (await db.execute(stmt)).scalars().all()

    updated = []
    for finding in findings:
        repo = (await db.execute(select(Repo).where(Repo.id == finding.repo_id))).scalar_one()
        if repo.org_id != user.org_id:
            continue

        old_status = finding.status
        finding.status = body.status
        db.add(FindingEvent(
            finding_id=finding.id,
            actor_id=user.id,
            action="status_change",
            old_value=old_status,
            new_value=body.status,
        ))
        updated.append(finding)

    await db.commit()
    for f in updated:
        await db.refresh(f)
    return updated


@router.post("/{finding_id}/auto-fix", response_model=FindingResponse)
async def trigger_auto_fix(
    finding_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    finding = (await db.execute(select(Finding).where(Finding.id == finding_id))).scalar_one_or_none()
    if not finding:
        raise NotFoundError("Finding", str(finding_id))

    repo = (await db.execute(select(Repo).where(Repo.id == finding.repo_id))).scalar_one()
    if repo.org_id != user.org_id:
        raise ForbiddenError()

    if not finding.ai_suggested_fix:
        from core.exceptions import ValidationError
        raise ValidationError("Finding has no AI suggested fix")

    if finding.auto_fix_status in ("pending", "in_progress"):
        from core.exceptions import ValidationError
        raise ValidationError("Auto-fix already in progress")

    finding.auto_fix_status = "pending"
    finding.auto_fix_error = None
    await db.commit()
    await db.refresh(finding)

    settings = get_settings()
    pool = await create_pool(RedisSettings.from_dsn(settings.redis_url))
    await pool.enqueue_job("run_auto_fix", str(finding_id))
    await pool.close()

    return finding


@router.get("/{finding_id}/events", response_model=list[FindingEventResponse])
async def list_finding_events(
    finding_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    finding = (await db.execute(select(Finding).where(Finding.id == finding_id))).scalar_one_or_none()
    if not finding:
        raise NotFoundError("Finding", str(finding_id))

    repo = (await db.execute(select(Repo).where(Repo.id == finding.repo_id))).scalar_one()
    if repo.org_id != user.org_id:
        raise ForbiddenError()

    stmt = select(FindingEvent).where(FindingEvent.finding_id == finding_id).order_by(FindingEvent.created_at)
    return (await db.execute(stmt)).scalars().all()
