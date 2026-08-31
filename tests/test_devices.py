import json
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.redis import get_redis
from app.db.session import get_db
from app.main import app
from app.models.telemetry import Telemetry


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
async def test_get_device_status_cache_hit(async_client, mock_redis, mock_db):
    """Test when status exists in Redis (Cache Hit),
    returns immediately without DB query.
    """

    device_id = "pico-001"
    cached_payload = {
        "id": str(uuid.uuid4()),
        "device_id": device_id,
        "voltage": 220.5,
        "current": 1.5,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    mock_redis.store[f"device:{device_id}:latest_status"] = json.dumps(cached_payload)

    response = await async_client.get(f"/api/v1/devices/{device_id}/status")

    assert response.status_code == 200
    data = response.json()
    assert data["device_id"] == device_id
    assert data["voltage"] == 220.5
    assert data["current"] == 1.5
    mock_redis.get.assert_awaited_once_with(f"device:{device_id}:latest_status")
    # DB should not be queried on cache hit
    mock_db.execute.assert_not_called()


@pytest.mark.asyncio
async def test_get_device_status_cache_miss_found_in_db(
    async_client, mock_redis, mock_db
):
    """Test Cache Miss: queries DB, saves to Redis, and returns response."""
    device_id = "pico-002"
    record_id = uuid.uuid4()
    now = datetime.now(timezone.utc)

    db_telemetry = Telemetry(
        id=record_id,
        device_id=device_id,
        voltage=230.1,
        current=2.0,
        timestamp=now,
    )

    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = db_telemetry
    mock_db.execute.return_value = mock_result

    response = await async_client.get(f"/api/v1/devices/{device_id}/status")

    assert response.status_code == 200
    data = response.json()
    assert data["device_id"] == device_id
    assert data["voltage"] == 230.1
    assert data["current"] == 2.0

    # Verify Redis get was called
    mock_redis.get.assert_awaited_once_with(f"device:{device_id}:latest_status")
    # Verify DB was queried
    mock_db.execute.assert_awaited_once()
    # Verify Redis set was called to cache the result
    mock_redis.set.assert_awaited_once()
    assert f"device:{device_id}:latest_status" in mock_redis.store


@pytest.mark.asyncio
async def test_get_device_status_not_found(async_client, mock_redis, mock_db):
    """Test 404 when device is neither in Redis cache nor in PostgreSQL DB."""
    device_id = "non-existent-device"

    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = None
    mock_db.execute.return_value = mock_result

    response = await async_client.get(f"/api/v1/devices/{device_id}/status")

    assert response.status_code == 404
    assert "Device status not found" in response.json()["detail"]
    mock_redis.set.assert_not_called()
