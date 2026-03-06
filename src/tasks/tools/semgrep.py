import json
from pathlib import Path

from core.logging import get_logger
from tasks.tools.base import BaseTool, RawFinding

logger = get_logger(__name__)

SEVERITY_MAP = {"ERROR": "high", "WARNING": "medium", "INFO": "low"}


class SemgrepTool(BaseTool):
    name = "semgrep"

    async def run(self, repo_path: Path) -> list[RawFinding]:
        returncode, stdout, stderr = await self._exec(
            "semgrep", "scan", "--json", "--config", "auto", str(repo_path),
            cwd=repo_path,
        )

        if returncode not in (0, 1):  # 1 means findings found
            logger.error("semgrep_failed", stderr=stderr[:500])
            return []

        try:
            data = json.loads(stdout)
        except json.JSONDecodeError:
            logger.error("semgrep_invalid_json")
            return []

        findings = []
        for result in data.get("results", []):
            findings.append(
                RawFinding(
                    tool=self.name,
                    rule_id=result.get("check_id", "unknown"),
                    file_path=result.get("path", ""),
                    line_start=result.get("start", {}).get("line"),
                    line_end=result.get("end", {}).get("line"),
                    snippet=result.get("extra", {}).get("lines", ""),
                    severity=SEVERITY_MAP.get(
                        result.get("extra", {}).get("severity", ""), "medium"
                    ),
                    category="sast",
                    title=result.get("extra", {}).get("message", "")[:512],
                    description=result.get("extra", {}).get("message", ""),
                )
            )
        return findings
