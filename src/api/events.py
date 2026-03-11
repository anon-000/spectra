"""SSE endpoints for real-time scan updates."""

import asyncio
import json
from collections.abc import AsyncGenerator

import redis.asyncio as aioredis
from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import select

from config import get_settings
from core.logging import get_logger
from core.security import decode_access_token
from db.engine import async_session
from db.models.user import User

logger = get_logger(__name__)
router = APIRouter(prefix="/events", tags=["events"])

HEARTBEAT_INTERVAL = 15  # seconds


async def _authenticate(token: str) -> User | None:
    """Authenticate via JWT query param (EventSource can't set headers)."""
    try:
        payload = decode_access_token(token)
        user_id = payload.get("sub")
        if not user_id:
            return None
        async with async_session() as db:
            result = await db.execute(select(User).where(User.id == user_id))
            return result.scalar_one_or_none()
    except Exception:
        return None


async def _sse_stream(channel: str) -> AsyncGenerator[str, None]:
    """Subscribe to a Redis channel and yield SSE-formatted events."""
    settings = get_settings()
    r = aioredis.from_url(settings.redis_url, decode_responses=True)
    pubsub = r.pubsub()
    await pubsub.subscribe(channel)

    try:
        while True:
            message = await asyncio.wait_for(
                pubsub.get_message(ignore_subscribe_messages=True, timeout=HEARTBEAT_INTERVAL),
                timeout=HEARTBEAT_INTERVAL + 1,
            )
            if message and message["type"] == "message":
                data = message["data"]
                yield f"data: {data}\n\n"
                # If it's a terminal event, close the stream
                try:
                    parsed = json.loads(data)
                    if parsed.get("stage") in ("completed", "failed"):
                        yield f"data: {json.dumps({'type': 'close'})}\n\n"
                        break
                except (json.JSONDecodeError, KeyError):
                    pass
            else:
                # Send heartbeat
                yield ": heartbeat\n\n"
    except asyncio.CancelledError:
        pass
    finally:
        await pubsub.unsubscribe(channel)
        await pubsub.close()
        await r.close()


@router.get("/scans/{scan_id}/stream")
async def scan_stream(scan_id: str, token: str = Query(...)):
    """SSE stream for per-scan progress updates."""
    user = await _authenticate(token)
    if not user:
        return StreamingResponse(
            iter([f"data: {json.dumps({'error': 'unauthorized'})}\n\n"]),
            status_code=401,
            media_type="text/event-stream",
        )

    channel = f"spectra:scan:{scan_id}:progress"
    return StreamingResponse(
        _sse_stream(channel),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/stream")
async def dashboard_stream(token: str = Query(...)):
    """SSE stream for org-level dashboard events."""
    user = await _authenticate(token)
    if not user or not user.org_id:
        return StreamingResponse(
            iter([f"data: {json.dumps({'error': 'unauthorized'})}\n\n"]),
            status_code=401,
            media_type="text/event-stream",
        )

    channel = f"spectra:org:{user.org_id}:events"
    return StreamingResponse(
        _sse_stream(channel),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
