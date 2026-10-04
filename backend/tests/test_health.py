import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(async_client: AsyncClient):
    response = await async_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data
    assert "app" in data


@pytest.mark.asyncio
async def test_api_v1_root(async_client: AsyncClient):
    response = await async_client.get("/api/v1/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
