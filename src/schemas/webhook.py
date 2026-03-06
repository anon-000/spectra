from pydantic import BaseModel


class WebhookPayload(BaseModel):
    action: str
    installation: dict | None = None
    repository: dict | None = None
    pull_request: dict | None = None
    sender: dict | None = None
