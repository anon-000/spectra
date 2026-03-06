import asyncio

import anthropic

from config import get_settings
from core.logging import get_logger
from tasks.tools.base import RawFinding

logger = get_logger(__name__)

_semaphore = asyncio.Semaphore(5)

TRIAGE_PROMPT = """You are a security engineer triaging a code scanning finding.
Analyze this finding and respond in JSON with these fields:
- severity: "critical", "high", "medium", or "low" (your adjusted assessment)
- explanation: 1-2 sentence explanation of the real-world impact
- suggested_fix: concise remediation guidance
- confidence: float between 0.0 and 1.0 indicating your confidence in this assessment
- verdict: "true_positive", "false_positive", or "needs_review"

Finding:
- Tool: {tool}
- Rule: {rule_id}
- Category: {category}
- Original severity: {severity}
- Title: {title}
- File: {file_path}:{line_start}
- Code snippet: {snippet}
- Description: {description}

Respond ONLY with valid JSON."""


async def triage_finding(finding: RawFinding) -> dict:
    """Call Claude API to triage a single finding. Returns dict with severity, explanation, suggested_fix."""
    settings = get_settings()
    if not settings.anthropic_api_key:
        return {}

    prompt = TRIAGE_PROMPT.format(
        tool=finding.tool,
        rule_id=finding.rule_id,
        category=finding.category,
        severity=finding.severity,
        title=finding.title,
        file_path=finding.file_path,
        line_start=finding.line_start or "N/A",
        snippet=(finding.snippet or "N/A")[:500],
        description=(finding.description or "N/A")[:500],
    )

    async with _semaphore:
        try:
            client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
            message = await client.messages.create(
                model="claude-sonnet-4-5-20250929",
                max_tokens=512,
                messages=[{"role": "user", "content": prompt}],
            )
            import json

            return json.loads(message.content[0].text)
        except Exception:
            logger.exception("ai_triage_failed", rule_id=finding.rule_id)
            return {}
