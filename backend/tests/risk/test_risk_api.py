"""
Sentinel Risk Engine — API Tests
"""
import pytest
from httpx import AsyncClient, ASGITransport
import uuid
from backend.app.main import app

@pytest.fixture
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac

@pytest.mark.asyncio
async def test_risk_score_endpoint(client):
    tx_id = str(uuid.uuid4())
    payload = {
        "id": tx_id,
        "amount": 100.0,
        "currency": "INR",
        "time": 1000.0
    }
    
    response = await client.post("/api/v1/risk/score", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["transaction_id"] == tx_id
    assert "final_risk_score" in data
    assert data["decision"] in ["APPROVE", "REVIEW", "HOLD"]
