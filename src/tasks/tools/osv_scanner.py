import json
from pathlib import Path

from core.logging import get_logger
from tasks.tools.base import BaseTool, RawFinding

logger = get_logger(__name__)

SEVERITY_MAP = {"CRITICAL": "critical", "HIGH": "high", "MODERATE": "medium", "LOW": "low"}


class OsvScannerTool(BaseTool):
    name = "osv-scanner"

    async def run(self, repo_path: Path) -> list[RawFinding]:
        returncode, stdout, stderr = await self._exec(
            "osv-scanner", "--format", "json", "-r", str(repo_path),
            cwd=repo_path,
        )

        if returncode not in (0, 1):
            logger.error("osv_scanner_failed", stderr=stderr[:500])
            return []

        try:
            data = json.loads(stdout)
        except json.JSONDecodeError:
            logger.error("osv_scanner_invalid_json")
            return []

        findings = []
        for result in data.get("results", []):
            source_path = result.get("source", {}).get("path", "")
            for pkg in result.get("packages", []):
                pkg_info = pkg.get("package", {})
                for vuln in pkg.get("vulnerabilities", []):
                    severity = "medium"
                    for db_specific in vuln.get("database_specific", {}).get("severity", []):
                        if isinstance(db_specific, str):
                            severity = SEVERITY_MAP.get(db_specific.upper(), severity)

                    aliases = vuln.get("aliases", [])
                    cve = next((a for a in aliases if a.startswith("CVE-")), None)

                    findings.append(
                        RawFinding(
                            tool=self.name,
                            rule_id=vuln.get("id", "unknown"),
                            file_path=source_path,
                            severity=severity,
                            category="sca",
                            title=vuln.get("summary", vuln.get("id", ""))[:512],
                            description=vuln.get("details", ""),
                            package_name=pkg_info.get("name"),
                            package_version=pkg_info.get("version"),
                            cve_id=cve,
                        )
                    )
        return findings
