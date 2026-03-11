import asyncio
from dataclasses import asdict
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select

from core.logging import get_logger
from db.engine import async_session
from db.models.finding import Finding
from db.models.scan import Scan
from services.github import clone_repo, cleanup_clone, get_installation_token
from services.scan_events import publish_scan_progress
from storage.s3 import ensure_bucket, upload_scan_results
from tasks.ai_triage import triage_finding
from tasks.normalizer import deduplicate
from tasks.tools.base import RawFinding
from tasks.tools.semgrep import SemgrepTool
from tasks.tools.trufflehog import TrufflehogTool
from tasks.tools.osv_scanner import OsvScannerTool
from tasks.tools.cyclonedx import CyclonedxTool

logger = get_logger(__name__)

TOOLS = [SemgrepTool(), TrufflehogTool(), OsvScannerTool(), CyclonedxTool()]


async def run_scan(ctx: dict, scan_id: str, installation_id: int, clone_url: str, repo_full_name: str) -> None:
    logger.info("scan_started", scan_id=scan_id)

    async with async_session() as db:
        stmt = select(Scan).where(Scan.id == UUID(scan_id))
        result = await db.execute(stmt)
        scan = result.scalar_one()
        scan.status = "running"
        scan.started_at = datetime.now(UTC)
        await db.commit()

        # Get org_id for SSE events
        from db.models.repo import Repo
        repo_row = (await db.execute(select(Repo).where(Repo.id == scan.repo_id))).scalar_one()
        org_id = str(repo_row.org_id)

    async def emit(stage: str, message: str, pct: int = 0, **kw):
        await publish_scan_progress(scan_id, org_id, stage, "running", message, pct, **kw)

    repo_path = None
    try:
        await emit("cloning", "Cloning repository…", 5)
        token = await get_installation_token(installation_id)
        repo_path = await clone_repo(clone_url, token, scan.commit_sha)
        await emit("cloning", "Repository cloned", 10)

        ensure_bucket()

        await emit("sast_running", "Running SAST & security scanners…", 15)
        # Run all tools concurrently
        tool_results = await asyncio.gather(
            *[tool.run(repo_path) for tool in TOOLS],
            return_exceptions=True,
        )

        all_findings: list[RawFinding] = []
        for tool, result in zip(TOOLS, tool_results):
            if isinstance(result, Exception):
                logger.error("tool_failed", tool=tool.name, error=str(result))
                continue
            upload_scan_results(scan_id, tool.name, [asdict(f) for f in result])
            all_findings.extend(result)

        await emit("normalizing", "Normalizing and deduplicating findings…", 50)
        # Normalize and dedup
        unique = deduplicate(all_findings)

        # AI triage concurrently
        await emit("ai_triage", f"AI triaging {len(unique)} findings…", 60)
        triage_tasks = [triage_finding(f) for f, _fp in unique]
        triage_results = await asyncio.gather(*triage_tasks, return_exceptions=True)

        # Persist findings with cross-scan deduplication
        counters = {"total": 0, "critical": 0, "high": 0}
        scan_findings = []
        async with async_session() as db:
            for (raw, fingerprint), triage in zip(unique, triage_results):
                ai = triage if isinstance(triage, dict) else {}

                # Check if this finding has been seen before in this repo
                stmt = select(Finding).where(
                    Finding.repo_id == scan.repo_id,
                    Finding.fingerprint == fingerprint
                )
                result = await db.execute(stmt)
                existing_finding = result.scalars().first()

                if existing_finding:
                    # Cross-scan dedup: update last_seen, do not create duplicate
                    existing_finding.last_seen = datetime.now(UTC)
                    # We do NOT increment the new findings counters, and do NOT add to PR comments
                    continue

                # New finding, create it
                finding = Finding(
                    scan_id=UUID(scan_id),
                    repo_id=scan.repo_id,
                    tool=raw.tool,
                    rule_id=raw.rule_id,
                    file_path=raw.file_path,
                    line_start=raw.line_start,
                    line_end=raw.line_end,
                    snippet=raw.snippet,
                    severity=raw.severity,
                    category=raw.category,
                    title=raw.title,
                    description=raw.description,
                    fingerprint=fingerprint,
                    ai_severity=ai.get("severity"),
                    ai_explanation=ai.get("explanation"),
                    ai_suggested_fix=ai.get("suggested_fix"),
                    confidence=ai.get("confidence"),
                    ai_verdict=ai.get("verdict"),
                    pr_number=scan.pr_number,
                    commit_sha=scan.commit_sha,
                    first_seen=datetime.now(UTC),
                    last_seen=datetime.now(UTC),
                    package_name=raw.package_name,
                    package_version=raw.package_version,
                    cve_id=raw.cve_id,
                    cwe_id=raw.cwe_id if hasattr(raw, "cwe_id") else None,
                    metadata_json=raw.metadata or None,
                )
                db.add(finding)
                scan_findings.append(finding)

                counters["total"] += 1
                effective_sev = ai.get("severity", raw.severity)
                if effective_sev == "critical":
                    counters["critical"] += 1
                elif effective_sev == "high":
                    counters["high"] += 1

            await db.commit()

        await emit("policy_eval", "Evaluating security policies…", 85)

        # Update scan status
        async with async_session() as db:
            stmt = select(Scan).where(Scan.id == UUID(scan_id))
            result = await db.execute(stmt)
            scan = result.scalar_one()
            scan.status = "completed"
            scan.finished_at = datetime.now(UTC)
            scan.findings_count = counters["total"]
            scan.critical_count = counters["critical"]
            scan.high_count = counters["high"]
            await db.commit()

        # Post-scan: policy eval + notifications
        async with async_session() as db:
            from services.policy_engine import evaluate_policies
            from services.notification import notify_github, notify_slack

            stmt = select(Scan).where(Scan.id == UUID(scan_id))
            scan = (await db.execute(stmt)).scalar_one()
            eval_result = await evaluate_policies(db, scan)

            # Load findings for inline PR comments
            findings_stmt = select(Finding).where(Finding.scan_id == UUID(scan_id))
            scan_findings = (await db.execute(findings_stmt)).scalars().all()

            try:
                await notify_github(token, repo_full_name, scan, eval_result, findings=scan_findings)
            except Exception:
                logger.exception("github_notification_failed", scan_id=scan_id)

            try:
                await notify_slack(scan, eval_result)
            except Exception:
                logger.exception("slack_notification_failed", scan_id=scan_id)

        await publish_scan_progress(
            scan_id, org_id, "completed", "completed",
            f"Scan completed — {counters['total']} new findings", 100,
            findings_count=counters["total"],
            critical_count=counters["critical"],
            high_count=counters["high"],
        )
        logger.info("scan_completed", scan_id=scan_id, findings=counters["total"])

    except Exception:
        logger.exception("scan_failed", scan_id=scan_id)
        async with async_session() as db:
            stmt = select(Scan).where(Scan.id == UUID(scan_id))
            result = await db.execute(stmt)
            scan = result.scalar_one()
            scan.status = "failed"
            scan.finished_at = datetime.now(UTC)
            await db.commit()
        await publish_scan_progress(scan_id, org_id, "failed", "failed", "Scan failed", 0)
        raise
    finally:
        if repo_path:
            cleanup_clone(repo_path)
