import time
import tempfile
import shutil
from pathlib import Path

import httpx
import jwt as pyjwt

from config import get_settings
from core.logging import get_logger

logger = get_logger(__name__)


def _generate_app_jwt() -> str:
    settings = get_settings()
    now = int(time.time())
    payload = {"iat": now - 60, "exp": now + (10 * 60), "iss": settings.github_app_id}
    return pyjwt.encode(payload, settings.github_app_private_key, algorithm="RS256")


async def get_installation_token(installation_id: int) -> str:
    app_jwt = _generate_app_jwt()
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"https://api.github.com/app/installations/{installation_id}/access_tokens",
            headers={
                "Authorization": f"Bearer {app_jwt}",
                "Accept": "application/vnd.github+json",
            },
        )
        resp.raise_for_status()
        return resp.json()["token"]


async def clone_repo(clone_url: str, token: str, ref: str) -> Path:
    """Clone a repo to a temp directory and checkout the given ref. Returns the path."""
    import asyncio

    work_dir = Path(tempfile.mkdtemp(prefix="spectra-"))
    auth_url = clone_url.replace("https://", f"https://x-access-token:{token}@")
    repo_dir = str(work_dir / "repo")

    # Try shallow clone with --branch first (works for branch/tag names)
    proc = await asyncio.create_subprocess_exec(
        "git", "clone", "--depth", "1", "--branch", ref, auth_url, repo_dir,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    _, stderr = await proc.communicate()

    if proc.returncode != 0:
        # --branch failed (likely a commit SHA), do a full clone + checkout
        shutil.rmtree(work_dir, ignore_errors=True)
        work_dir = Path(tempfile.mkdtemp(prefix="spectra-"))
        repo_dir = str(work_dir / "repo")

        proc = await asyncio.create_subprocess_exec(
            "git", "clone", auth_url, repo_dir,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        _, stderr = await proc.communicate()
        if proc.returncode != 0:
            logger.error("git_clone_failed", stderr=stderr.decode())
            raise RuntimeError(f"git clone failed: {stderr.decode()}")

        proc = await asyncio.create_subprocess_exec(
            "git", "-C", repo_dir, "checkout", ref,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        _, stderr = await proc.communicate()
        if proc.returncode != 0:
            logger.error("git_checkout_failed", stderr=stderr.decode())
            raise RuntimeError(f"git checkout failed: {stderr.decode()}")

    return work_dir / "repo"


def cleanup_clone(path: Path) -> None:
    shutil.rmtree(path.parent, ignore_errors=True)


async def create_check_run(
    token: str, repo_full_name: str, sha: str, name: str = "Spectra Scan",
) -> int | None:
    """Create a GitHub Check Run in 'in_progress' status. Returns check_run_id."""
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"https://api.github.com/repos/{repo_full_name}/check-runs",
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
            },
            json={
                "name": name,
                "head_sha": sha,
                "status": "in_progress",
            },
        )
        if resp.status_code >= 400:
            logger.warning("create_check_run_failed", status=resp.status_code, body=resp.text[:300])
            return None
        return resp.json().get("id")


async def update_check_run(
    token: str,
    repo_full_name: str,
    check_run_id: int,
    conclusion: str,
    summary: str,
    text: str = "",
    annotations: list[dict] | None = None,
) -> None:
    """Update a GitHub Check Run to 'completed' with conclusion and output.

    conclusion: 'success', 'failure', 'neutral', 'cancelled', 'action_required'
    annotations: list of {path, start_line, end_line, annotation_level, message} (max 50 per call)
    """
    output: dict = {
        "title": "Spectra Scan Results",
        "summary": summary,
    }
    if text:
        output["text"] = text
    if annotations:
        # GitHub limits to 50 annotations per API call
        output["annotations"] = annotations[:50]

    async with httpx.AsyncClient() as client:
        resp = await client.patch(
            f"https://api.github.com/repos/{repo_full_name}/check-runs/{check_run_id}",
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
            },
            json={
                "status": "completed",
                "conclusion": conclusion,
                "output": output,
            },
        )
        if resp.status_code >= 400:
            logger.warning("update_check_run_failed", status=resp.status_code, body=resp.text[:300])

        # If > 50 annotations, send remaining in batches
        if annotations and len(annotations) > 50:
            for i in range(50, len(annotations), 50):
                batch = annotations[i : i + 50]
                await client.patch(
                    f"https://api.github.com/repos/{repo_full_name}/check-runs/{check_run_id}",
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Accept": "application/vnd.github+json",
                    },
                    json={"output": {"title": "Spectra Scan Results", "summary": summary, "annotations": batch}},
                )


async def _post_commit_status(
    token: str, repo_full_name: str, sha: str, state: str, description: str,
) -> None:
    """Fallback: post a commit status if Checks API is unavailable."""
    async with httpx.AsyncClient() as client:
        await client.post(
            f"https://api.github.com/repos/{repo_full_name}/statuses/{sha}",
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
            },
            json={
                "state": state,
                "description": description[:140],
                "context": "spectra/scan",
            },
        )


async def post_pr_comment(token: str, repo_full_name: str, pr_number: int, body: str) -> None:
    async with httpx.AsyncClient() as client:
        await client.post(
            f"https://api.github.com/repos/{repo_full_name}/issues/{pr_number}/comments",
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
            },
            json={"body": body},
        )


async def post_pr_review(
    token: str, repo_full_name: str, pr_number: int,
    comments: list[dict], body: str = "",
) -> None:
    """Post a PR review with inline comments on specific lines.

    Each comment dict should have: path, line (or position), body.
    """
    if not comments:
        return

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"https://api.github.com/repos/{repo_full_name}/pulls/{pr_number}/reviews",
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
            },
            json={
                "body": body,
                "event": "COMMENT",
                "comments": comments,
            },
        )
        if resp.status_code >= 400:
            logger.warning(
                "pr_review_failed",
                status=resp.status_code,
                response=resp.text[:500],
                comment_count=len(comments),
            )

