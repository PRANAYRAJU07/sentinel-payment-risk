import pytest
import asyncio
from httpx import AsyncClient, ASGITransport
import uuid

from app.main import app

@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

@pytest.mark.asyncio
async def test_api_router_exists(client):
    # Just verify the router is registered by checking 422 vs 404
    res = await client.post("/api/v1/behavior/profile", json={})
    assert res.status_code == 422 # Validation error means router is registered
