import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.exceptions import ForbiddenError, NotFoundError
from db.models.repo import Repo
from db.models.scan import Scan
from db.models.user import User
from dependencies import get_current_user, get_db
from schemas.scan import ManualScanRequest, ScanResponse
from services.scan_orchestrator import enqueue_manual_scan

router = APIRouter(prefix="/scans", tags=["scans"])


@router.get("", response_model=list[ScanResponse])
async def list_scans(
    repo_id: uuid.UUID | None = Query(None),
    status: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not user.org_id:
        return []

    stmt = (
        select(Scan)
        .join(Repo, Scan.repo_id == Repo.id)
        .where(Repo.org_id == user.org_id)
    )
    if repo_id:
        stmt = stmt.where(Scan.repo_id == repo_id)
    if status:
        stmt = stmt.where(Scan.status == status)

    stmt = stmt.order_by(Scan.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    return (await db.execute(stmt)).scalars().all()


@router.get("/{scan_id}", response_model=ScanResponse)
async def get_scan(
    scan_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Scan).where(Scan.id == scan_id)
    scan = (await db.execute(stmt)).scalar_one_or_none()
    if not scan:
        raise NotFoundError("Scan", str(scan_id))

    repo = (await db.execute(select(Repo).where(Repo.id == scan.repo_id))).scalar_one()
    if repo.org_id != user.org_id:
        raise ForbiddenError()
    return scan


@router.post("", response_model=ScanResponse, status_code=201)
async def trigger_manual_scan(
    body: ManualScanRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = (await db.execute(select(Repo).where(Repo.id == body.repo_id))).scalar_one_or_none()
    if not repo:
        raise NotFoundError("Repo", str(body.repo_id))
    if repo.org_id != user.org_id:
        raise ForbiddenError()

    from db.models.organization import Organization
    org = (await db.execute(select(Organization).where(Organization.id == repo.org_id))).scalar_one()

    scan_id = await enqueue_manual_scan(
        repo_id=str(repo.id),
        commit_sha=body.commit_sha,
        branch=body.branch,
        installation_id=org.installation_id,
        clone_url=f"https://github.com/{repo.full_name}.git",
        repo_full_name=repo.full_name,
    )

    scan = (await db.execute(select(Scan).where(Scan.id == uuid.UUID(scan_id)))).scalar_one()
    return scan
