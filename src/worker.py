from arq.connections import RedisSettings

from config import get_settings
from tasks.auto_fix_task import run_auto_fix
from tasks.scan_task import run_scan


async def startup(ctx: dict) -> None:
    from core.logging import setup_logging
    setup_logging()


async def shutdown(ctx: dict) -> None:
    pass


class WorkerSettings:
    functions = [run_scan, run_auto_fix]
    on_startup = startup
    on_shutdown = shutdown
    max_jobs = 4
    job_timeout = 600  # 10 minutes

    redis_settings = RedisSettings.from_dsn(get_settings().redis_url)
