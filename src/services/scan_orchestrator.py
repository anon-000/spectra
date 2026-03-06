from arq import create_pool
from arq.connections import RedisSettings
from sqlalchemy import select

from config import get_settings
from core.logging import get_logger
from db.engine import async_session
from db.models.organization import Organization
from db.models.repo import Repo
from db.models.scan import Scan
from services.github import get_installation_token, create_check_run

logger = get_logger(__name__)


def _redis_settings() -> RedisSettings:
    settings = get_settings()
    return RedisSettings.from_dsn(settings.redis_url)


async def handle_pr_event(payload: dict) -> None:
    pr = payload["pull_request"]
    repo_data = payload["repository"]
    installation_id = payload["installation"]["id"]

    async with async_session() as db:
        stmt = select(Repo).where(Repo.github_id == repo_data["id"])
        result = await db.execute(stmt)
        repo = result.scalar_one_or_none()

        if not repo or not repo.is_active:
            logger.info("repo_not_tracked", github_id=repo_data["id"])
            return

        scan = Scan(
            repo_id=repo.id,
            pr_number=pr["number"],
            commit_sha=pr["head"]["sha"],
            branch=pr["head"]["ref"],
            trigger="pull_request",
            status="pending",
        )
        db.add(scan)
        await db.commit()
        await db.refresh(scan)

    # Create a GitHub Check Run immediately (shows "in progress" on the PR)
    try:
        token = await get_installation_token(installation_id)
        check_run_id = await create_check_run(token, repo_data["full_name"], pr["head"]["sha"])
        if check_run_id:
            async with async_session() as db:
                stmt = select(Scan).where(Scan.id == scan.id)
                s = (await db.execute(stmt)).scalar_one()
                s.check_run_id = check_run_id
                await db.commit()
    except Exception:
        logger.exception("pending_check_run_failed", scan_id=str(scan.id))

    pool = await create_pool(_redis_settings())
    await pool.enqueue_job(
        "run_scan",
        str(scan.id),
        installation_id,
        repo_data["clone_url"],
        repo_data["full_name"],
    )
    await pool.close()
    logger.info("scan_enqueued", scan_id=str(scan.id))


async def handle_installation_event(payload: dict) -> None:
    installation = payload["installation"]
    account = installation["account"]

    async with async_session() as db:
        stmt = select(Organization).where(Organization.github_id == account["id"])
        result = await db.execute(stmt)
        org = result.scalar_one_or_none()

        if not org:
            org = Organization(
                github_id=account["id"],
                name=account["login"],
                installation_id=installation["id"],
            )
            db.add(org)
        else:
            org.installation_id = installation["id"]

        await db.commit()

        # Sync repos from installation
        for repo_data in payload.get("repositories", []):
            existing = select(Repo).where(Repo.github_id == repo_data["id"])
            res = await db.execute(existing)
            if not res.scalar_one_or_none():
                db.add(
                    Repo(
                        github_id=repo_data["id"],
                        full_name=repo_data["full_name"],
                        org_id=org.id,
                    )
                )
        await db.commit()

    logger.info("installation_created", org=account["login"])


async def handle_push_event(payload: dict) -> None:
    """Handle a push event — only scan pushes to the repo's default branch."""
    ref = payload.get("ref", "")
    repo_data = payload["repository"]
    installation_id = payload["installation"]["id"]

    default_branch = repo_data.get("default_branch", "main")
    if ref != f"refs/heads/{default_branch}":
        logger.info("push_not_default_branch", ref=ref, default_branch=default_branch)
        return

    commit_sha = payload.get("after")
    if not commit_sha or commit_sha == "0" * 40:
        # Branch deleted
        return

    async with async_session() as db:
        stmt = select(Repo).where(Repo.github_id == repo_data["id"])
        result = await db.execute(stmt)
        repo = result.scalar_one_or_none()

        if not repo or not repo.is_active:
            logger.info("repo_not_tracked", github_id=repo_data["id"])
            return

        scan = Scan(
            repo_id=repo.id,
            commit_sha=commit_sha,
            branch=default_branch,
            trigger="push",
            status="pending",
        )
        db.add(scan)
        await db.commit()
        await db.refresh(scan)

    # Create pending check run
    try:
        token = await get_installation_token(installation_id)
        check_run_id = await create_check_run(token, repo_data["full_name"], commit_sha)
        if check_run_id:
            async with async_session() as db:
                stmt = select(Scan).where(Scan.id == scan.id)
                s = (await db.execute(stmt)).scalar_one()
                s.check_run_id = check_run_id
                await db.commit()
    except Exception:
        logger.exception("pending_check_run_failed", scan_id=str(scan.id))

    pool = await create_pool(_redis_settings())
    await pool.enqueue_job(
        "run_scan",
        str(scan.id),
        installation_id,
        repo_data["clone_url"],
        repo_data["full_name"],
    )
    await pool.close()
    logger.info("push_scan_enqueued", scan_id=str(scan.id), branch=default_branch)


async def enqueue_manual_scan(
    repo_id: str, commit_sha: str, branch: str, installation_id: int, clone_url: str,
    repo_full_name: str,
) -> str:
    """Enqueue a manual scan from the API. Returns scan ID."""
    from uuid import UUID

    async with async_session() as db:
        scan = Scan(
            repo_id=UUID(repo_id),
            commit_sha=commit_sha,
            branch=branch,
            trigger="manual",
            status="pending",
        )
        db.add(scan)
        await db.commit()
        await db.refresh(scan)

    pool = await create_pool(_redis_settings())
    await pool.enqueue_job("run_scan", str(scan.id), installation_id, clone_url, repo_full_name)
    await pool.close()
    return str(scan.id)
