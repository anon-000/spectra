"""Analytics endpoints for finding trends."""

import uuid
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, text, case, extract
from sqlalchemy.ext.asyncio import AsyncSession

from db.models.finding import Finding
from db.models.finding_event import FindingEvent
from db.models.repo import Repo
from db.models.user import User
from dependencies import get_current_user, get_db
from schemas.analytics import (
    AnalyticsResponse,
    CategoryCount,
    MTTRBySeverity,
    SeverityCount,
    TimeSeriesPoint,
    TopRepo,
    TopRule,
)

router = APIRouter(prefix="/analytics", tags=["analytics"])

PERIOD_DAYS = {"30d": 30, "90d": 90, "1y": 365}


@router.get("/trends", response_model=AnalyticsResponse)
async def get_trends(
    repo_id: uuid.UUID | None = Query(None),
    period: str = Query("30d"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not user.org_id:
        return AnalyticsResponse(
            total_open=0, total_resolved=0, total_suppressed=0,
            time_series=[], by_severity=[], by_category=[],
            top_rules=[], top_repos=[], mttr_by_severity=[],
        )

    days = PERIOD_DAYS.get(period, 30)
    since = datetime.now(UTC) - timedelta(days=days)

    # Determine granularity
    if days <= 30:
        trunc = "day"
    elif days <= 90:
        trunc = "week"
    else:
        trunc = "month"

    # Base filter: org-scoped findings
    org_filter = [Repo.org_id == user.org_id]
    if repo_id:
        org_filter.append(Finding.repo_id == repo_id)

    # --- Totals ---
    totals_stmt = (
        select(
            func.count().filter(Finding.status == "open").label("total_open"),
            func.count().filter(Finding.status == "resolved").label("total_resolved"),
            func.count().filter(Finding.status == "suppressed").label("total_suppressed"),
        )
        .select_from(Finding)
        .join(Repo, Finding.repo_id == Repo.id)
        .where(*org_filter)
    )
    totals = (await db.execute(totals_stmt)).one()

    # --- Time series: findings opened ---
    opened_stmt = (
        select(
            func.date_trunc(trunc, Finding.created_at).label("bucket"),
            func.count().label("opened"),
        )
        .select_from(Finding)
        .join(Repo, Finding.repo_id == Repo.id)
        .where(*org_filter, Finding.created_at >= since)
        .group_by("bucket")
        .order_by("bucket")
    )
    opened_rows = (await db.execute(opened_stmt)).all()

    # --- Time series: findings resolved ---
    resolved_filter = [Repo.org_id == user.org_id, FindingEvent.action == "status_change", FindingEvent.new_value == "resolved", FindingEvent.created_at >= since]
    if repo_id:
        resolved_filter.append(Finding.repo_id == repo_id)

    resolved_stmt = (
        select(
            func.date_trunc(trunc, FindingEvent.created_at).label("bucket"),
            func.count().label("resolved"),
        )
        .select_from(FindingEvent)
        .join(Finding, FindingEvent.finding_id == Finding.id)
        .join(Repo, Finding.repo_id == Repo.id)
        .where(*resolved_filter)
        .group_by("bucket")
        .order_by("bucket")
    )
    resolved_rows = (await db.execute(resolved_stmt)).all()

    # Merge time series
    resolved_map = {str(r.bucket.date()): r.resolved for r in resolved_rows}
    time_series = []
    for row in opened_rows:
        d = str(row.bucket.date())
        time_series.append(TimeSeriesPoint(
            date=d,
            opened=row.opened,
            resolved=resolved_map.get(d, 0),
        ))

    # --- By severity ---
    sev_stmt = (
        select(Finding.severity, func.count().label("count"))
        .join(Repo, Finding.repo_id == Repo.id)
        .where(*org_filter, Finding.status == "open")
        .group_by(Finding.severity)
    )
    sev_rows = (await db.execute(sev_stmt)).all()
    by_severity = [SeverityCount(severity=r.severity, count=r.count) for r in sev_rows]

    # --- By category ---
    cat_stmt = (
        select(Finding.category, func.count().label("count"))
        .join(Repo, Finding.repo_id == Repo.id)
        .where(*org_filter, Finding.status == "open")
        .group_by(Finding.category)
    )
    cat_rows = (await db.execute(cat_stmt)).all()
    by_category = [CategoryCount(category=r.category, count=r.count) for r in cat_rows]

    # --- Top 10 rules ---
    rules_stmt = (
        select(Finding.rule_id, Finding.tool, func.count().label("count"))
        .join(Repo, Finding.repo_id == Repo.id)
        .where(*org_filter, Finding.status == "open")
        .group_by(Finding.rule_id, Finding.tool)
        .order_by(func.count().desc())
        .limit(10)
    )
    rules_rows = (await db.execute(rules_stmt)).all()
    top_rules = [TopRule(rule_id=r.rule_id, tool=r.tool, count=r.count) for r in rules_rows]

    # --- Top 10 repos ---
    repos_stmt = (
        select(Repo.full_name, func.count().label("count"))
        .select_from(Finding)
        .join(Repo, Finding.repo_id == Repo.id)
        .where(Repo.org_id == user.org_id, Finding.status == "open")
        .group_by(Repo.full_name)
        .order_by(func.count().desc())
        .limit(10)
    )
    repos_rows = (await db.execute(repos_stmt)).all()
    top_repos = [TopRepo(full_name=r.full_name, count=r.count) for r in repos_rows]

    # --- MTTR by severity ---
    # MTTR = avg time between finding creation and the first "resolved" event
    mttr_stmt = (
        select(
            Finding.severity,
            func.avg(
                extract("epoch", FindingEvent.created_at - Finding.created_at) / 3600
            ).label("avg_hours"),
        )
        .select_from(FindingEvent)
        .join(Finding, FindingEvent.finding_id == Finding.id)
        .join(Repo, Finding.repo_id == Repo.id)
        .where(
            Repo.org_id == user.org_id,
            FindingEvent.action == "status_change",
            FindingEvent.new_value == "resolved",
        )
        .group_by(Finding.severity)
    )
    mttr_rows = (await db.execute(mttr_stmt)).all()
    mttr_by_severity = [
        MTTRBySeverity(severity=r.severity, avg_hours=round(float(r.avg_hours), 1))
        for r in mttr_rows
    ]

    return AnalyticsResponse(
        total_open=totals.total_open,
        total_resolved=totals.total_resolved,
        total_suppressed=totals.total_suppressed,
        time_series=time_series,
        by_severity=by_severity,
        by_category=by_category,
        top_rules=top_rules,
        top_repos=top_repos,
        mttr_by_severity=mttr_by_severity,
    )
