import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport
from src.app import create_app


@pytest.fixture(scope="module")
def test_client():
    app = create_app()
    return TestClient(app)

@pytest.fixture(scope="module")
async def async_client():
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac