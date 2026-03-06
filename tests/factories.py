import uuid
from datetime import UTC, datetime

from spectra.db.models.finding import Finding
from spectra.db.models.organization import Organization
from spectra.db.models.repo import Repo
from spectra.db.models.scan import Scan
from spectra.db.models.user import User


def make_org(**kwargs) -> Organization:
    defaults = {
        "github_id": 12345,
        "name": "test-org",
        "installation_id": 99999,
    }
    defaults.update(kwargs)
    return Organization(**defaults)


def make_user(org: Organization | None = None, **kwargs) -> User:
    defaults = {
        "github_id": 67890,
        "github_login": "testuser",
        "email": "test@example.com",
    }
    if org:
        defaults["org_id"] = org.id
    defaults.update(kwargs)
    return User(**defaults)


def make_repo(org: Organization, **kwargs) -> Repo:
    defaults = {
        "github_id": 11111,
        "full_name": "test-org/test-repo",
        "org_id": org.id,
    }
    defaults.update(kwargs)
    return Repo(**defaults)


def make_scan(repo: Repo, **kwargs) -> Scan:
    defaults = {
        "repo_id": repo.id,
        "commit_sha": "a" * 40,
        "trigger": "pull_request",
        "status": "completed",
    }
    defaults.update(kwargs)
    return Scan(**defaults)


def make_finding(scan: Scan, repo: Repo, **kwargs) -> Finding:
    defaults = {
        "scan_id": scan.id,
        "repo_id": repo.id,
        "tool": "semgrep",
        "rule_id": "python.security.test-rule",
        "file_path": "src/app.py",
        "severity": "high",
        "category": "sast",
        "title": "Test finding",
        "fingerprint": uuid.uuid4().hex + uuid.uuid4().hex[:32],
    }
    defaults.update(kwargs)
    return Finding(**defaults)
