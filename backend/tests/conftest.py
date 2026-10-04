# pyrefly: ignore [missing-import]
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.database import engine


@pytest_asyncio.fixture(autouse=True)
async def cleanup_database_connections():
    """Ensure connections in pool are disposed between test functions so event loops don't conflict."""
    yield
    await engine.dispose()


@pytest_asyncio.fixture
async def async_client():
    """Async HTTP client fixture for testing endpoints."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
