from fastapi import APIRouter, Header, Request

from core.exceptions import AuthError
from core.logging import get_logger
from core.security import verify_webhook_signature
from services.scan_orchestrator import handle_pr_event, handle_installation_event, handle_push_event

logger = get_logger(__name__)

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("/github")
async def github_webhook(
    request: Request,
    x_hub_signature_256: str = Header(...),
    x_github_event: str = Header(...),
):
    body = await request.body()

    if not verify_webhook_signature(body, x_hub_signature_256):
        raise AuthError("Invalid webhook signature")

    payload = await request.json()
    logger.info("webhook_received", github_event=x_github_event, action=payload.get("action"))

    if x_github_event == "pull_request" and payload.get("action") in ("opened", "synchronize"):
        await handle_pr_event(payload)
    elif x_github_event == "installation" and payload.get("action") == "created":
        await handle_installation_event(payload)
    elif x_github_event == "push":
        await handle_push_event(payload)

    return {"status": "ok"}
