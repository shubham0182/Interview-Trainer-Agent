"""ST-01 scaffold smoke test — verifies the app factory imports and health check works."""
import pytest


@pytest.mark.asyncio
async def test_health_check(async_client):
    response = await async_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "InterviewPro" in data["service"]
