import httpx

from config import get_settings
from core.logging import get_logger
from db.models.finding import Finding
from db.models.scan import Scan
from schemas.policy import PolicyEvalResult
from services.github import (
    update_check_run,
    _post_commit_status,
    post_pr_comment,
    post_pr_review,
)

logger = get_logger(__name__)

SEVERITY_BADGE = {
    "critical": "🔴",
    "high": "🟠",
    "medium": "🟡",
    "low": "🔵",
}

SEVERITY_TO_ANNOTATION_LEVEL = {
    "critical": "failure",
    "high": "failure",
    "medium": "warning",
    "low": "notice",
}


def _build_pr_comment(scan: Scan, eval_result: PolicyEvalResult) -> str:
    status = "PASSED" if eval_result.passed else "FAILED"
    lines = [
        f"## Spectra Scan Results - {status}",
        "",
        f"| Metric | Count |",
        f"|--------|-------|",
        f"| Total findings | {scan.findings_count} |",
        f"| Critical | {scan.critical_count} |",
        f"| High | {scan.high_count} |",
        "",
    ]

    if eval_result.violations:
        lines.append("### Policy Violations")
        for v in eval_result.violations[:10]:
            lines.append(f"- {v}")
        if len(eval_result.violations) > 10:
            lines.append(f"- ... and {len(eval_result.violations) - 10} more")

    return "\n".join(lines)


def _build_check_summary(scan: Scan, eval_result: PolicyEvalResult) -> str:
    status = "✅ Passed" if eval_result.passed else "❌ Failed"
    lines = [
        f"## {status}",
        "",
        f"- **Total findings:** {scan.findings_count}",
        f"- **Critical:** {scan.critical_count}",
        f"- **High:** {scan.high_count}",
    ]
    if eval_result.violations:
        lines.append("")
        lines.append("### Policy Violations")
        for v in eval_result.violations[:10]:
            lines.append(f"- {v}")
    return "\n".join(lines)


def _build_annotations(findings: list[Finding]) -> list[dict]:
    """Convert findings into GitHub Check Run annotations."""
    annotations = []
    for f in findings:
        if not f.file_path or not f.line_start:
            continue

        effective_sev = f.ai_severity or f.severity
        level = SEVERITY_TO_ANNOTATION_LEVEL.get(effective_sev, "notice")

        message = f"[{f.tool}] {f.title}"
        if f.ai_explanation:
            message += f"\n{f.ai_explanation}"
        if f.ai_suggested_fix:
            message += f"\n💡 Fix: {f.ai_suggested_fix}"

        annotations.append({
            "path": f.file_path,
            "start_line": f.line_start,
            "end_line": f.line_end or f.line_start,
            "annotation_level": level,
            "message": message,
            "title": f"{effective_sev.upper()}: {f.rule_id}",
        })

    return annotations


def _build_inline_comments(findings: list[Finding]) -> list[dict]:
    """Convert findings into GitHub PR review inline comment dicts."""
    comments = []
    for f in findings:
        if not f.file_path or not f.line_start:
            continue

        badge = SEVERITY_BADGE.get(f.ai_severity or f.severity, "⚪")
        effective_sev = f.ai_severity or f.severity

        body_parts = [
            f"{badge} **{effective_sev.upper()}** — {f.title}",
            f"*Tool: {f.tool} • Rule: {f.rule_id}*",
        ]

        if f.ai_explanation:
            body_parts.append(f"\n> {f.ai_explanation}")

        if f.ai_suggested_fix:
            body_parts.append(f"\n💡 **Fix:** {f.ai_suggested_fix}")

        comments.append({
            "path": f.file_path,
            "line": f.line_start,
            "body": "\n".join(body_parts),
        })

    return comments


async def notify_github(
    token: str,
    repo_full_name: str,
    scan: Scan,
    eval_result: PolicyEvalResult,
    findings: list[Finding] | None = None,
) -> None:
    conclusion = "success" if eval_result.passed else "failure"
    summary = _build_check_summary(scan, eval_result)

    # Update GitHub Check Run (preferred) or fall back to commit status
    if scan.check_run_id:
        annotations = _build_annotations(findings) if findings else []
        await update_check_run(
            token, repo_full_name, scan.check_run_id,
            conclusion=conclusion,
            summary=summary,
            annotations=annotations,
        )
    else:
        # Fallback for scans without a check run (e.g. manual scans)
        state = "success" if eval_result.passed else "failure"
        desc = f"{scan.findings_count} findings, {scan.critical_count} critical"
        await _post_commit_status(token, repo_full_name, scan.commit_sha, state, desc)

    if scan.pr_number:
        # Post summary comment
        body = _build_pr_comment(scan, eval_result)
        await post_pr_comment(token, repo_full_name, scan.pr_number, body)

        # Post inline review comments on specific lines
        if findings:
            inline_comments = _build_inline_comments(findings)
            if inline_comments:
                try:
                    await post_pr_review(
                        token, repo_full_name, scan.pr_number,
                        comments=inline_comments,
                        body=f"Spectra found {len(inline_comments)} issue(s) in this PR.",
                    )
                except Exception:
                    logger.exception("inline_review_failed", scan_id=str(scan.id))


async def notify_slack(scan: Scan, eval_result: PolicyEvalResult) -> None:
    settings = get_settings()
    if not settings.slack_webhook_url:
        return

    status = "passed" if eval_result.passed else "FAILED"
    text = (
        f"Spectra scan {status} for commit `{scan.commit_sha[:8]}`: "
        f"{scan.findings_count} findings ({scan.critical_count} critical, {scan.high_count} high)"
    )

    async with httpx.AsyncClient() as client:
        try:
            await client.post(settings.slack_webhook_url, json={"text": text})
        except Exception:
            logger.exception("slack_notification_failed")
