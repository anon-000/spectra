"""AI auto-fix PR generation via Claude + GitHub API."""

import base64

import anthropic
import httpx

from config import get_settings
from core.logging import get_logger

logger = get_logger(__name__)

GITHUB_API = "https://api.github.com"

FIX_PROMPT = """You are a security engineer fixing a vulnerability in source code.

FINDING:
- Title: {title}
- Severity: {severity}
- Category: {category}
- Rule: {rule_id}
- File: {file_path}:{line_start}
- Description: {description}
- AI Suggested Fix: {suggested_fix}

CURRENT FILE CONTENT:
```{language}
{file_content}
```

INSTRUCTIONS:
1. Fix ONLY the security issue described above
2. Do NOT change any other code, formatting, or logic
3. Return the COMPLETE corrected file content
4. Do NOT wrap in markdown code blocks
5. Do NOT add comments explaining the fix unless critical for understanding

Return ONLY the fixed file content, nothing else."""


async def get_file_from_github(
    token: str, repo: str, path: str, ref: str,
) -> tuple[str, str]:
    """Fetch file content and blob SHA from GitHub."""
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{GITHUB_API}/repos/{repo}/contents/{path}",
            params={"ref": ref},
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
            },
        )
        resp.raise_for_status()
        data = resp.json()
        content = base64.b64decode(data["content"]).decode("utf-8")
        return content, data["sha"]


async def generate_fix_with_claude(
    finding_title: str,
    finding_severity: str,
    finding_category: str,
    finding_rule_id: str,
    finding_file_path: str,
    finding_line_start: int | None,
    finding_description: str | None,
    finding_suggested_fix: str | None,
    file_content: str,
    language: str,
) -> str:
    """Use Claude to generate a security fix for the file."""
    settings = get_settings()
    prompt = FIX_PROMPT.format(
        title=finding_title,
        severity=finding_severity,
        category=finding_category,
        rule_id=finding_rule_id,
        file_path=finding_file_path,
        line_start=finding_line_start or "N/A",
        description=finding_description or "N/A",
        suggested_fix=finding_suggested_fix or "N/A",
        file_content=file_content,
        language=language,
    )

    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
    message = await client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=8192,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text


async def create_branch(token: str, repo: str, branch_name: str, from_ref: str) -> None:
    """Create a new branch from a ref."""
    async with httpx.AsyncClient() as client:
        # Get the SHA of the base ref
        resp = await client.get(
            f"{GITHUB_API}/repos/{repo}/git/ref/heads/{from_ref}",
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
            },
        )
        resp.raise_for_status()
        sha = resp.json()["object"]["sha"]

        # Create the branch
        resp = await client.post(
            f"{GITHUB_API}/repos/{repo}/git/refs",
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
            },
            json={"ref": f"refs/heads/{branch_name}", "sha": sha},
        )
        resp.raise_for_status()


async def commit_file(
    token: str, repo: str, path: str, content: str, blob_sha: str, branch: str, message: str,
) -> None:
    """Update a file on a branch via the GitHub Contents API."""
    async with httpx.AsyncClient() as client:
        resp = await client.put(
            f"{GITHUB_API}/repos/{repo}/contents/{path}",
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
            },
            json={
                "message": message,
                "content": base64.b64encode(content.encode("utf-8")).decode("ascii"),
                "sha": blob_sha,
                "branch": branch,
            },
        )
        resp.raise_for_status()


async def create_pull_request(
    token: str, repo: str, title: str, body: str, head: str, base: str,
) -> dict:
    """Create a pull request and return the response data."""
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{GITHUB_API}/repos/{repo}/pulls",
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
            },
            json={"title": title, "body": body, "head": head, "base": base},
        )
        resp.raise_for_status()
        return resp.json()
