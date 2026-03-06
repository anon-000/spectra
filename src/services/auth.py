import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import get_settings
from core.exceptions import AuthError
from core.logging import get_logger
from core.security import create_access_token
from db.models.organization import Organization
from db.models.user import User

logger = get_logger(__name__)


async def exchange_github_code(code: str) -> dict:
    """Exchange GitHub OAuth code for access token and user info."""
    settings = get_settings()

    async with httpx.AsyncClient() as client:
        token_resp = await client.post(
            "https://github.com/login/oauth/access_token",
            json={
                "client_id": settings.github_client_id,
                "client_secret": settings.github_client_secret,
                "code": code,
            },
            headers={"Accept": "application/json"},
        )
        token_data = token_resp.json()

        if "access_token" not in token_data:
            raise AuthError("Failed to exchange GitHub code")

        gh_token = token_data["access_token"]

        user_resp = await client.get(
            "https://api.github.com/user",
            headers={"Authorization": f"Bearer {gh_token}"},
        )
        user_data = user_resp.json()

    return {"token": gh_token, "user": user_data}


async def _resolve_org(db: AsyncSession, gh_token: str, gh_user: dict) -> Organization | None:
    """Try to match the user to an existing Organization in the DB.

    Strategy:
    1. Query GitHub App installations accessible to the user → match against organizations table.
    2. Fallback: check user's org memberships.
    3. Fallback: check if the user's own account has a GitHub App installation.
    """
    headers = {"Authorization": f"Bearer {gh_token}", "Accept": "application/vnd.github+json"}

    async with httpx.AsyncClient() as client:
        # 1) Check GitHub App installations accessible to this user
        installations_resp = await client.get("https://api.github.com/user/installations", headers=headers)
        if installations_resp.status_code == 200:
            installations = installations_resp.json().get("installations", [])
            install_account_ids = [inst["account"]["id"] for inst in installations]
            logger.info("org_resolution_installations_found", account_ids=install_account_ids, user=gh_user["login"])
            if install_account_ids:
                stmt = select(Organization).where(Organization.github_id.in_(install_account_ids))
                result = await db.execute(stmt)
                org = result.scalars().first()
                if org:
                    return org

        # 2) Check user's GitHub org memberships
        orgs_resp = await client.get("https://api.github.com/user/orgs", headers=headers)
        if orgs_resp.status_code == 200:
            gh_org_ids = [org["id"] for org in orgs_resp.json()]
            if gh_org_ids:
                stmt = select(Organization).where(Organization.github_id.in_(gh_org_ids))
                result = await db.execute(stmt)
                org = result.scalars().first()
                if org:
                    return org

        # 3) Check if the user's personal account has an app installation
        stmt = select(Organization).where(Organization.github_id == gh_user["id"])
        result = await db.execute(stmt)
        return result.scalar_one_or_none()


async def get_or_create_user(db: AsyncSession, github_data: dict) -> User:
    """Find existing user by GitHub ID or create a new one. Auto-links to organization."""
    gh_token = github_data["token"]
    gh_user = github_data["user"]

    stmt = select(User).where(User.github_id == gh_user["id"])
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if user:
        user.github_login = gh_user["login"]
        user.avatar_url = gh_user.get("avatar_url")
        user.github_access_token = gh_token
    else:
        user = User(
            github_id=gh_user["id"],
            github_login=gh_user["login"],
            email=gh_user.get("email"),
            avatar_url=gh_user.get("avatar_url"),
            github_access_token=gh_token,
        )
        db.add(user)

    # Auto-link to organization if not already linked
    if not user.org_id:
        try:
            org = await _resolve_org(db, gh_token, gh_user)
            if org:
                user.org_id = org.id
                logger.info("user_org_linked", user=gh_user["login"], org=org.name)
        except Exception:
            logger.exception("org_resolution_failed", user=gh_user["login"])

    await db.commit()
    await db.refresh(user)
    return user


def issue_jwt(user: User) -> str:
    return create_access_token({"sub": str(user.id), "github_login": user.github_login})
