import pytest
from types import SimpleNamespace

@pytest.mark.anyio
async def test_liveness(async_client):
    """Test the /liveness endpoint."""
    response = await async_client.get("/liveness")
    assert response.status_code == 200
    assert response.json() == {"message": "ok"}

@pytest.mark.anyio
async def test_readiness(async_client):
    """Test the /readiness endpoint."""
    response = await async_client.get("/readiness")
    assert response.status_code == 200
    assert response.json() == {"message": "ok"}
