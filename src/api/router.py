from fastapi import APIRouter

from api.analytics import router as analytics_router
from api.auth import router as auth_router
from api.events import router as events_router
from api.findings import router as findings_router
from api.policies import router as policies_router
from api.repos import router as repos_router
from api.scans import router as scans_router
from api.webhooks import router as webhooks_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth_router)
api_router.include_router(repos_router)
api_router.include_router(scans_router)
api_router.include_router(findings_router)
api_router.include_router(policies_router)
api_router.include_router(events_router)
api_router.include_router(analytics_router)

# Webhooks don't need the /api/v1 prefix
webhook_router = webhooks_router
