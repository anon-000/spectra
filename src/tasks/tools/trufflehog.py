import json
from pathlib import Path

from core.logging import get_logger
from tasks.tools.base import BaseTool, RawFinding

logger = get_logger(__name__)


class TrufflehogTool(BaseTool):
    name = "trufflehog"

    async def run(self, repo_path: Path) -> list[RawFinding]:
        # Write exclude patterns to a temp file — skip .git/ to avoid
        # false positives on the x-access-token embedded in the clone URL.
        exclude_file = repo_path / ".trufflehog-exclude"
        exclude_file.write_text(".git/\n")
        try:
            returncode, stdout, stderr = await self._exec(
                "trufflehog", "filesystem", "--json", "--no-update",
                "--exclude-paths", str(exclude_file),
                str(repo_path),
                cwd=repo_path,
            )
        finally:
            exclude_file.unlink(missing_ok=True)

        findings = []
        for line in stdout.strip().splitlines():
            if not line:
                continue
            try:
                result = json.loads(line)
            except json.JSONDecodeError:
                continue

            source_meta = result.get("SourceMetadata", {}).get("Data", {}).get("Filesystem", {})
            findings.append(
                RawFinding(
                    tool=self.name,
                    rule_id=result.get("DetectorName", "unknown"),
                    file_path=source_meta.get("file", ""),
                    line_start=source_meta.get("line"),
                    severity="critical",
                    category="secret",
                    title=f"Secret detected: {result.get('DetectorName', 'unknown')}",
                    description=f"Verified: {result.get('Verified', False)}",
                    metadata={"verified": result.get("Verified", False)},
                )
            )
        return findings
