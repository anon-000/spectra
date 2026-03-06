import io
import json
from functools import lru_cache

from minio import Minio

from config import get_settings
from core.logging import get_logger

logger = get_logger(__name__)


@lru_cache
def get_minio_client() -> Minio:
    settings = get_settings()
    return Minio(
        settings.minio_endpoint,
        access_key=settings.minio_access_key,
        secret_key=settings.minio_secret_key,
        secure=settings.minio_secure,
    )


def ensure_bucket() -> None:
    settings = get_settings()
    client = get_minio_client()
    if not client.bucket_exists(settings.minio_bucket):
        client.make_bucket(settings.minio_bucket)


def upload_scan_results(scan_id: str, tool_name: str, results: list[dict]) -> str:
    """Upload raw tool output to MinIO. Returns the object key."""
    settings = get_settings()
    client = get_minio_client()
    key = f"scans/{scan_id}/{tool_name}.json"
    data = json.dumps(results, default=str).encode()
    client.put_object(
        settings.minio_bucket, key, io.BytesIO(data), len(data),
        content_type="application/json",
    )
    logger.info("uploaded_results", key=key)
    return key


def download_scan_results(scan_id: str, tool_name: str) -> list[dict]:
    settings = get_settings()
    client = get_minio_client()
    key = f"scans/{scan_id}/{tool_name}.json"
    response = client.get_object(settings.minio_bucket, key)
    return json.loads(response.read())
