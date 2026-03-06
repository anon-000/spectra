import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path

from core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class RawFinding:
    tool: str
    rule_id: str
    file_path: str
    line_start: int | None = None
    line_end: int | None = None
    snippet: str | None = None
    severity: str = "medium"
    category: str = "sast"
    title: str = ""
    description: str = ""
    package_name: str | None = None
    package_version: str | None = None
    cve_id: str | None = None
    metadata: dict = field(default_factory=dict)


class BaseTool(ABC):
    name: str = "base"

    @abstractmethod
    async def run(self, repo_path: Path) -> list[RawFinding]:
        ...

    async def _exec(self, *cmd: str, cwd: Path) -> tuple[int, str, str]:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=cwd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        return proc.returncode, stdout.decode(), stderr.decode()
