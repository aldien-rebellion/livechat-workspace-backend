import uuid

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.services.presence_service import presence_service


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


async def create_user_with_token(client: AsyncClient, prefix: str):
    suffix = uuid.uuid4().hex[:6]
    username = f"{prefix}_{suffix}"
    email = f"{username}@test.com"
    password = "Password123!"

    reg = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "username": username, "password": password},
    )
    user_id = reg.json()["id"]

    login = await client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": password},
    )
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    return user_id, headers


@pytest.mark.asyncio
async def test_presence_service_lifecycle():
    user_id = uuid.uuid4()
    ws_id = uuid.uuid4()

    # 1. Mark online
    was_offline = await presence_service.mark_online(user_id, ws_id)
    assert was_offline is True
    assert await presence_service.is_user_online(user_id) is True

    # 2. Get online users in workspace
    online_users = await presence_service.get_online_users(ws_id)
    assert str(user_id) in online_users

    # 3. Heartbeat
    await presence_service.heartbeat(user_id, ws_id)
    assert await presence_service.is_user_online(user_id) is True

    # 4. Mark offline
    await presence_service.mark_offline(user_id, ws_id)
    assert await presence_service.is_user_online(user_id) is False
    online_users_after = await presence_service.get_online_users(ws_id)
    assert str(user_id) not in online_users_after


@pytest.mark.asyncio
async def test_read_receipts_rest_flow(client: AsyncClient):
    user_a_id, headers_a = await create_user_with_token(client, "reader_a")
    user_b_id, headers_b = await create_user_with_token(client, "reader_b")

    # User A creates workspace
    ws_res = await client.post(
        "/api/v1/workspaces",
        json={"name": "Receipt Test Space"},
        headers=headers_a,
    )
    assert ws_res.status_code == 201
    ws_id = ws_res.json()["id"]

    # User B joins workspace
    join_res = await client.post(
        f"/api/v1/workspaces/{ws_id}/members",
        json={"user_id": user_b_id, "role": "member"},
        headers=headers_b,
    )
    assert join_res.status_code == 201

    # Get #general channel
    chans = await client.get(f"/api/v1/workspaces/{ws_id}/channels", headers=headers_a)
    general_id = chans.json()[0]["id"]

    # User A sends a message
    msg_res = await client.post(
        f"/api/v1/channels/{general_id}/messages",
        json={"content": "Please read this important message!"},
        headers=headers_a,
    )
    assert msg_res.status_code == 201
    msg_id = msg_res.json()["id"]

    # Check readers before User B reads (should be empty)
    readers_before = await client.get(
        f"/api/v1/messages/{msg_id}/readers",
        headers=headers_a,
    )
    assert readers_before.status_code == 200
    assert len(readers_before.json()) == 0

    # User B marks message as read
    read_res = await client.post(
        f"/api/v1/messages/{msg_id}/read",
        headers=headers_b,
    )
    assert read_res.status_code == 200
    assert read_res.json()["marked_count"] == 1

    # Check readers after User B reads
    readers_after = await client.get(
        f"/api/v1/messages/{msg_id}/readers",
        headers=headers_a,
    )
    assert readers_after.status_code == 200
    readers = readers_after.json()
    assert len(readers) == 1
    assert readers[0]["user_id"] == str(user_b_id)


@pytest.mark.asyncio
async def test_workspace_online_users_endpoint(client: AsyncClient):
    user_id, headers = await create_user_with_token(client, "presence_user")

    # Create workspace
    ws_res = await client.post(
        "/api/v1/workspaces",
        json={"name": "Presence Online Space"},
        headers=headers,
    )
    assert ws_res.status_code == 201
    ws_id = ws_res.json()["id"]

    # Mark user online in workspace
    await presence_service.mark_online(uuid.UUID(user_id), uuid.UUID(ws_id))

    # Query online users endpoint
    online_res = await client.get(
        f"/api/v1/workspaces/{ws_id}/online-users",
        headers=headers,
    )
    assert online_res.status_code == 200
    data = online_res.json()
    assert data["online_count"] >= 1
    assert str(user_id) in data["online_users"]

    # Cleanup
    await presence_service.mark_offline(uuid.UUID(user_id), uuid.UUID(ws_id))
