import uuid

import httpx
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.exceptions import ForbiddenError, NotFoundError
from core.logging import get_logger
from db.models.repo import Repo
from db.models.user import User
from dependencies import get_current_user, get_db
from schemas.repo import RepoResponse, RepoUpdate

logger = get_logger(__name__)
router = APIRouter(prefix="/repos", tags=["repos"])


async def _sync_repos_from_github(user: User, db: AsyncSession) -> None:
    """Fetch repos from GitHub using the user's token and upsert into the DB."""
    headers = {
        "Authorization": f"Bearer {user.github_access_token}",
        "Accept": "application/vnd.github+json",
    }
    all_repos: list[dict] = []
    page = 1

    seen_ids: set[int] = set()

    async with httpx.AsyncClient() as client:
        # 1) Fetch repos from GitHub App installations (org repos)
        while True:
            resp = await client.get(
                "https://api.github.com/user/installations",
                headers=headers,
                params={"page": page, "per_page": 100},
            )
            if resp.status_code != 200:
                logger.warning("github_installations_fetch_failed", status=resp.status_code)
                break

            installations = resp.json().get("installations", [])
            for inst in installations:
                repos_resp = await client.get(
                    f"https://api.github.com/user/installations/{inst['id']}/repositories",
                    headers=headers,
                    params={"per_page": 100},
                )
                if repos_resp.status_code == 200:
                    for r in repos_resp.json().get("repositories", []):
                        if r["id"] not in seen_ids:
                            all_repos.append(r)
                            seen_ids.add(r["id"])

            if len(installations) < 100:
                break
            page += 1

        # 2) Fetch user's own repos (personal + repos they have access to)
        page = 1
        while True:
            resp = await client.get(
                "https://api.github.com/user/repos",
                headers=headers,
                params={"page": page, "per_page": 100, "sort": "updated"},
            )
            if resp.status_code != 200:
                logger.warning("github_user_repos_fetch_failed", status=resp.status_code)
                break

            repos_page = resp.json()
            for r in repos_page:
                if r["id"] not in seen_ids:
                    all_repos.append(r)
                    seen_ids.add(r["id"])

            if len(repos_page) < 100:
                break
            page += 1

    for repo_data in all_repos:
        stmt = select(Repo).where(Repo.github_id == repo_data["id"])
        result = await db.execute(stmt)
        existing = result.scalar_one_or_none()
        if not existing:
            db.add(Repo(
                github_id=repo_data["id"],
                full_name=repo_data["full_name"],
                default_branch=repo_data.get("default_branch", "main"),
                language=repo_data.get("language"),
                org_id=user.org_id,
            ))
        else:
            existing.full_name = repo_data["full_name"]
            existing.default_branch = repo_data.get("default_branch", "main")
            existing.language = repo_data.get("language")

    await db.commit()
    logger.info("repos_synced_from_github", count=len(all_repos), user=user.github_login)


@router.post("/sync", response_model=list[RepoResponse])
async def sync_repos(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not user.org_id:
        return []
    await _sync_repos_from_github(user, db)
    stmt = select(Repo).where(Repo.org_id == user.org_id).order_by(Repo.full_name)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("", response_model=list[RepoResponse])
async def list_repos(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not user.org_id:
        return []

    stmt = select(Repo).where(Repo.org_id == user.org_id).order_by(Repo.full_name)
    result = await db.execute(stmt)
    repos = result.scalars().all()

    # If no repos in DB yet, sync from GitHub
    if not repos:
        await _sync_repos_from_github(user, db)
        result = await db.execute(stmt)
        repos = result.scalars().all()

    return repos


@router.get("/{repo_id}", response_model=RepoResponse)
async def get_repo(
    repo_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Repo).where(Repo.id == repo_id)
    result = await db.execute(stmt)
    repo = result.scalar_one_or_none()
    if not repo:
        raise NotFoundError("Repo", str(repo_id))
    if repo.org_id != user.org_id:
        raise ForbiddenError()
    return repo


@router.patch("/{repo_id}", response_model=RepoResponse)
async def update_repo(
    repo_id: uuid.UUID,
    body: RepoUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Repo).where(Repo.id == repo_id)
    result = await db.execute(stmt)
    repo = result.scalar_one_or_none()
    if not repo:
        raise NotFoundError("Repo", str(repo_id))
    if repo.org_id != user.org_id:
        raise ForbiddenError()

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(repo, field, value)

    await db.commit()
    await db.refresh(repo)
    return repo
