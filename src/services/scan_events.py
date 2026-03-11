"""Redis pub/sub helper for real-time scan progress events."""

import json
from datetime import UTC, datetime

import redis.asyncio as aioredis

from config import get_settings
from core.logging import get_logger

logger = get_logger(__name__)

SCAN_STAGES = [
    "cloning",
    "sast_running",
    "sca_running",
    "secrets_running",
    "license_running",
    "normalizing",
    "ai_triage",
    "policy_eval",
    "completed",
    "failed",
]


def _get_redis() -> aioredis.Redis:
    settings = get_settings()
    return aioredis.from_url(settings.redis_url, decode_responses=True)


async def publish_scan_progress(
    scan_id: str,
    org_id: str,
    stage: str,
    status: str,
    message: str,
    progress_pct: int = 0,
    **extra,
) -> None:
    """Publish scan progress to Redis channels for SSE consumers."""
    event = {
        "scan_id": scan_id,
        "org_id": org_id,
        "stage": stage,
        "status": status,
        "message": message,
        "progress_pct": progress_pct,
        "timestamp": datetime.now(UTC).isoformat(),
        **extra,
    }
    payload = json.dumps(event)

    try:
        r = _get_redis()
        async with r:
            # Per-scan channel (for scan detail page)
            await r.publish(f"spectra:scan:{scan_id}:progress", payload)
            # Org-level channel (for dashboard)
            await r.publish(f"spectra:org:{org_id}:events", payload)
    except Exception:
        logger.exception("publish_scan_progress_failed", scan_id=scan_id)
