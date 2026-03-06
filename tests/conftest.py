import asyncio
import uuid
from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from spectra.config import Settings, get_settings
from spectra.core.security import create_access_token
from spectra.db.base import Base
from spectra.db.models import *  # noqa: F401,F403

TEST_DB_URL = "sqlite+aiosqlite:///test.db"


def get_test_settings() -> Settings:
    return Settings(
        database_url=TEST_DB_URL,
        jwt_secret_key="test-secret",
        github_webhook_secret="test-webhook-secret",
        environment="test",
    )


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_engine():
    engine = create_async_engine(TEST_DB_URL)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    session_factory = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session
        await session.rollback()


@pytest.fixture
async def client(test_engine, db_session) -> AsyncGenerator[AsyncClient, None]:
    from spectra.main import create_app
    from spectra.dependencies import get_db

    app = create_app()

    # Override settings
    app.dependency_overrides[get_settings] = get_test_settings

    async def override_db():
        yield db_session

    app.dependency_overrides[get_db] = override_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.fixture
def auth_headers() -> dict:
    token = create_access_token({"sub": str(uuid.uuid4()), "github_login": "testuser"})
    return {"Authorization": f"Bearer {token}"}
