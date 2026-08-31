import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.redis import get_redis
from app.db.session import get_db
from app.main import app


@pytest.fixture
def mock_redis():
    redis = AsyncMock()
    redis.store = {}

    async def fake_get(key: str):
        return redis.store.get(key)

    async def fake_set(key: str, value: str):
        redis.store[key] = value
        return True

    redis.get = AsyncMock(side_effect=fake_get)
    redis.set = AsyncMock(side_effect=fake_set)
    return redis


@pytest.fixture
def mock_db():
    db = AsyncMock()
    db.add = MagicMock()

    async def fake_refresh(obj):
        if not hasattr(obj, "id") or obj.id is None:
            obj.id = uuid.uuid4()
        if not hasattr(obj, "timestamp") or obj.timestamp is None:
            obj.timestamp = datetime.now(timezone.utc)
        return obj

    db.refresh = AsyncMock(side_effect=fake_refresh)
    return db


@pytest.fixture
async def async_client(mock_db, mock_redis):
    async def override_get_db():
        yield mock_db

    async def override_get_redis():
        return mock_redis

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_redis] = override_get_redis

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_create_telemetry_and_update_redis_cache(
    async_client, mock_redis, mock_db
):
    """Test POST /api/v1/telemetry saves record to DB and updates Redis cache."""
    payload = {
        "device_id": "pico-test-01",
        "voltage": 225.4,
        "current": 1.85,
    }

    response = await async_client.post("/api/v1/telemetry/", json=payload)

    assert response.status_code == 201
    data = response.json()
    assert data["device_id"] == "pico-test-01"
    assert data["voltage"] == 225.4
    assert data["current"] == 1.85
    assert "id" in data
    assert "timestamp" in data

    # Verify DB operations
    mock_db.add.assert_called_once()
    mock_db.commit.assert_awaited_once()
    mock_db.refresh.assert_awaited_once()

    # Verify Redis cache update
    expected_cache_key = "device:pico-test-01:latest_status"
    mock_redis.set.assert_awaited_once()
    assert expected_cache_key in mock_redis.store
