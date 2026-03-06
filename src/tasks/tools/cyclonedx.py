import json
import tempfile
from pathlib import Path

from core.logging import get_logger
from tasks.tools.base import BaseTool, RawFinding

logger = get_logger(__name__)


class CyclonedxTool(BaseTool):
    name = "cyclonedx"

    async def run(self, repo_path: Path) -> list[RawFinding]:
        """Generate SBOM and extract license findings."""
        sbom_file = Path(tempfile.mktemp(suffix=".json", prefix="cdxgen-"))
        try:
            returncode, stdout, stderr = await self._exec(
                "cdxgen", "-o", str(sbom_file), "--spec-version", "1.5", str(repo_path),
                cwd=repo_path,
            )

            if returncode != 0:
                logger.error("cyclonedx_failed", stderr=stderr[:500])
                return []

            if not sbom_file.exists():
                logger.error("cyclonedx_no_output_file")
                return []

            try:
                sbom = json.loads(sbom_file.read_text())
            except json.JSONDecodeError:
                logger.error("cyclonedx_invalid_json")
                return []
        finally:
            sbom_file.unlink(missing_ok=True)

        copyleft = {"GPL-2.0", "GPL-3.0", "AGPL-3.0", "LGPL-2.1", "LGPL-3.0", "SSPL-1.0"}
        findings = []

        for component in sbom.get("components", []):
            for lic in component.get("licenses", []):
                license_id = lic.get("license", {}).get("id", "")
                if not license_id:
                    license_id = lic.get("expression", "unknown")

                # Only flag copyleft or unknown licenses
                is_copyleft = any(c in license_id for c in copyleft)
                is_unknown = license_id == "unknown"

                if not is_copyleft and not is_unknown:
                    continue

                severity = "high" if is_copyleft else "low"
                findings.append(
                    RawFinding(
                        tool=self.name,
                        rule_id=f"license/{license_id}",
                        file_path="sbom",
                        severity=severity,
                        category="license",
                        title=f"License: {license_id} in {component.get('name', 'unknown')}",
                        description=f"Component {component.get('name')}@{component.get('version')} uses {license_id}",
                        package_name=component.get("name"),
                        package_version=component.get("version"),
                    )
                )
        return findings
