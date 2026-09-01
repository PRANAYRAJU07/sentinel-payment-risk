"""
Sentinel Backend — Phase 1 Tests
Tests the core FastAPI application setup.
"""
import pytest
from httpx import AsyncClient, ASGITransport


@pytest.fixture
async def client():
    """Create a test client for the FastAPI app."""
    # Import here to avoid circular imports
    from app.main import app
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac


@pytest.mark.asyncio
async def test_health_check_returns_200(client):
    """Health check endpoint must return 200."""
    response = await client.get("/api/v1/health")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_health_check_structure(client):
    """Health check must return expected JSON structure."""
    response = await client.get("/api/v1/health")
    data = response.json()

    assert "status" in data
    assert "version" in data
    assert "components" in data
    assert "database" in data["components"]
    assert "model" in data["components"]


@pytest.mark.asyncio
async def test_health_check_has_mode_warning(client):
    """Health check must include TEST/DEMO mode warning."""
    response = await client.get("/api/v1/health")
    data = response.json()

    # Must NOT claim to be production
    assert "TEST" in data.get("mode", "").upper() or "DEMO" in data.get("mode", "").upper()


@pytest.mark.asyncio
async def test_openapi_available(client):
    """OpenAPI docs must be accessible."""
    response = await client.get("/openapi.json")
    assert response.status_code == 200
    data = response.json()
    assert data["info"]["title"] == "Sentinel — AI-Powered Payment Risk Control Tower"


@pytest.mark.asyncio
async def test_request_id_header(client):
    """Every response must include a request ID."""
    response = await client.get("/api/v1/health")
    assert "x-request-id" in response.headers


@pytest.mark.asyncio
async def test_process_time_header(client):
    """Every response must include processing time."""
    response = await client.get("/api/v1/health")
    assert "x-process-time-ms" in response.headers


@pytest.mark.asyncio
async def test_404_returns_structured_error(client):
    """Unknown endpoints should return structured error-like response."""
    response = await client.get("/api/v1/nonexistent")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_cors_headers_present(client):
    """CORS headers must be present for frontend requests."""
    response = await client.get(
        "/api/v1/health",
        headers={"Origin": "http://localhost:5173"},
    )
    # CORS headers should be in response
    assert response.status_code == 200
