import hashlib
import re

from tasks.tools.base import RawFinding


def _normalize_snippet(snippet: str | None) -> str:
    if not snippet:
        return ""
    return re.sub(r"\s+", " ", snippet.strip())[:256]


def compute_fingerprint(f: RawFinding) -> str:
    """SHA-256 fingerprint for dedup: tool:rule_id:file_path:normalized_snippet."""
    parts = f"{f.tool}:{f.rule_id}:{f.file_path}:{_normalize_snippet(f.snippet)}"
    return hashlib.sha256(parts.encode()).hexdigest()


def deduplicate(findings: list[RawFinding]) -> list[tuple[RawFinding, str]]:
    """Return deduplicated findings with their fingerprints."""
    seen: set[str] = set()
    result = []
    for f in findings:
        fp = compute_fingerprint(f)
        if fp not in seen:
            seen.add(fp)
            result.append((f, fp))
    return result
