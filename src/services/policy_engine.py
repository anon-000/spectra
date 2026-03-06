from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models.finding import Finding
from db.models.policy import Policy
from db.models.scan import Scan
from schemas.policy import PolicyEvalResult


async def evaluate_policies(db: AsyncSession, scan: Scan) -> PolicyEvalResult:
    """Evaluate all active policies for the scan's organization."""
    from db.models.repo import Repo

    repo_stmt = select(Repo).where(Repo.id == scan.repo_id)
    repo = (await db.execute(repo_stmt)).scalar_one()

    stmt = select(Policy).where(Policy.org_id == repo.org_id, Policy.is_active.is_(True))
    policies = (await db.execute(stmt)).scalars().all()

    if not policies:
        return PolicyEvalResult(passed=True, violations=[])

    findings_stmt = select(Finding).where(Finding.scan_id == scan.id, Finding.status == "open")
    findings = (await db.execute(findings_stmt)).scalars().all()

    violations: list[str] = []

    for policy in policies:
        rules = policy.rules or {}

        # Check severity thresholds
        fail_on = rules.get("fail_on", [])
        for f in findings:
            effective_sev = f.ai_severity or f.severity
            if effective_sev in fail_on:
                violations.append(
                    f"Policy '{policy.name}': {effective_sev} finding '{f.title[:80]}'"
                )

        # Check max counts
        max_critical = rules.get("max_critical")
        if max_critical is not None and scan.critical_count > max_critical:
            violations.append(
                f"Policy '{policy.name}': {scan.critical_count} critical findings (max {max_critical})"
            )

        max_high = rules.get("max_high")
        if max_high is not None and scan.high_count > max_high:
            violations.append(
                f"Policy '{policy.name}': {scan.high_count} high findings (max {max_high})"
            )

        # Check blocked licenses
        blocked = rules.get("block_licenses", [])
        if blocked:
            for f in findings:
                if f.category == "license" and any(bl in f.rule_id for bl in blocked):
                    violations.append(
                        f"Policy '{policy.name}': blocked license in {f.package_name}"
                    )

    return PolicyEvalResult(passed=len(violations) == 0, violations=violations)
